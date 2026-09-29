#!/bin/bash
set -euo pipefail
cd /build/wasm
minor=${PYTHON_VERSION%.*}
python3 /recipe/stdlib.py /build/source/Lib /bundle/python/lib "${minor}"
main=/build/source/Modules/python.c
if [[ -f /build/source/Programs/python.c ]]; then main=/build/source/Programs/python.c; fi
emcc -O2 -g2 -DPy_BUILD_CORE "${main}" "libpython${minor}.a" \
 -I/build/wasm -I/build/source/Include -I/build/source/Include/internal \
 -sEMULATE_FUNCTION_POINTER_CASTS=1 -sALLOW_MEMORY_GROWTH=1 -sSTACK_SIZE=5MB \
 -sFORCE_FILESYSTEM=1 -sMODULARIZE=1 -sEXPORT_NAME=createPython \
 -sEXPORT_ES6=1 -sENVIRONMENT=web,worker,node \
 -sINVOKE_RUN=0 -sEXIT_RUNTIME=1 \
 -sEXPORTED_FUNCTIONS=_main -sEXPORTED_RUNTIME_METHODS=callMain,FS \
 --preload-file /bundle@/ -o /out/python.mjs
