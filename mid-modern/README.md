# CPython 3.11–3.13 source build branch

`python3 build.py 3.11 3.12 3.13` uses Docker buildx to compile the pinned source archives into Emscripten artifacts. Each build uses two compiler jobs, and writes its log under `logs` and verified artifacts under `builds/<patch-version>`.

The build first creates native CPython for generators, then cross-compiles a static, single-threaded interpreter with Emscripten 5.0.3 using the builder host's architecture. Browser/worker/Node glue exports `callMain` and `FS`. The stdlib source is stored in a deterministic uncompressed ZIP inside the preload data file. This branch uses function-pointer-cast emulation for compatibility with older CPython and intentionally disables Wasm dynamic linking and pthreads.

An initial Emscripten 3.1.73 amd64 attempt is retained as `Dockerfile.sdk3.1.73-amd64` with logs. Under Apple Silicon emulation, its native bootstrap alone took over ten minutes, so the active builder moved to the native-architecture SDK 5.0.3 image. A cancelled build is not evidence of an invalid recipe or a successful target artifact.

The final stage runs the produced interpreter in Node, checks its version and basic stdlib/filesystem behavior, probes optional modules, and generates `smoke.json` and `manifest.json`. Browser validation is a separate step. This is a minimal CPython runtime, not a Pyodide distribution or a claim of Pyodide-wheel ABI compatibility.

The base compiler image and source archives are digest-pinned. Ubuntu package metadata is not snapshot-pinned, and byte-identical clean rebuilds have not been established. Runtime behavior and byte reproducibility must be reported separately.
