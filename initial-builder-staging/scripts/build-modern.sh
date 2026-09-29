#!/bin/bash
set -euo pipefail
export CONFIG_SITE=/src/cpython/Platforms/emscripten/config.site-wasm32-emscripten
export CFLAGS='-O2 -DPY_CALL_TRAMPOLINE'
export LDFLAGS='-sMODULARIZE=1 -sEXPORT_ES6=1 -sENVIRONMENT=web,worker,node'
emconfigure /src/cpython/configure \
    --host=wasm32-unknown-emscripten \
    --build="$(/src/cpython/config.guess)" \
    --with-build-python=/src/native/python \
    --prefix=/ --without-ensurepip --disable-test-modules \
    --disable-shared --disable-wasm-dynamic-linking --disable-wasm-pthreads \
    --without-pymalloc --disable-ipv6 > /src/wasm-configure.log 2>&1 \
    || { tail -100 /src/wasm-configure.log; cat config.log; exit 1; }
