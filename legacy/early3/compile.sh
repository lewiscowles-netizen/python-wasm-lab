#!/usr/bin/env bash
set -euo pipefail
export SOURCE_DATE_EPOCH=1587254400
export PYTHONHASHSEED=0
export TZ=UTC
cd /build/wasm
minor=${PYTHON_VERSION%.*}
python3 - <<'PY'
import re
from pathlib import Path
p = Path('/build/source/Modules/posixmodule.c')
# CPython 3.0's private helper collides with a newer POSIX libc declaration.
p.write_text(re.sub(r'\bposix_close\b', '_Py_wasm_posix_close', p.read_text()))
PY
cat >> pyconfig.h <<'EOF'
#undef HAVE_DYNAMIC_LOADING
#undef HAVE_FORK
#undef HAVE_FORKPTY
#undef HAVE_EXECV
#undef HAVE_EXECVE
#undef HAVE_POSIX_SPAWN
#undef HAVE_POSIX_SPAWNP
#undef HAVE_PTHREAD_SIGMASK
/* Emscripten's musl implements the C99 long-long printf modifier. */
#ifndef PY_FORMAT_LONG_LONG
#define PY_FORMAT_LONG_LONG "ll"
#endif
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
if not Path('/build/source/Parser/intrcheck.c').exists():
    lines.append('signal signalmodule.c')
setup.write_text('\n'.join(lines) + '\n')
PY
emmake make Makefile
generated=()
signal_objects=()
if [[ ! -f /build/source/Parser/intrcheck.c ]]; then signal_objects+=(SIGNAL_OBJS=); fi
for file in Include/graminit.h Python/graminit.c Include/Python-ast.h Python/Python-ast.c Python/importlib.h Python/importlib_external.h Python/importlib_zipimport.h; do
  if [[ -f /build/source/$file ]]; then generated+=(-o "/build/source/$file"); fi
done
emmake make -j"${JOBS:-2}" "libpython${minor}.a" OPT='-DNDEBUG -O1 -fwrapv' PYTHON_FOR_BUILD=/bin/false DYNLOADFILE=dynload_stub.o "${generated[@]}" "${signal_objects[@]}"
