import hashlib
import json
import os
import pathlib
import subprocess

version = os.environ['PYTHON_VERSION']
lock = json.loads(pathlib.Path('/recipe/sources.json').read_text())[version]
root = pathlib.Path('/out')
smoke = json.loads((root / 'smoke.json').read_text())
manifest = {
    'schemaVersion': 1,
    'version': version,
    'runtime': 'cpython',
    'target': 'wasm32-emscripten',
    'adapter': 'emscripten',
    'invocation': 'callMain',
    'source': {'url': lock['url'], 'sha256': lock['sha256']},
    'emscripten': subprocess.check_output(['emcc', '--version'], universal_newlines=True).splitlines()[0],
    'features': {
        'filesystem': 'MEMFS', 'threads': False, 'dynamicLinking': False,
        'pip': False, 'micropip': False, 'modules': smoke['modules'],
    },
    'validation': {'node': smoke, 'browser': 'pending'},
    'files': {p.name: {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
              for p in sorted(root.iterdir()) if p.is_file()},
}
(root / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
