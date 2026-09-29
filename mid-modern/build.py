"""Run the CPython 3.11--3.13 source-build branch with pinned source archives."""
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parent
versions = json.loads((root / 'versions.json').read_text())['versions']
series = sys.argv[1:]
if not series or any(value not in {'3.11', '3.12', '3.13'} for value in series):
    raise SystemExit('Pass one or more of: 3.11 3.12 3.13')
for value in series:
    entry = next(item for item in versions if item['series'] == value)
    args = ['docker', 'buildx', 'build', '--progress=plain',
            '--target', 'artifacts', '--build-arg', 'JOBS=2',
            '--output', f'type=local,dest={root / "builds" / entry["version"]}']
    for key, val in {'PYTHON_VERSION': entry['version'], 'PYTHON_SERIES': value,
                     'PYTHON_URL': entry['url'], 'PYTHON_SHA256': entry['sha256']}.items():
        args += ['--build-arg', f'{key}={val}']
    args.append(str(root))
    with (root / 'logs' / f'{entry["version"]}.log').open('w') as log:
        print('Building', entry['version'], flush=True)
        result = subprocess.run(args, stdout=log, stderr=subprocess.STDOUT)
    print(entry['version'], 'exit', result.returncode, flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)
