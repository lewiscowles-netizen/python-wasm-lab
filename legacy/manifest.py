import hashlib
import json
import pathlib
import subprocess

root = pathlib.Path('/out')
smoke = json.loads((root / 'smoke.json').read_text())
manifest = {
    'schemaVersion': 1,
    'version': '2.7.18',
    'runtime': 'cpython',
    'target': 'wasm32-emscripten',
    'adapter': 'emscripten',
    'invocation': 'callMain',
    'source': {
        'url': 'https://www.python.org/ftp/python/2.7.18/Python-2.7.18.tar.xz',
        'sha256': 'b62c0e7937551d0cc02b8fd5cb0f544f9405bafc9a54d3808ed4594812edef43',
    },
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
