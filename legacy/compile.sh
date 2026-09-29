# Description: static CPython 2.7 core and selected extension modules.
#!/usr/bin/env bash
set -euo pipefail
export SOURCE_DATE_EPOCH=1587254400
export PYTHONHASHSEED=0
export TZ=UTC
cd /build/wasm
cat >> pyconfig.h <<'EOF'
/* This distribution only loads statically linked C modules. */
#undef HAVE_DYNAMIC_LOADING
/* Process creation has no implementation in this browser profile. */
#undef HAVE_FORK
#undef HAVE_FORKPTY
#undef HAVE_EXECV
#undef HAVE_EXECVE
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
_md5 md5module.c md5.c
_sha shamodule.c
_sha256 sha256module.c
_sha512 sha512module.c
_io _io/_iomodule.c _io/iobase.c _io/fileio.c _io/bytesio.c _io/bufferedio.c _io/textio.c _io/stringio.c
EOF
emmake make Makefile
# The release tarball already contains generated grammar and AST sources.
# Building only the static library does not require a native interpreter.
# A failing sentinel prevents silently using an incompatible host Python.
emmake make -j"${JOBS:-2}" libpython2.7.a OPT='-DNDEBUG -O1 -fwrapv' PYTHON_FOR_BUILD=/bin/false DYNLOADFILE=dynload_stub.o
