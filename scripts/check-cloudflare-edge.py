#!/usr/bin/env python3
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import signal
import socket
import subprocess
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "docs/examples/cloudflare-edge"
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def request(base, path="/", body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, headers={"Content-Type": "application/json"})
    try:
        response = OPENER.open(req, timeout=10)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return {"path": path, "method": req.get_method(), "status": response.status, "body": json.loads(response.read())}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def stop(process):
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)


def version(command):
    return subprocess.check_output(command, cwd=EXAMPLE, text=True, timeout=30).strip()


def cycle(port, inspector_port, label, env, report):
    base = f"http://127.0.0.1:{port}"
    log_path = EXAMPLE / ".local" / f"{label}.log"
    command = ["uv", "run", "--frozen", "pywrangler", "dev", "--local", "--ip", "127.0.0.1", "--port", str(port), "--inspector-port", str(inspector_port)]
    result = {"command": command, "requests": []}
    report["runs"].append(result)
    with log_path.open("w") as log:
        process = subprocess.Popen(command, cwd=EXAMPLE, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        started = time.monotonic()
        try:
            while time.monotonic() - started < 180:
                if process.poll() is not None:
                    raise RuntimeError(f"Worker exited during startup; see {log_path}")
                try:
                    first = request(base)
                    if first["status"] == 200:
                        break
                except (OSError, ValueError):
                    pass
                time.sleep(0.25)
            else:
                raise TimeoutError(f"Worker startup timed out; see {log_path}")
            result["startup_seconds_local_observation"] = round(time.monotonic() - started, 3)
            result["requests"].append(first)
            require(first["body"]["python"] == "3.14.2", "Unexpected Python version; revalidate runtime pins")
            require(first["body"]["pyodide"] == "314.0.6", "Unexpected injected Pyodide version; revalidate runtime pins")
            require(first["body"]["platform"] == "emscripten", "Expected the Emscripten runtime")
            require(first["body"]["binding"] == "local workerd binding", "Binding was not delivered")
            if label == "first":
                packages = request(base, "/packages")
                result["requests"].append(packages)
                require(packages["status"] == 200, "Package endpoint failed")
                require(packages["body"]["versions"] == {"snowballstemmer": "3.1.1", "certifi": "2026.7.22"}, "Package pins changed")
                require(packages["body"]["stems"] == ["run", "jump"], "Stemmer output differs")
                require(packages["body"]["resource"]["bytes"] == 240216, "Bundled data resource differs")
                require(packages["body"]["resource"]["certificate_count"] == 121, "Certificate resource contents differ")
                posted = request(base, "/stem", {"words": ["running", "jumping"]})
                result["requests"].append(posted)
                require(posted["status"] == 200 and posted["body"]["stems"] == ["run", "jump"], "POST handler failed")
                invalid = request(base, "/stem", {"words": 42})
                result["requests"].append(invalid)
                require(invalid["status"] == 400, "Invalid POST was not rejected")
                missing = request(base, "/missing")
                result["requests"].append(missing)
                require(missing["status"] == 404, "Missing route did not return 404")
                resources = request(base, "/resources")
                result["requests"].append(resources)
                require(resources["status"] == 200, "Resource endpoint failed")
                require(resources["body"]["thread"] == {"type": "RuntimeError", "message": "can't start new thread"}, "Thread behavior changed")
                require(resources["body"]["file"].get("roundtrip") == "temporary Wasm file", "Temporary file roundtrip failed")
                require(resources["body"]["file"]["existed_before"] is False, "Temporary file existed before the first probe")
                reused = request(base, "/resources")
                result["requests"].append(reused)
                require(reused["body"]["file"]["existed_before"] is True, "Temporary file did not survive a warm request")
            else:
                resources = request(base, "/resources")
                result["requests"].append(resources)
                require(resources["body"]["file"]["existed_before"] is False, "Temporary file survived process restart")
            last = request(base)
            result["requests"].append(last)
            require(last["body"]["request_count"] > first["body"]["request_count"], "Warm request count did not increase")
        finally:
            stop(process)
            result["log"] = log_path.read_text()
    return result


def main():
    parser = argparse.ArgumentParser(description="Start, check, restart and stop a local Cloudflare Python Worker; build a dry-run bundle without deploying.")
    parser.add_argument("--port", type=int, default=8791)
    parser.add_argument("--inspector-port", type=int, default=9236)
    parser.add_argument("--output", type=Path, default=EXAMPLE / ".local/check-result.json")
    args = parser.parse_args()
    for port in [args.port, args.inspector_port]:
        with socket.socket() as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            probe.bind(("127.0.0.1", port))
    (EXAMPLE / ".local").mkdir(exist_ok=True)
    env = dict(os.environ, WRANGLER_SEND_METRICS="false", CI="1")
    report = {"date": datetime.date.today().isoformat(), "scope": "Local workerd HTTP checks and dry-run packaging; no cloud deployment or quota enforcement tested", "host": {"system": platform.system(), "machine": platform.machine()}, "versions": {}, "runs": []}
    try:
        for name, command in {"uv": ["uv", "--version"], "node": ["node", "--version"], "pywrangler": ["uv", "run", "--frozen", "pywrangler", "--version"], "workerd": [str(EXAMPLE / "node_modules/.bin/workerd"), "--version"]}.items():
            report["versions"][name] = version(command)
        report["versions"]["wrangler"] = json.loads((EXAMPLE / "node_modules/wrangler/package.json").read_text())["version"]
        print("Checking first local Worker instance...", flush=True)
        first = cycle(args.port, args.inspector_port, "first", env, report)
        print("Checking a fresh instance after process restart...", flush=True)
        second = cycle(args.port, args.inspector_port, "restart", env, report)
        require(second["requests"][0]["body"]["request_count"] == first["requests"][0]["body"]["request_count"], "Counter did not reset after restart")
        command = ["uv", "run", "--frozen", "pywrangler", "deploy", "--dry-run", "--outdir", ".local/bundle"]
        print("Creating local dry-run deployment bundle...", flush=True)
        bundle = subprocess.run(command, cwd=EXAMPLE, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
        report["bundle"] = {"command": command, "exit_code": bundle.returncode, "log": bundle.stdout}
        require(bundle.returncode == 0, "Dry-run packaging failed")
        size_line = re.search(r"Total Upload:.*", bundle.stdout)
        report["bundle"]["reported_upload"] = size_line.group(0) if size_line else None
        paths = sorted(path for path in (EXAMPLE / ".local/bundle").rglob("*") if path.is_file())
        report["bundle"]["files"] = [{"path": str(path.relative_to(EXAMPLE / ".local/bundle")), "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in paths]
        report["source_sha256"] = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in [EXAMPLE / "src/entry.py", EXAMPLE / "wrangler.toml", EXAMPLE / "pyproject.toml", EXAMPLE / "pylock.toml", EXAMPLE / "uv.lock", EXAMPLE / "package.json", EXAMPLE / "yarn.lock", Path(__file__)]}
        report["passed"] = True
    except Exception as error:
        report["passed"] = False
        report["error"] = {"type": type(error).__name__, "message": str(error)}
        raise
    finally:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")
        print(f"Evidence: {args.output}", flush=True)


if __name__ == "__main__":
    main()
