# Why package loading is only part of an application

A package switch changes which compatible code gets loaded. It does not change how the interpreter was compiled or which services its host supplies. The [runtime reference](../reference/runtimes.md) owns exact versions and measured modules; the [artifact contract](../reference/artifacts.md) owns the bundle interface.

## Build choices and loading choices

A compiled extension needs its native dependencies and compatible runtime support. A checkbox cannot add an omitted SQLite library, enable dynamic linking or supply operating-system processes. Python's own [platform documentation](https://docs.python.org/3/library/intro.html#webassembly-platforms) distinguishes import availability from operations that actually work.

[pip](https://pip.pypa.io/en/stable/cli/pip_install/) installs Python packages and can invoke package builds; it does not provide a WebAssembly (Wasm) port of their native dependencies. Merely installing pip does not recreate a desktop environment. In Pyodide, micropip installs compatible pure Python wheels and supported Wasm wheels. Pure Python still needs compatible syntax, dependencies and host facilities. Native wheels must match the interpreter and application binary interface (ABI), including Emscripten platform and linker choices. A desktop wheel, or another Wasm build sharing the Python version, is not sufficient evidence of compatibility. [Package loading](https://pyodide.org/en/stable/usage/loading-packages.html), [Emscripten packaging specification](https://peps.python.org/pep-0783/).

The [worker](../../experiments/wasm/python/worker.mjs) implements two independent Pyodide options: automatic import loading calls `loadPackagesFromImports`, while micropip loading can install explicit requirements. Automatic import loading searches the Pyodide distribution, not all package indexes. These controls are loading policy, not permissions: unchecked options do not block downloads initiated by application code or grant missing native capabilities. Bare CPython has no corresponding package integration in this adapter.

## What the Datasette example proves

The [example](../../experiments/wasm/python/examples/datasette.py) installs its [pinned requirements](../../experiments/wasm/python/examples/datasette-requirements.txt), creates a SQLite fixture, constructs Datasette with `num_sql_threads=0`, awaits `invoke_startup()`, then calls `ds.client.get(...)`. Disabling query threads avoids a thread pool in this browser profile; this setting is explicitly supported by [Datasette](https://docs.datasette.io/en/stable/settings.html#num-sql-threads).

Those calls exercise the application in-process through its Asynchronous Server Gateway Interface (ASGI), with no listening socket or server process, as shown by the [client implementation](https://github.com/simonw/datasette/blob/0.65.5/datasette/app.py#L1610). The recorded data, page and missing-route responses test more than imports. They establish one pinned application combination, not compatibility across the historical interpreter matrix.

[Datasette Lite](https://github.com/simonw/datasette-lite#how-this-works) adds a resident worker and a browser frontend. A comparable application needs navigation and request transport, asset handling, plugin assessment and an explicit state lifecycle. The lab displays response checks; it does not implement or validate that complete frontend. Its [execution lifecycle](architecture.md) is designed for isolated runs, so a resident application would need explicit state management.

## Deployment follows the required capabilities

Keeping dependencies local can remove startup downloads, but version pins alone neither vendor wheels nor prove offline operation. Remote wheels and datasets depend on browser fetch rules, including cross-origin resource sharing (CORS). Persistent data requires a storage integration and synchronization policy; virtual-file writes alone do not provide persistence. These are deployment decisions beyond selecting an installer.

The [guided examples](../../experiments/wasm/python/LAB-NOTES.md) provide the practical walkthrough. [Runtime alternatives](runtime-alternatives.md) explains which interpreter and host combinations can supply the underlying facilities.
