#!/usr/bin/env bash
set -euo pipefail
export SOURCE_DATE_EPOCH=1789430400
export PYTHONHASHSEED=0
export TZ=UTC
cd /build/wasm
python3 - <<'PY'
from pathlib import Path
import re
p = Path('/build/source/Modules/posixmodule.c')
text = p.read_text()
text = re.sub(r'(?m)^(#\s*define\s+(?:HAVE_FORK|HAVE_EXECV|HAVE_POPEN)\s+1[^\n]*)$',
              r'#ifndef __EMSCRIPTEN__\n\1\n#endif', text)
p.write_text(text)
p = Path('/build/source/Objects/object.c')
text = p.read_text()
for call in ('PyGILState_STATE gil;', 'gil = PyGILState_Ensure();', 'PyGILState_Release(gil);'):
    text = text.replace(call, '\n#ifdef WITH_THREAD\n' + call + '\n#endif\n')
p.write_text(text)
for p in Path('/build/source/Python').glob('*.c'):
    text = p.read_text()
    corrected = text.replace('extern int _PyTraceMalloc_Fini(void);', 'extern void _PyTraceMalloc_Fini(void);')
    corrected = corrected.replace('    PyThreadState *tss_tstate = PyGILState_GetThisThreadState();',
        '#ifdef WITH_THREAD\n    PyThreadState *tss_tstate = PyGILState_GetThisThreadState();\n'
        '#else\n    PyThreadState *tss_tstate = PyThreadState_GET();\n#endif')
    if text != corrected:
        p.write_text(corrected)
p = Path('/build/source/Python/fileutils.c')
if p.exists():
    text = p.read_text()
    marker = '#ifdef __EMSCRIPTEN__\n    return 0; /* No subprocesses or inherited FDs in this browser build. */\n#endif'
    if marker in text:
        start = text.index(marker)
        end = text.index('\n}', start)
        text = text[:end] + '\n#endif' + text[end:]
        text = text.replace(marker, marker.removesuffix('#endif') + '#else')
        p.write_text(text)
PY
minor=${PYTHON_VERSION%.*}
cat >> pyconfig.h <<'EOF'
#undef HAVE_DYNAMIC_LOADING
#undef HAVE_FORK
#undef HAVE_FORKPTY
#undef HAVE_EXECV
#undef HAVE_EXECVE
#undef HAVE_FEXECVE
#undef HAVE_MEMFD_CREATE
#undef HAVE_RTPSPAWN
#undef HAVE_POPEN
#undef HAVE_POSIX_SPAWN
#undef HAVE_POSIX_SPAWNP
#undef HAVE_PTHREAD_SIGMASK
EOF
cat > Modules/Setup.local <<'EOF'
*static*
math mathmodule.c _math.c
_struct _struct.c
binascii binascii.c
_random _randommodule.c
_collections _collectionsmodule.c
_functools _functoolsmodule.c
itertools itertoolsmodule.c
operator operator.c
time timemodule.c
_heapq _heapqmodule.c
_md5 md5module.c
_sha1 sha1module.c
_sha256 sha256module.c
_sha512 sha512module.c
EOF
# Module names/source organization vary between release families.
python3 - <<'PY'
from pathlib import Path
setup = Path('Modules/Setup.local')
lines = []
for line in setup.read_text().splitlines():
    if line.startswith('math ') and not Path('/build/source/Modules/_math.c').exists():
        line = 'math mathmodule.c'
    if line.startswith('operator ') and not Path('/build/source/Modules/operator.c').exists():
        line = '_operator _operator.c'
    if all(Path('/build/source/Modules', token).exists() for token in line.split()[1:] if token.endswith('.c')):
        lines.append(line)
if Path('/build/source/Modules/_fileio.c').exists():
    lines.append('_fileio _fileio.c')
if Path('/build/source/Modules/_io/_iomodule.c').exists():
    lines.append('_io _io/_iomodule.c _io/iobase.c _io/fileio.c _io/bytesio.c _io/bufferedio.c _io/textio.c _io/stringio.c')
setup.write_text('\n'.join(lines) + '\n')
PY
emmake make Makefile
generated=()
for file in Include/graminit.h Python/graminit.c Include/Python-ast.h Python/Python-ast.c Python/importlib.h Python/importlib_external.h Python/importlib_zipimport.h; do
  if [[ -f /build/source/$file ]]; then generated+=(-o "/build/source/$file"); fi
done
emmake make -j2 "libpython${minor}.a" OPT='-DNDEBUG -O1 -fwrapv' PYTHON_FOR_BUILD=/bin/false DYNLOADFILE=dynload_stub.o "${generated[@]}"
