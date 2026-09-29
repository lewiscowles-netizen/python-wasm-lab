# Legacy CPython to genuine WebAssembly: live porting record

This directory owns 2.7 and pre-upstream-Wasm CPython exploration. It does not
claim an interpreter works until the resulting Wasm passes its runtime smoke.

## Source and toolchain

- Python 2.7.18 official release archive, SHA-256
  `b62c0e7937551d0cc02b8fd5cb0f544f9405bafc9a54d3808ed4594812edef43`.
- `emscripten/emsdk:2.0.2`, immutable image digest
  `sha256:d2daf8d497c38f69e854239b06679184dcb676580fcb56146a3ad6f559b47aa6`.
- [python-emscripten/python](https://github.com/python-emscripten/python), commit
  `b8f7eafbb238e150f2f2e032b10d362d83b2aed6`: 2.7.18 cross-compile and no-popen
  patches retained with original attribution and permission notice. The port
  was maintained for Ren'Py's browser build. Its README specifies SDK 2.0.2.
- `pyenv-definitions/` contains the source-lock definitions retrieved for each
  3.0–3.10 minor. `early3/sources.json` extracts official source URL and hash.

The historical `asmjs-unknown-emscripten` configure name is accepted by the
upstream 2.7 patch. It does not select asm.js output: Emscripten 2 emits Wasm by
default, and the smoke explicitly validates `00 61 73 6d` binary magic.

## Commands and current evidence

```sh
docker buildx build --platform linux/amd64 --progress plain \
  --output type=local,dest=dist/2.7.18 . > build-2.7.18.log 2>&1
docker buildx build --platform linux/amd64 --progress plain \
  --target configured --build-arg PYTHON_VERSION=3.0.1 early3 \
  > build-3.0.1-configure.log 2>&1
```

| Version | Current evidence |
| --- | --- |
| 2.7.18 | **PASS** Docker Buildx + Node exact-version/arithmetic/stdlib/Wasm smoke; artifacts in dist/2.7.18 |
| 3.0.1 | **PASS** Docker Buildx + Node exact-version/arithmetic/stdlib/Wasm smoke; artifacts in dist/3.0.1 |
| 3.1.5 | **PASS** Docker Buildx + Node exact-version/arithmetic/stdlib/Wasm and exception-exit smoke |
| 3.2.6 | **PASS** full Buildx/Node runtime smoke with actual sysconfig installation metadata |
| 3.3.7 | **PASS** full Buildx/Node runtime smoke; maxunicode 1114111 and astralLength 1 |
| 3.4.10–3.10.21 | Main task owns transitional builds |

## Findings and corrections

1. A native build was initially started but stopped during configure. The
   narrow `libpython2.7.a` target consumes generated grammar/AST files already
   in the release archive, so there is no need to run an old native Python for
   this build path. `PYTHON_FOR_BUILD=/bin/false` is an intentional sentinel:
   if a recipe unexpectedly tries to regenerate files, the build must fail.
2. The Docker cache separates source/configure, static compilation, and final
   linking so browser-loader changes do not repeat expensive configure probes.
3. CPython 3.0.1 does not ship `config.sub` or `config.guess`. The experimental
   early3 recipe now handles their absence and passes the known builder triple.
4. CPython 3.0's configure has three fatal cross-runtime tests. The port disables
   chflags/lchflags and supplies musl's standard `%zd` format capability.
5. SDK 2's data loader rejects Node before asking for a preloaded data buffer.
   A narrowly asserted generated-loader edit permits the wrapper to supply
   exact Wasm and stdlib bytes. The wrapper presents `python.mjs` and
   `module.callMain(['-c', source])` to both Node and the browser.
6. This is a static interpreter profile: no pip, SSL, SQLite, native extension
   loading, subprocesses or real network sockets are claimed. Pure-Python
   standard-library files are preloaded; selected C modules are linked in.

## Consumer contract

Each call to the factory creates a separate Emscripten instance. Treat
`callMain` as one Python CLI process; create a fresh instance for each run.
Artifacts are `python.mjs`, `python.wasm`, `python.data`,
plus a JSON smoke record. Browser code should use a Worker for responsiveness.
The JS bridge handles output and virtual files, not Pyodide's rich JsProxy API.

### Why the 2.7 smoke checks arithmetic

The test requires `sys.version_info[:3] == (2, 7, 18)` and `7/2 == 3`, then
executes JSON, math and SHA-256. A 3.x interpreter with its label changed would
fail both the exact-version and old-division assertions. The early3 test instead
requires its exact release and `7/2 == 3.5`. Both verify the binary Wasm magic.
These are minimal integration checks; passing does not imply CPython's full
regression suite passes in a browser.

### Static versus dynamic support

The final 2.7 compile disables `HAVE_DYNAMIC_LOADING` and links
`dynload_stub.o`; configure's inherited Ren'Py patch originally selected
`dlopen` support. Runtime extension loading therefore cannot accidentally be
claimed merely because an Emscripten libc stub linked. Native extensions require
new static modules, matching Wasm side modules, or a Pyodide distribution.

### Early 3.x generated code

Python 3.0's Makefile automatically depends on a `Parser/pgen` executable even
when release-generated grammar sources are present. The experimental early3
build marks the released grammar, AST and frozen-import sources as already
current (`make -o` for existing generated files). It compiles their exact
release content rather than trying to execute a target-Wasm generator in Linux.
`PYTHON_FOR_BUILD=/bin/false` remains a guard against unplanned regeneration.

### Reproducibility controls

Sources and toolchain are hash pinned. Compilation/linking set
`SOURCE_DATE_EPOCH=1587254400`, `PYTHONHASHSEED=0`, and `TZ=UTC` so compiler date
macros and host environment do not vary silently. Static objects use `-O1` for
this initial compatibility profile; final link uses `-O2`. This establishes a
repeatable recipe, but byte-for-byte reproduction has not yet been tested.

### Wasm C-call signatures and entropy

The old CPython C API casts function pointers between calling conventions.
WebAssembly validates indirect-call signatures, so the historical port requires
`EMULATE_FUNCTION_POINTER_CASTS=1` at link time. This is a compatibility/performance
tradeoff; modern upstream CPython has dedicated Emscripten call trampolines.

The universal ESM build targets browser/worker glue and loads bytes explicitly
under Node. SDK 2's browser glue cannot discover Node 12's cryptographic RNG.
`entropy.js` accepts a per-instance provider; the Node adapter supplies
`crypto.randomFillSync`, while browsers use Web Crypto. No global monkey-patch or
insecure random fallback is used.

### Measured configure cache now available

The 2.7 target configure completed successfully. Its exact `config.log`,
`pyconfig.h` and generated `Makefile` are in `configuration/2.7.18/`. Extracted
229 generic C header/function/type/size checks into
`early3/emscripten-2.0.2.config.site` to avoid repeating them for each old minor.
Only the same pinned SDK and wasm32 target may consume these facts. Explicit
browser-profile exclusions follow the shared facts and override them. Python
version-specific configure logic still runs normally.

### First 2.7 runtime failure and correction

The full C core and selected modules compiled, linked into Wasm and initialized
under Node. Startup then failed in `site.py`: the narrow static-library target
does not generate `_sysconfigdata.py`. The minimal runtime now includes
`build_time_vars = {}`, matching the upstream Ren'Py packager, and creates the
expected empty `lib-dynload` path to avoid prefix warnings. This supports normal
site initialization without claiming an extension-building toolchain is present.

The second smoke executed real Python 2.7.18, JSON, math and SHA-256 correctly,
but the strict no-stderr check caught two prefix warnings. Emscripten omits empty
directories from preload packages, so `lib-dynload/.keep` now ensures that path
exists at runtime. The same run showed this old Clang ignores SOURCE_DATE_EPOCH
for CPython's date macros; final linking now recompiles only getbuildinfo.o with
explicit deterministic DATE/TIME definitions. The complete smoke is rerun.

### Verified 2.7.18 milestone

`dist/2.7.18/` contains the actual exported Wasm and ESM runtime. Docker's Node
12 smoke and the host's current Node both passed. Exact runtime version is
2.7.18, platform is emscripten, `7/2` returns 3, and JSON/math/hashlib checks pass
without interpreter stderr. `smoke.json` and SHA-256 manifest accompany the
artifacts. This is a minimal integration pass, not a full CPython test-suite pass.
The output's combined uncompressed size is about 16.45 MB. Browser verification
is delegated to the main task's shared application harness.

### Python 3.0.1 compile correction

Its core and almost all C modules compiled. `Modules/posixmodule.c` then collided
with musl's public `posix_close(int, int)` declaration: this old CPython used the
same name for a private Python-callable helper. The compile recipe now renames
only that C identifier to `_Py_wasm_posix_close`; Python's public `os.close`
interface is unchanged. This demonstrates why old-minor branch-specific
compatibility patches are preferable to changing the reported version of a newer
interpreter.

Python 3.0.1 next reached the final link, exposing an upstream threadless-build
bug: `_PyObject_Dump` calls PyGILState_Ensure/Release even when their
implementations were excluded with `--without-threads`. Its two debugging-only
calls are now guarded with WITH_THREAD and that one object is rebuilt before
linking. No fake GIL implementation or unresolved-symbol suppression is used.

Python 3.1.5's configure has two unconditional cross-runtime tests: broken
sem_getvalue and `%zd` formatting. They need explicit browser/musl answers;
initial configure correctly stopped rather than executing a target artifact.

### Nonzero exit propagation

The shared browser consumer exposed an SDK 2 integration trap: callMain catches
its ExitStatus exception and `noExitRuntime` suppresses onExit, so return values
alone incorrectly look successful. The ESM wrapper now records the underlying
Module.quit status and returns it from callMain. Both legacy smoke scripts create
a second fresh interpreter, raise ValueError deliberately, and require exit 1
plus the expected traceback. These are application-visible correctness checks.

### Additional measured historical behavior

On the current host Node, 2.7.18's MEMFS byte write/read probe passed and printing
a Unicode snowman succeeded with UTF-8 stdout. Both 2.7.18 and 3.0.1 use the
source defaults for Unicode: `sys.maxunicode == 65535`; an astral character has
string length 2. This is the old narrow-Unicode build choice, not a Wasm parsing
error. Before [PEP 393](https://peps.python.org/pep-0393/), `--enable-unicode=ucs4`
could select a different CPython Unicode ABI. Exact version, source hash,
compiler and configure flags all matter when describing compatibility.

### Python 3.2 long-long format probe

Python 3.2.6 completed configure but its runtime printf probe left
PY_FORMAT_LONG_LONG undefined when cross-compiling. The first C compilation
correctly failed with that missing prerequisite. The fixed profile supplies
the C99 `ll` modifier implemented by the pinned Emscripten musl libc. This is
an explicit target-library fact, and the smoke verifies integer formatting,
arithmetic and SHA-256 through the resulting interpreter.

Python 3.2's static time module next exposed a source-list difference: it needs
`Modules/_time.c` for its checked double-to-time_t conversion. The final link
now builds and archives that release's actual implementation. Undefined symbols
remain fatal; no missing-function stubs or link-error suppression are used.

Python 3.3's source removed Parser/intrcheck.c but configure retained a broken
--without-signal-module path that names its missing object. The 3.3 profile now
selects its actual signalmodule.c and clears that obsolete SIGNAL_OBJS list.
This supplies interpreter interrupt machinery; browser OS-signal delivery is
still not promised.

Python 3.2.6 reached runtime initialization, where site.py imports sysconfig.
That release reads its installed Makefile and pyconfig.h directly, unlike the
_sysconfigdata path used elsewhere. Packaging now includes the actual configured
Makefile and pyconfig.h at its ABI-specific install locations. This is runtime
installation metadata; it does not install a compiler or package manager.
