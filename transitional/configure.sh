#!/bin/bash
set -euo pipefail
python3 /recipe/port.py
mkdir -p /build/wasm /out
cd /build/wasm
cp /recipe/sdk-config.site /build/config.site
cat >> /build/config.site <<'EOF'
ac_cv_file__dev_ptmx=no
ac_cv_file__dev_ptc=no
ac_cv_func_dlopen=no
ac_cv_func_fork=no
ac_cv_func_vfork=no
ac_cv_func_posix_spawn=no
ac_cv_func_posix_spawnp=no
ac_cv_func_pthread_sigmask=no
ac_cv_buggy_getaddrinfo=no
EOF
export CFLAGS='-O2 -Wno-error=implicit-function-declaration -Wno-error=incompatible-pointer-types'
CONFIG_SITE=/build/config.site PYTHON_FOR_BUILD=/bin/false \
 MACHDEP=emscripten ac_sys_system=Emscripten ac_sys_release=5.0.3 READELF=true \
 emconfigure /build/source/configure \
 --host=wasm32-unknown-emscripten --build="$(gcc -dumpmachine)" \
 --prefix=/python --without-pymalloc --disable-ipv6 --disable-shared \
 --without-threads --without-ensurepip
