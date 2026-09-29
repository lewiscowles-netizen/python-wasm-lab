# Validation reference

This reference records observed results and what they establish. Run a new check using the [test guide](../how-to/test.md).

## Recorded browser runs

All dates are 2026-09-29. These are distinct suites, not counts to add together.

| Run | Passed | Skipped | Evidence |
| --- | ---: | ---: | --- |
| Standalone repository, full suite | 32 | 0 | [Report with source and artifact hashes](../evidence/browser-2026-09-29.json) |
| Standalone repository, local-only suite | 27 | 5 | Earlier console result; superseded by the full run above |
| Original website integration, full suite | 31 | 0 | [Historical ledger](../../experiments/wasm/python/browser-evidence.json) |

The standalone full run uses Playwright 1.62.1 with Chromium and takes 52.5 seconds. Its extra test checks selector grouping, numeric order, the stable default and Pyodide package controls. The report identifies the original source commit, executed command and every test result. Its local runtime file hashes match the imported bundles; all manifest-declared files were verified after the run.

Separate [network checks](network-dependencies.md#recorded-checks) record the scope and limits of execution with external HTTP requests blocked.

## History cleanup

The [2026-09-29 cleanup record](../evidence/history-cleanup-2026-09-29.json) maps original commits to their rewritten equivalents after removing the downloaded and generated material identified in the [provenance appendix](../../appendix.md). The original browser report retains its original commit identity. Its application source and runtime hashes still match after cleanup; this verification does not represent a new browser test run. The cleanup record also identifies the unchanged tip tree and checks that local files and dependency checkout heads were preserved.

## Checks by layer

| Layer | Established by the recorded checks |
| --- | --- |
| Build execution | Generated WebAssembly (Wasm) executes in Node.js and reports the expected version; this is distinct from the native build-tool Python |
| Every local browser runtime | Actual version/platform, arithmetic, Unicode source, future imports, JavaScript Object Notation (JSON), regular expressions, math, virtual files, separate streams and exception exit status |
| Modern configuration | Target build metadata and four-byte pointers on the selected 3.11–3.15 builds |
| Diagnostics | Python info on 2.7, 3.0, modern local builds and Pyodide |
| User controls | Missing local catalog fallback, version ordering, worker Stop, time limit and recovery |
| Pyodide applications | Pure Python wheel install/reset, compiled NumPy import/reset, browser/runtime output and pinned Datasette requests |

The [builder audit](https://github.com/lewiscowles-netizen/python-wasm-builder/blob/ce8b58b131eec715ad7380688508c5bc9bf27905/docs/evidence/runtime-matrix.json) connects source pins, file hashes and historical browser evidence for the [runtime matrix](runtimes.md). The build manifests retain `validation.browser: "pending"` because browser evidence is recorded separately after export; that field is not the current lab test verdict.

## Limits

These checks do not establish full CPython regression compatibility, every library operation, all browser engines, independent clean-build reproducibility, persistent storage, arbitrary native wheels or complete Datasette Lite behavior. An import test establishes an import, not all operations of that module. Cached downloads do not establish offline operation.

A compiler log is not proof that the generated interpreter runs. A Node.js pass is not a browser pass. A Python version string does not identify exact bytes. Old evidence must not be relabeled as a new result after rebuilding. Hashes identify content; they are not independent proof of trustworthy execution or a security audit.

The historical ledger keeps earlier failures and artifact revisions for diagnosis. Its old source hashes belong to the original website integration; use the standalone report for the current worker and examples.
