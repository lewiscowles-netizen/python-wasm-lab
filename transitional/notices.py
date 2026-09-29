"""Preserve notices shipped with the interpreter sources and SDK runtime."""
from pathlib import Path
import sys

source, output = map(Path, sys.argv[1:])
sdk = Path('/emsdk/upstream/emscripten')
files = {sdk / 'LICENSE', sdk / 'AUTHORS'}
for root in (source / 'Modules', sdk / 'system/lib', sdk / 'cache/ports'):
    if root.exists():
        for path in root.rglob('*'):
            if path.is_file() and path.name.lower().split('.')[0] in {
                'license', 'licence', 'copying', 'copyright', 'notice'}:
                files.add(path)
parts = ['Notices accompanying CPython source components and Emscripten runtime libraries.\n'
         'Some notices cover optional components not linked into this profile.\n']
for path in sorted(files):
    if path.is_file():
        parts.append('\n' + '=' * 72 + '\n' + str(path) + '\n' + '=' * 72 + '\n'
                     + path.read_text(errors='replace'))
output.write_text('\n'.join(parts) + '\n')
