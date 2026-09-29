# Playground interface reference

The playground accepts Python source and a runtime descriptor, executes one script, and displays the selected interpreter's output. [Run the lab](../../../docs/how-to/run-lab.md) for setup; follow the [guided tutorial](LAB-NOTES.md) for a first experiment.

## Controls

| Control | Contract |
| --- | --- |
| Python build | Local CPython entries in numeric version order, followed by Pyodide in its own group |
| Initial selection | Newest available stable local CPython, otherwise newest local prerelease, otherwise Pyodide; no selection is saved across page loads |
| Time limit | 10, 30 or 120 seconds; default 30; includes download, initialization and execution |
| Example | Replaces editor contents; Python info and Datasette source are fetched from `examples/` |
| Run Python | Starts a new worker; Control/Command + Enter is the equivalent shortcut |
| Stop | Terminates the worker; the editor remains available for another run |
| Package options | Enabled only for Pyodide; both begin unchecked and reset on runtime selection |
| Package requirements | One requirement per line, installed before source execution when micropip is enabled |

The version range, prerelease status and measured capabilities have one home in the [runtime reference](../../../docs/reference/runtimes.md). The [package explanation](../../../docs/explanation/packages-and-applications.md) defines what the two package controls enable.

## Results

The page displays the actual `sys.version` and `sys.platform`, separate standard output and standard error, elapsed time, and completion status. Successful execution reports exit code zero. A bare-CPython exception reports nonzero exit status; a Pyodide exception reports execution failure. Output is rendered as text. Its combined stream budget is 1,000,000 bytes in the UTF-8 (8-bit Unicode Transformation Format) encoding.

Bare loaders provide line-oriented callbacks. Pyodide uses stream writers and flushes both streams before termination, preserving partial output. The bare adapter captures `quit` as well as exit callbacks because older loaders can otherwise hide the command-line exit status.

Input immediately reaches end-of-file. Each run discards the previous interpreter, variables, installed packages and in-memory files. Python info probes interpreter properties and selected imports; unavailable historical build metadata appears explicitly. It does not dump environment variables or launch a native process.

## Worker protocol

The page sends `{type: 'run', runtime, code, options}`. `runtime.baseURL` supplies the catalog's page-relative address context; `options` contains `autoPackages`, `micropip` and the requirements array.

| Worker response type | Fields |
| --- | --- |
| `status` | `message` |
| `version` | `version`, `platform` |
| `output` | `stream` (`stdout` or `stderr`), `text` |
| `done` | `exitCode` |
| `error` | `message` |

The supported adapters are `emscripten` and `pyodide`. Other names fail explicitly. Catalogs, factories and bundle fields are specified in the [artifact reference](../../../docs/reference/artifacts.md). Worker lifetime and browser restrictions are explained in [architecture](../../../docs/explanation/architecture.md).

Source: [page controller](playground.mjs), [worker](worker.mjs) and [Python info](examples/python-info.py). The playground source was brought over from the user's website experiment; its [license](LICENSE) is preserved here. Runtime notices are distributed with each separate build.
