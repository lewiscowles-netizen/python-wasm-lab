#!/usr/bin/env bash
set -euo pipefail
export SOURCE_DATE_EPOCH=1587254400
export PYTHONHASHSEED=0
export TZ=UTC
cd /build/wasm
mkdir -p /package/python/lib/python2.7
cp -a /build/source/Lib/. /package/python/lib/python2.7/
mkdir -p /package/python/lib/python2.7/lib-dynload
touch /package/python/lib/python2.7/lib-dynload/.keep
# The static-library build intentionally skips setup.py's generated metadata.
# site.py requires the module even when no extension build toolchain is shipped.
printf 'build_time_vars = {}\n' > /package/python/lib/python2.7/_sysconfigdata.py
rm -rf /package/python/lib/python2.7/test /package/python/lib/python2.7/idlelib /package/python/lib/python2.7/lib-tk
# This historical Clang ignores SOURCE_DATE_EPOCH for these C macros.
emcc -c -O1 -I/build/wasm -I/build/source/Include -DPy_BUILD_CORE \
 '-DDATE="Apr 19 2020"' '-DTIME="00:00:00"' \
 /build/source/Modules/getbuildinfo.c -o Modules/getbuildinfo.o
emar r libpython2.7.a Modules/getbuildinfo.o
emcc -O2 /build/source/Modules/python.c libpython2.7.a \
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
