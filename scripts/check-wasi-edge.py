#!/usr/bin/env python3
"""Build and verify the pinned native WASI HTTP lab; see docs/reference/wasi-edge-lab.md."""
import argparse
import hashlib
import io
import json
import platform
import queue
import re
import signal
import subprocess
import sys
import tarfile
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / 'docs/examples/wasi-edge'


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download', action='store_true', help='Download missing pinned tool and WIT archives; existing downloads are always verified.')
    parser.add_argument('--work-dir', type=Path, default=EXAMPLE / '.build', help='Directory for generated files and native tools.')
    parser.add_argument('--output', type=Path, default=ROOT / 'test-results/wasi-edge.json', help='Evidence output; the default is ignored.')
    parser.add_argument('--summary-output', type=Path, help='Also write a curated evidence record, for example docs/evidence/wasi-edge-2026-09-29.json.')
    args = parser.parse_args()
    if not __debug__:
        parser.error('Verification requires assertions; remove -O, -OO and PYTHONOPTIMIZE.')
    if sys.version_info < (3, 12):
        parser.error('This checker requires native Python 3.12 or newer.')
    if (platform.system(), platform.machine()) != ('Darwin', 'arm64'):
        parser.error('The pinned native tool downloads cover macOS arm64 only; the component itself targets WASI.')
    work = args.work_dir.resolve()
    work.mkdir(parents=True, exist_ok=True)
    lock_path = EXAMPLE / 'toolchain.lock.json'
    lock = json.loads(lock_path.read_text())
    evidence = {'schemaVersion': 1, 'checkedAt': datetime.now(timezone.utc).isoformat(), 'host': platform.platform(), 'nativePython': sys.version, 'tools': {key: lock[key] for key in ('componentizePy', 'wasmtime', 'wasmTools')}, 'requestedWorld': lock['requestedWorld'], 'witSourceCommit': lock['witSourceCommit'], 'assets': [], 'commands': [], 'cases': [], 'sources': {str(p.relative_to(ROOT)): sha256(p.read_bytes()) for p in (EXAMPLE / 'app.py', lock_path, Path(__file__).resolve())}, 'scope': 'A Python WASI HTTP component on native Wasmtime, without application containers. The capability probe tests directory access only; it is not an audit of every imported host interface.'}

    def run(command, cwd=EXAMPLE):
        command = [str(part) for part in command]
        started = time.monotonic()
        result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=180)
        evidence['commands'].append({'argv': command, 'cwd': str(cwd), 'exitCode': result.returncode, 'elapsedSeconds': round(time.monotonic() - started, 3), 'stdout': result.stdout.strip(), 'stderr': result.stderr.strip()})
        if result.returncode:
            raise RuntimeError('Command failed: ' + ' '.join(command) + '\n' + result.stderr)
        return result.stdout

    def serve(label, preopen):
        command = [str(wasmtime), 'serve', '-Scli', '--addr', '127.0.0.1:0', '--max-instance-reuse-count', '1']
        if preopen:
            command.extend(['--dir', str(fixture) + '::/data'])
        command.append(str(component))
        process = subprocess.Popen(command, cwd=work, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        lines = queue.Queue()
        log = []

        def read_output():
            for line in process.stdout:
                log.append(line.rstrip())
                lines.put(line)
            lines.put(None)

        reader = threading.Thread(target=read_output, daemon=True)
        reader.start()
        record = {'name': label, 'argv': command, 'directoryPreopen': str(fixture) + '::/data' if preopen else None, 'requests': []}
        evidence['cases'].append(record)
        try:
            deadline = time.monotonic() + 60
            while True:
                line = lines.get(timeout=max(0.1, deadline - time.monotonic()))
                if line is None:
                    raise RuntimeError('Wasmtime exited before listening: ' + '\n'.join(log))
                match = re.search(r'Serving HTTP on (http://127\.0\.0\.1:\d+)', line)
                if match:
                    origin = match.group(1)
                    break
                if time.monotonic() >= deadline:
                    raise TimeoutError('Wasmtime startup exceeded 60 seconds')

            local_http = urllib.request.build_opener(urllib.request.ProxyHandler({}))

            def request(method, path, body=None):
                data = None if body is None else body.encode()
                req = urllib.request.Request(origin + path, data=data, method=method, headers={'Content-Type': 'application/json'})
                try:
                    response = local_http.open(req, timeout=15)
                except urllib.error.HTTPError as error:
                    response = error
                with response:
                    payload = json.loads(response.read())
                    item = {'method': method, 'path': path, 'status': response.status, 'json': payload}
                record['requests'].append(item)
                return item

            first = request('GET', '/info')
            second = request('GET', '/info')
            assert first['status'] == second['status'] == 200
            assert first['json'] == second['json'] == {'platform': 'wasi', 'python': '3.14.0', 'requests_in_instance': 1}
            if not preopen:
                quote = request('POST', '/quote', '{"sku":"widget","quantity":2}')
                assert quote['status'] == 200
                assert quote['json'] == {'sku': 'widget', 'quantity': 2, 'total_cents': 250}
                assert request('POST', '/quote', '{"sku":"widget","quantity":0}')['status'] == 422
                assert request('POST', '/quote', '{')['status'] == 400
                assert request('POST', '/quote', 'x' * 4097)['status'] == 413
                assert request('GET', '/missing')['status'] == 404
            data = request('GET', '/data')
            if preopen:
                assert data == {'method': 'GET', 'path': '/data', 'status': 200, 'json': {'message': 'explicit directory capability'}}
            else:
                assert data['status'] == 403 and data['json']['exception'] == 'FileNotFoundError' and data['json']['errno'] == 44
        finally:
            process.send_signal(signal.SIGINT) if process.poll() is None else None
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            reader.join(timeout=2)
            record['hostLog'] = log
            record['hostExitCode'] = process.returncode
        assert record['hostExitCode'] == 0, 'Wasmtime did not shut down successfully.'
        record['passed'] = True

    try:
        for asset in lock['assets']:
            destination = work / asset['filename']
            if not destination.exists():
                if not args.download:
                    raise FileNotFoundError(str(destination) + ' is missing; rerun with --download.')
                with urllib.request.urlopen(asset['url'], timeout=120) as response:
                    data = response.read()
                if sha256(data) != asset['sha256']:
                    raise ValueError('Downloaded hash mismatch: ' + asset['filename'])
                destination.write_bytes(data)
            assert sha256(destination.read_bytes()) == asset['sha256'], asset['filename']
            evidence['assets'].append(asset)
            if destination.name.endswith(('.tar.xz', '.tar.gz')):
                with tarfile.open(destination) as archive:
                    for member in archive.getmembers():
                        if member.isfile():
                            target = work / member.name
                            if target.exists():
                                assert sha256(target.read_bytes()) == sha256(archive.extractfile(member).read()), 'Extracted source/tool changed: ' + str(target)
                            else:
                                archive.extract(member, work, filter='data')
        venv = work / 'venv'
        if not (venv / 'bin/python').exists():
            run([sys.executable, '-m', 'venv', venv])
        wheel = next(work / item['filename'] for item in lock['assets'] if item['filename'].endswith('.whl'))
        run([venv / 'bin/python', '-m', 'pip', '--disable-pip-version-check', 'install', '--no-index', '--no-deps', '--force-reinstall', wheel])
        componentize = venv / 'bin/componentize-py'
        wasmtime = work / ('wasmtime-v' + lock['wasmtime'] + '-aarch64-macos/wasmtime')
        wasm_tools = work / ('wasm-tools-' + lock['wasmTools'] + '-aarch64-macos/wasm-tools')
        evidence['reportedToolVersions'] = [run([tool, '--version']).strip() for tool in (componentize, wasmtime, wasm_tools)]
        wit = work / ('componentize-py-' + lock['witSourceCommit']) / 'wit'
        component = work / 'app.wasm'
        run([componentize, '-d', wit, '-w', lock['requestedWorld'], 'componentize', 'app', '-o', component])
        run([wasm_tools, 'validate', component])
        artifact_wit = run([wasm_tools, 'component', 'wit', component])
        (work / 'app.wit').write_text(artifact_wit)
        component_bytes = component.read_bytes()
        assert component_bytes[:8].hex() == '0061736d0d000100', 'Expected component encoding, not a core Wasm module.'
        evidence['artifact'] = {'filename': 'app.wasm', 'bytes': len(component_bytes), 'sha256': sha256(component_bytes), 'encodingHeader': component_bytes[:8].hex(), 'imports': re.findall(r'^  import (\S+);$', artifact_wit, re.MULTILINE), 'exports': ['exports'] + re.findall(r'^  export (\S+);$', artifact_wit, re.MULTILINE), 'witSHA256': sha256(artifact_wit.encode()), 'embeddedPython': '3.14.0', 'pythonVersionVerifiedBy': 'GET /info on the native WASI host'}
        assert 'wasi:http/incoming-handler@0.2.0' in evidence['artifact']['exports']
        fixture = work / 'fixture'
        fixture.mkdir(exist_ok=True)
        (fixture / 'message.txt').write_text('explicit directory capability\n')
        evidence['fixture'] = {'path': str(fixture / 'message.txt'), 'sha256': sha256((fixture / 'message.txt').read_bytes()), 'createdBeforeHostLaunch': True, 'excludedFromPackage': True}
        serve('directory-not-granted', False)
        serve('directory-granted', True)
        manifest = {key: evidence[key] for key in ('tools', 'requestedWorld', 'witSourceCommit', 'sources', 'artifact')}
        manifest['runtimeRequirement'] = 'A WASI HTTP host implementing the recorded imports; tested with native Wasmtime 49.0.1. This package does not contain a native host, operating-system image or fixture data.'
        manifest_bytes = (json.dumps(manifest, indent=2) + '\n').encode()
        (work / 'manifest.json').write_bytes(manifest_bytes)
        package = work / 'wasi-edge-app.tar'
        with tarfile.open(package, 'w') as archive:
            for name, contents in [('app.wasm', component_bytes), ('manifest.json', manifest_bytes)]:
                info = tarfile.TarInfo(name)
                info.size = len(contents)
                info.mode = 0o644
                archive.addfile(info, io.BytesIO(contents))
        evidence['package'] = {'filename': package.name, 'bytes': package.stat().st_size, 'sha256': sha256(package.read_bytes()), 'members': ['app.wasm', 'manifest.json']}
        for name, expected in evidence['sources'].items():
            assert sha256((ROOT / name).read_bytes()) == expected, 'Handwritten source changed during run.'
        evidence['passed'] = True
    except Exception as error:
        evidence['passed'] = False
        evidence['failure'] = {'type': type(error).__name__, 'message': str(error)}
        raise
    finally:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(evidence, indent=2) + '\n')
        if args.summary_output:
            summary = {key: value for key, value in evidence.items() if key != 'commands'}
            summary['commands'] = [{key: value for key, value in item.items() if key not in ('stdout', 'stderr')} for item in evidence['commands']]
            args.summary_output.parent.mkdir(parents=True, exist_ok=True)
            args.summary_output.write_text(json.dumps(summary, indent=2) + '\n')
        print(json.dumps({'passed': evidence['passed'], 'output': str(args.output), 'summaryOutput': str(args.summary_output) if args.summary_output else None, 'component': str(work / 'app.wasm'), 'package': str(work / 'wasi-edge-app.tar')}, indent=2))


if __name__ == '__main__':
    main()
