import concurrent.futures
from pathlib import Path
import subprocess
import sys

def build(version):
    log = Path('build-' + version + '-matrix.log')
    with log.open('w') as stream:
        result = subprocess.run(['docker', 'buildx', 'build', '--build-arg', 'PYTHON_VERSION=' + version,
            '--target', 'artifacts', '--output', 'type=local,dest=dist/' + version, '--progress', 'plain', '.'],
            stdout=stream, stderr=subprocess.STDOUT)
    print(version, 'PASS' if result.returncode == 0 else 'FAIL', str(log), flush=True)
    return result.returncode

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(build, sys.argv[1:] or ['3.5.10', '3.6.15', '3.8.20', '3.9.25', '3.4.10', '3.7.17', '3.10.21']))
raise SystemExit(any(results))
