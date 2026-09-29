"""Preserve notices shipped with the interpreter sources and SDK runtime."""
from pathlib import Path
import re
import sys

source, output = map(Path, sys.argv[1:])
sdk = Path('/emsdk/upstream/emscripten')
files = {sdk / 'LICENSE', sdk / 'AUTHORS', Path('/patches/LICENSE')}
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
# Historical CPython embeds third-party notices in C comments as well as files
# named LICENSE (for example, Aladdin's MD5 implementation and dtoa.c).
for directory in ('Parser', 'Objects', 'Python', 'Modules', 'Include'):
    for path in sorted((source / directory).rglob('*')):
        if path.is_file() and path.suffix in ('.c', '.h'):
            comments = re.findall(r'/\*.*?\*/', path.read_text(errors='replace'), re.S)
            notices = [comment for comment in comments if re.search(
                r'copyright|permission|licen[cs]e|public domain', comment, re.I)]
            if notices:
                parts.append('\n' + '=' * 72 + '\n' + str(path) + '\n'
                             + '=' * 72 + '\n' + '\n\n'.join(notices))
output.write_text('\n'.join(parts) + '\n')
