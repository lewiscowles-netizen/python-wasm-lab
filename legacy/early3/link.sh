#!/usr/bin/env bash
set -euo pipefail
export SOURCE_DATE_EPOCH=1587254400
export PYTHONHASHSEED=0
export TZ=UTC
cd /build/wasm
minor=${PYTHON_VERSION%.*}
mkdir -p /package/python/lib/python${minor}
cp -a /build/source/Lib/. /package/python/lib/python${minor}/
mkdir -p /package/python/lib/python${minor}/lib-dynload
touch /package/python/lib/python${minor}/lib-dynload/.keep
if [[ -f /build/source/Lib/sysconfig.py ]]; then
  printf 'build_time_vars = {}\n' > /package/python/lib/python${minor}/_sysconfigdata.py
fi
if [[ "$PYTHON_VERSION" == 3.2.6 ]]; then
  # This release reads installation metadata directly during site startup.
  mkdir -p /package/python/lib/python3.2/config-3.2 /package/python/include/python3.2
  cp Makefile /package/python/lib/python3.2/config-3.2/Makefile
  cp pyconfig.h /package/python/include/python3.2/pyconfig.h
fi
rm -rf /package/python/lib/python${minor}/test /package/python/lib/python${minor}/idlelib /package/python/lib/python${minor}/lib-tk
emcc -c -O1 -I/build/wasm -I/build/source/Include -DPy_BUILD_CORE \
 '-DDATE="Apr 19 2020"' '-DTIME="00:00:00"' \
 /build/source/Modules/getbuildinfo.c -o Modules/getbuildinfo.o
emar r "libpython${minor}.a" Modules/getbuildinfo.o
if [[ "$PYTHON_VERSION" == 3.2.6 ]]; then
  # Python 3.2 keeps timemodule's checked double-to-time_t conversion separately.
  emcc -c -O1 -fwrapv -I/build/wasm -I/build/source/Include -DPy_BUILD_CORE \
    /build/source/Modules/_time.c -o Modules/_time.o
  emar r "libpython${minor}.a" Modules/_time.o
fi
if [[ "$PYTHON_VERSION" == 3.0.1 ]]; then
  # Its debug dump helper unconditionally calls GIL APIs even without threads.
  python3 - <<'PY'
from pathlib import Path
p = Path('/build/source/Objects/object.c')
s = p.read_text()
for call in ('gil = PyGILState_Ensure();', 'PyGILState_Release(gil);'):
    assert s.count(call) == 1
    s = s.replace(call, '\n#ifdef WITH_THREAD\n' + call + '\n#endif\n')
p.write_text(s)
PY
  emcc -c -O1 -fwrapv -I/build/wasm -I/build/source/Include -DPy_BUILD_CORE \
    /build/source/Objects/object.c -o Objects/object.o
  emar r "libpython${minor}.a" Objects/object.o
fi
MAIN_SOURCE=/build/source/Modules/python.c
if [[ -f /build/source/Programs/python.c ]]; then MAIN_SOURCE=/build/source/Programs/python.c; fi
emcc -O2 "${MAIN_SOURCE}" "libpython${minor}.a" \
 -I/build/wasm -I/build/source/Include \
 -s EMULATE_FUNCTION_POINTER_CASTS=1 -s ALLOW_MEMORY_GROWTH=1 \
 -s FORCE_FILESYSTEM=1 -s MODULARIZE=1 -s EXPORT_NAME=createPython \
 -s EXPORT_ES6=1 -s ENVIRONMENT=web,worker \
 -s INVOKE_RUN=0 -s EXIT_RUNTIME=0 \
 -s EXPORTED_FUNCTIONS='["_main"]' \
 -s EXTRA_EXPORTED_RUNTIME_METHODS='["callMain","FS"]' \
 --pre-js /recipe/entropy.js --preload-file /package/python@/python -o /out/python.js
# SDK 2.0.2's data packager rejects Node before consulting getPreloadedPackage.
# No browser path is needed when the wrapper supplies the bytes directly.
python3 - <<'PY'
from pathlib import Path
import re
p = Path('/out/python.js')
s = p.read_text()
pattern = r"throw\s*(['\"])using preloaded data can only be done on a web page or in a web worker\1;?"
s, count = re.subn(pattern, "void 0;", s)
assert count == 1, 'Expected SDK 2.0.2 preloader guard exactly once'
wrapper = Path('/recipe/python.mjs').read_text().replace("import createCore from './python-core.mjs';", 'const createCore = createPython;').replace('export default async function createPython(', 'export default async function createPythonRuntime(')
assert 'export default createPython;' in s
Path('/out/python.mjs').write_text(s.replace('export default createPython;', wrapper))
p.unlink()
PY
cp /recipe/smoke.mjs /out/
cd /out
node --experimental-modules smoke.mjs
cp /build/source/LICENSE /out/CPYTHON-LICENSE.txt
python3 /recipe/notices.py /build/source /out/THIRD-PARTY-NOTICES.txt
python3 /recipe/manifest.py
