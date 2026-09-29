# Python WebAssembly lab

Run and compare Python interpreters in a browser, from **CPython 2.7 through every 3.x minor up to 3.15**, alongside Pyodide. The lab is a static playground with a source editor, examples, Python diagnostics, separate output streams and runtime capability information.

The current verified set contains **17 source-built CPython runtimes**, ending at **3.15.0rc2**, plus **Pyodide 314.0.7 / CPython 3.14.2** as a separate comparison. Python 3.15.0rc2 is a release candidate. Local CPython versions appear in numeric order, separately from Pyodide; when available, **3.14.7** is the default newest stable build.

No AI service, account, API key or assistant session is required. No npm installation or frontend build is needed to use the playground. Python executes in your browser; the local Python server only serves static files.

## Quick start

You need Python 3, a current browser, and completed artifacts in the sibling `../python-wasm-builder` checkout to use the local CPython builds. From this repository's root:

```sh
python3 scripts/import-runtimes.py
python3 serve.py
```

Open **[http://127.0.0.1:8129/experiments/wasm/python/](http://127.0.0.1:8129/experiments/wasm/python/)**, choose a Python build and example, then press **Run Python**.

The importer uses the sibling builder by default. For a different checkout:

```sh
python3 scripts/import-runtimes.py --builder /path/to/python-wasm-builder
```

The server binds to `127.0.0.1` and serves this repository's root. To choose another port:

```sh
python3 serve.py --port 8130
```

Then visit the same `/experiments/wasm/python/` path on port 8130.

### Fresh clone or missing local builds

Generated runtime bundles and `experiments/wasm/python/runtimes.local.json` are ignored by Git. A fresh clone does **not** contain the 17 compiled interpreters. Import completed sibling-builder artifacts to add them to the selector.

You can also skip the import and run `python3 serve.py` immediately. The tracked catalog offers the pinned Pyodide comparison, which downloads its runtime from a CDN when run. Pyodide and package examples require internet access. Local CPython bundles can run without external downloads once all their files have been imported; there is no service-worker offline cache.

## What to try

| Example | What it shows |
| --- | --- |
| Version and arithmetic; Language differences | Actual interpreter versions and changes such as Python 2 versus Python 3 division |
| Python info | A `phpinfo()`-style report of the interpreter, ABI, pointer width, Unicode behavior, encodings, paths, modules and target build metadata |
| Standard library probe | Which imports are available in the selected build |
| SQLite application query | Table creation, inserts and queries on Pyodide and the local 3.11–3.15 builds |
| Errors and separate output streams | stdout, stderr and an intentional Python exception |
| Stop an infinite loop | Worker termination and the time limit |
| Pyodide package and browser examples | A pure Python wheel, compiled NumPy, JavaScript interoperability and asynchronous fetch |
| Datasette application | A pinned application making in-process JSON, HTML and missing-route requests on Pyodide |

**Python info** reports missing historical facilities explicitly instead of aborting. The modern local 3.11–3.15 builds include their target sysconfig metadata and report a four-byte pointer size. Its [portable source](experiments/wasm/python/examples/python-info.py) can also run with an ordinary Python interpreter.

See the [guided lab notes](experiments/wasm/python/LAB-NOTES.md) for exact examples, package versions, expected output and the limits of the recorded checks. The Datasette experiment is an application demonstration; it does not provide the full resident Datasette Lite frontend.

## Packages and execution limits

The local builds are bare CPython profiles. They do not include desktop pip, Pyodide's micropip installer, its JavaScript bridge or its wheel repository. Package controls are disabled for these runtimes. Available standard-library modules vary by build; an import alone does not prove that every operation is supported.

Pyodide offers two independent options, both off by default: **Enable micropip for this run** installs supplied requirements, while **Load known Pyodide packages named in imports** loads packages from the matching Pyodide distribution. These options can download from the CDN, PyPI and wheel hosts. Turning them off skips automatic installation; it does not block network requests made by code. Desktop native wheels do not become compatible just because a package installer is enabled.

Each run starts a **fresh worker**. Python variables, virtual files, in-memory databases and installed packages are discarded when it ends. Stop and the time limit terminate the worker, including an infinite Python loop. Standard input returns EOF. Ordinary operating-system processes, browser TCP sockets, threads and dynamic extension loading are not general capabilities of these profiles.

## Build ownership and evidence

The sibling [python-wasm-builder](https://github.com/lewiscowles-netizen/python-wasm-builder) repository owns CPython source pins, compatibility-family branches, Docker Buildx recipes, manifests and artifact validation. This repository owns the browser playground and retains the original research workspace.

To create missing artifacts, follow the [sibling builder instructions](../python-wasm-builder/README.md). Its coordinator can replay all locked families:

```sh
cd ../python-wasm-builder
python3 scripts/build-all.py --parallel 2
cd ../python-wasm-lab
python3 scripts/import-runtimes.py
```

Building requires Docker with Buildx and the recipe histories described in the builder documentation. Running already imported bundles does not require Docker.

The importer calls the builder's exporter to verify artifact hashes and the recorded interpreter version, copy the declared files and update the ignored local catalog. Keep each loader, Wasm binary, standard-library data file, manifest and notices together. Re-import after rebuilding. Changed runtime bytes need fresh browser validation; an old result is not evidence for a new build.

The [browser evidence ledger](experiments/wasm/python/browser-evidence.json) records the tested runtime hashes and checks. The sibling [measured runtime matrix](../python-wasm-builder/docs/RUNTIME-MATRIX.md) and [build architecture](../python-wasm-builder/docs/BUILD-ARCHITECTURE.md) explain source-build validation and reproducibility limits. These checks cover specific interpreter and application behavior, not the entire upstream CPython regression suite. The sibling documentation links assume the default adjacent checkout layout.

## Browser checks

The optional browser tests run independently of AI. Install the test tools once:

```sh
yarn install --frozen-lockfile --registry https://registry.npmjs.org
yarn playwright install chromium
```

Then run `yarn test:e2e` to check every imported local interpreter, version selection,
Python info, output, exceptions, files and stopping loops. CDN tests are opt-in:
`PYTHON_WASM_TEST_PYODIDE=1 yarn test:e2e`. Set `PYTHON_WASM_PORT=8130` when
another checkout already occupies the default port. These tools are only needed
for automated development checks.

On 29 September 2026, `PYTHON_WASM_PORT=8130 yarn test:e2e --reporter=line`
passed **27 tests** against this standalone checkout and all 17 imported builds.
The **five optional CDN tests were skipped** in that run. The separate historical
browser ledger records the earlier full Pyodide and Datasette checks.

## Project layout

| Path | Purpose |
| --- | --- |
| `experiments/wasm/python/` | Active static playground, runtime adapters, examples and browser evidence |
| `scripts/import-runtimes.py` | Import completed builds from the sibling builder |
| `serve.py` | Serve this repository locally |
| `tests/`, `playwright.config.cjs` | Browser acceptance checks and local server configuration |
| `research/` | Technical research, including the [Pyodide teardown and diagrams](research/pyodide-teardown.md) |
| `legacy/`, `transitional/`, `mid-modern/` | Preserved experiments, porting work and historical build logs |
| `initial-builder-staging/` | Earlier builder staging material |
| `cpython-modern/`, `pyenv/` and other source trees | Reference sources retained from the investigation |

The research directories remain as investigation history. Use the sibling builder's committed family recipes for supported replay, and the root quick start above for the active playground. The [playground README](experiments/wasm/python/README.md) documents its artifact contract, adapters and browser behavior in more detail.
