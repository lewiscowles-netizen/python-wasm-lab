# CPython 3.4–3.10 static browser port

This work uses the pinned Emscripten 5.0.3 image and checksummed CPython release
archives. The browser profile builds a static interpreter and raw-source stdlib;
it does not build native wheels, threads, processes or sockets.

## Observed failures and fixes

- CPython 3.10.21 configured and compiled its interpreter with current Clang.
  The POSIX source overrides configure's `HAVE_FORK` result on generic Unix.
  Guard those overrides for Emscripten and disable process-only APIs in
  `pyconfig.h`; leaving `HAVE_FEXECVE` enabled also compiles the unavailable
  exec environment parser.
- Linking then exposed `memfd_create`: the SDK declares this Linux facility
  but does not provide a browser implementation. Disable its feature macro;
  undefined-symbol errors remain enabled throughout linking.
- An empty `lib-dynload` directory is omitted by the Emscripten file packager.
  A marker file retains the directory and removes CPython's startup path
  warning. This does not enable dynamic extension loading.
- Use release-generated grammar, AST and frozen importlib headers. These old
  versions otherwise attempt to execute a target Wasm generator during build.
  No host-generated foreign-version bytecode is put in the stdlib.
- File-descriptor inheritance has no process counterpart in this profile;
  `set_inheritable` returns success. Files themselves remain ordinary MEMFS
  files, verified by writing and reading a file inside the Wasm interpreter.

The first 3.10.21 execution passed version, arithmetic, JSON, math, regex and
filesystem assertions. Its initial startup warning is recorded in the build
log and corrected by the directory marker before browser export.

## Configure facts

`configuration/3.10.21` records the full configure log, header and Makefile from
a real wasm32 configure run on the exact SDK. Reused facts are restricted to
libc functions, headers, target sizes and types on this same SDK. They are not
native host results or a promise that every exposed POSIX function works in a
browser. Browser capability exclusions are applied separately.

## Additional real compatibility fixes

- CPython 3.4 and 3.7 declared `_PyTraceMalloc_Fini` as returning `int`, while
  the implementation returns `void`. Wasm linking warned and execution trapped
  at interpreter finalization. Correcting the declaration fixes the ABI; the
  build does not suppress undefined-symbol errors or ignore runtime traps.
- The CPython 3.7 executable entry point uses a private core API. Compile that
  entry point with `Py_BUILD_CORE`, matching upstream make behavior.
- CPython 3.4 imports `_sysconfigdata` during normal site initialization. The
  stdlib packager now derives its build variables from the target Makefile and
  target pyconfig header, including browser exclusions. It also writes the
  platform-specific module name used by 3.6 and later.
- The old `--without-signal-module` configure path refers to removed build
  objects in 3.4; use the normal signal-module build. Browser delivery of
  native process signals is not part of this runtime contract.
