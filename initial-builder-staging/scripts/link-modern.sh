#!/bin/bash
set -euo pipefail
# The upstream helper enables dynamic linking, which brings addFunction in as
# a dependency. Our static profile must retain it explicitly for CPython's
# Wasm-GC call trampoline and allow the trampoline table entry to be appended.
flags='-sMODULARIZE=1 -sEXPORT_ES6=1 -sENVIRONMENT=web,worker,node -sALLOW_TABLE_GROWTH=1 --preload-file /bundle@/'
link_flags="$(sed -n 's/^LINKFORSHARED=[[:space:]]*//p' Makefile) -sEXPORTED_RUNTIME_METHODS=FS,callMain,ENV,HEAPU32,TTY,ERRNO_CODES,addFunction"
make -j"${JOBS}" LDFLAGS="${flags}" LINKFORSHARED="${link_flags}" python.mjs > /src/wasm-link.log 2>&1 \
    || { tail -100 /src/wasm-link.log; exit 1; }
