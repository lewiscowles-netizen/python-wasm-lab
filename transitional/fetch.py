import hashlib
import json
import os
import subprocess
from pathlib import Path

version = os.environ['PYTHON_VERSION']
lock = json.loads(Path('/recipe/sources.json').read_text())[version]
subprocess.run(['curl', '-fsSL', lock['url'], '-o', '/build/source.tar'], check=True)
assert hashlib.sha256(Path('/build/source.tar').read_bytes()).hexdigest() == lock['sha256']
subprocess.run(['tar', '-xf', '/build/source.tar'], check=True, cwd='/build')
Path('/build/Python-' + version).rename('/build/source')
