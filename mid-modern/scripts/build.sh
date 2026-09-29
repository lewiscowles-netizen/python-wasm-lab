#!/bin/bash
set -euo pipefail
export CONFIG_SITE=/src/cpython/Tools/wasm/config.site-wasm32-emscripten
export CFLAGS='-O2'
export LDFLAGS='-sMODULARIZE=1 -sEXPORT_ES6=1 -sENVIRONMENT=web,worker,node -sEMULATE_FUNCTION_POINTER_CASTS=1 -sEXPORTED_RUNTIME_METHODS=callMain,FS -sSTACK_SIZE=5MB'
emconfigure /src/cpython/configure \
    --host=wasm32-unknown-emscripten \
    --build="$(/src/cpython/config.guess)" \
    --with-build-python=/src/native/python \
    --with-emscripten-target=browser --with-suffix=.mjs \
    --prefix=/ --without-ensurepip --disable-test-modules \
    --disable-shared --disable-wasm-dynamic-linking --disable-wasm-pthreads \
    --without-pymalloc --disable-ipv6 > /src/wasm-configure.log 2>&1 \
    || { tail -100 /src/wasm-configure.log; exit 1; }
make -j"${JOBS}" LINKFORSHARED='-O2 -g0 --preload-file /bundle@/' python.mjs > /src/wasm-build.log 2>&1 \
    || { tail -100 /src/wasm-build.log; exit 1; }
