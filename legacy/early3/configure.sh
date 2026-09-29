#!/usr/bin/env bash
set -euo pipefail
python3 /recipe/port.py
mkdir -p /build/wasm /out
cd /build/wasm
cp /recipe/emscripten-2.0.2.config.site /build/config.site
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
ac_cv_posix_semaphores_enabled=no
EOF
CONFIG_SITE=/build/config.site PYTHON_FOR_BUILD=/bin/false \
 MACHDEP=emscripten ac_sys_system=Emscripten ac_sys_release=2.0.2 READELF=true \
 emconfigure /build/source/configure \
 --host=wasm32-unknown-emscripten --build=x86_64-pc-linux-gnu \
 --prefix=/python --without-pymalloc --disable-ipv6 --disable-shared \
 --without-threads --without-signal-module --without-ensurepip
