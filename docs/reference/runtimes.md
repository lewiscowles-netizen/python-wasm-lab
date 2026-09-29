# Runtime compatibility reference

This is the measured 2026-09-29 snapshot of the imported WebAssembly (Wasm) builds. It is not a promise about every upstream Python installation. Sizes count the uncompressed loader, interpreter and standard-library data together; one mebibyte (MiB) is 1,048,576 bytes. They are not browser transfer sizes or memory-use measurements.

## Available interpreters

| CPython | Runtime MiB |
| --- | ---: |
| 2.7.18 | 15.67 |
| 3.0.1 | 9.77 |
| 3.1.5 | 10.58 |
| 3.2.6 | 11.79 |
| 3.3.7 | 12.85 |
| 3.4.10 | 11.46 |
| 3.5.10 | 11.91 |
| 3.6.15 | 11.92 |
| 3.7.17 | 12.32 |
| 3.8.20 | 12.61 |
| 3.9.25 | 12.96 |
| 3.10.21 | 13.13 |
| 3.11.16 | 17.84 |
| 3.12.14 | 17.77 |
| 3.13.15 | 17.04 |
| 3.14.7 | 17.39 |
| 3.15.0rc2 | 17.99 |

3.15.0rc2 is a release candidate. The separate pinned Pyodide 314.0.7 distribution reports CPython 3.14.2. Pyodide's distribution version and its embedded Python version are different identifiers.

All local profiles target `wasm32-emscripten` and declare an in-memory filesystem, no Python package installer, no threads and no dynamically loaded extensions. The [selector reference](../../experiments/wasm/python/README.md) defines ordering and defaults. The [alternative-runtime comparison](../explanation/runtime-alternatives.md) explains the different implementation surfaces.

## Measured module imports

These are recorded Node.js probes. **Unprobed** means no conclusion, not absence. A successful import does not establish every operation of a module.

| Local Python lines | sqlite3 | zlib | bz2 | decimal | ssl | ctypes |
| --- | --- | --- | --- | --- | --- | --- |
| 2.7, 3.0–3.3 | Unprobed | Unprobed | Unprobed | Unprobed | Unprobed | Unprobed |
| 3.4–3.6 | No | No | No | Yes | No | No |
| 3.7–3.10 | No | No | No | No | No | No |
| 3.11–3.15 | Yes | Yes | Yes | Yes | No | No |

The older five profiles instead record successful `hashlib`, `time`, `re`, `json` and `math` probes and virtual file operations. Pyodide's bundled SQLite query and optional package behavior are covered by the [application evidence](validation.md), not the local-build import matrix.

## Language and configuration differences

| Surface | Observed distinction |
| --- | --- |
| Integer slash division | `7 / 2` produces `3` on 2.7 and `3.5` on Python 3 |
| Unicode representation | These 2.7–3.2 builds have narrow Unicode: one astral character has length two; 3.3 and later use length one |
| Target configuration | 3.0/3.1 lack `sysconfig`; 2.7 has minimal build variables; newer packaging supplies target metadata, with explicit browser checks for 3.11–3.15 |
| Pointer width | The inspected profiles report 32-bit pointers; these are not native host interpreters |

Python info reports missing facilities without stopping. Language features introduced after a selected release still fail normally; runtime selection does not translate newer Python syntax.

The exact values come from the [pinned builder audit](https://github.com/lewiscowles-netizen/python-wasm-builder/blob/ce8b58b131eec715ad7380688508c5bc9bf27905/docs/evidence/runtime-matrix.json), its family smoke records, and the [browser evidence reference](validation.md). The latter defines coverage and limitations. New artifacts require a new measured snapshot.
