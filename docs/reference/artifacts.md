# Runtime artifact reference

This reference describes the WebAssembly (Wasm) files exchanged between the Python builder and this browser lab. It applies to the `emscripten` adapter; a WebAssembly System Interface (WASI) command module requires a different host adapter. See [runtime alternatives](../explanation/runtime-alternatives.md).

## Bundle files

Each imported version occupies `experiments/wasm/python/builds/build-<version>/`.

| File | Interface |
| --- | --- |
| `python.mjs` | JavaScript module whose default export is an asynchronous Emscripten factory |
| `python.wasm` | Interpreter and compiled libraries, targeting `wasm32-emscripten` |
| `python.data` | That interpreter's packaged standard library and virtual filesystem contents |
| `manifest.json` | Source, compiler, features, recorded Node.js checks and file hashes |
| `smoke.json`, `smoke.mjs` | Recorded build-time results and their executable check |
| `CPYTHON-LICENSE.txt`, `THIRD-PARTY-NOTICES.txt` | Runtime distribution notices |

Files from different builds are not interchangeable, even when their Python version labels match. The loader and data package belong to the same link output. Sizes and measured modules are in the [runtime matrix](runtimes.md).

## Catalog schema

Both catalogs use `{"schemaVersion": 1, "runtimes": [...]}` in JavaScript Object Notation (JSON). The tracked `runtimes.json` describes Pyodide. The generated, Git-ignored `runtimes.local.json` describes imported builds. Entries merge by `id`; local entries take precedence. A missing local catalog is allowed. Other fetch failures or invalid schema versions stop catalog loading.

| Entry field | Meaning |
| --- | --- |
| `id`, `label` | Unique selector value and displayed distribution name |
| `version` | Exact CPython version for local builds; also determines sorting and stable default selection |
| `adapter` | `emscripten` or `pyodide` |
| `module` | Loader address, relative to the playground directory unless absolute |
| `manifest` | Optional manifest address, relative to the playground directory |
| `invocation` | `callMain` by default; `arguments` for a loader that executes during initialization |
| `wasm`, `data` | Optional filenames relative to the loader; defaults are `python.wasm` and `python.data`; `data: false` omits the data fetch |
| `description`, `capabilities` | Optional displayed text and capability declarations |

## Emscripten factory interface

The worker supplies `wasmBinary`, `getPreloadedPackage`, `locateFile`, output callbacks, immediate-end-of-file `stdin`, and exit/error callbacks. `callMain` mode uses `noInitialRun: true`, then calls `callMain(['-c', wrappedSource])` once. An older loader may report its exit through `quit`, `onExit`, a return value or an `ExitStatus` exception; the adapter handles those paths. [Worker messages and user controls](../../experiments/wasm/python/README.md) are a separate interface.

## Import validation

The lab importer delegates to the builder's exporter. Before copying, it checks every manifest-declared file's byte size and 256-bit Secure Hash Algorithm (SHA-256) checksum, required runtime files, the Wasm signature and the version in recorded smoke output. It copies all declared files and the manifest, then updates the local catalog. Importing does not execute a fresh browser test or prove the recorded Node.js result was freshly reproduced. The browser loader itself does not recheck these checksums; [validation evidence](validation.md) identifies tested bytes.

Source: [importer](../../scripts/import-runtimes.py) and [builder exporter](https://github.com/lewiscowles-netizen/python-wasm-builder/blob/ce8b58b131eec715ad7380688508c5bc9bf27905/scripts/export-site.py).
