#!/usr/bin/env bash
set -euo pipefail
cd /build/source
patch -p1 < /patches/python2-cross_compile.patch
patch -p1 < /patches/python2-no_popen.patch
mkdir -p /build/wasm /out
cd /build/wasm
CONFIG_SITE=/build/source/config.site \
 PYTHON_FOR_BUILD=/bin/false \
 emconfigure /build/source/configure \
 --host=asmjs-unknown-emscripten --build=$(/build/source/config.guess) \
 --prefix=/python --without-threads --without-pymalloc \
 --without-signal-module --disable-ipv6 --disable-shared
