# Bring a larger Python project into the lab

Start with a callable part of your project and a deterministic input. Prove that slice in the target interpreter before adding its interface, plugins or external services. This guide uses the existing editor; it does not add an upload control or resident application server.

## Choose the integration boundary

Check the project's minimum Python version, standard-library imports, native extensions and operating-system dependencies against the [runtime reference](../reference/runtimes.md). Include optional dependencies and plugins used by your intended workflow.

| Project needs | First integration |
| --- | --- |
| Pure Python modules and local data | Package the source and fixtures; call a function from a short harness |
| Native extensions available in Pyodide | Use the matching Pyodide distribution and its packages |
| Native extensions absent from the selected runtime | Port/rebuild the extension and interpreter profile first |
| Web framework | Exercise its application in-process, following the [Datasette example](../../experiments/wasm/python/examples/datasette.py) |
| Processes, sockets or persistent services | Replace that boundary with a browser-compatible adapter or retain an intranet service |

See [package and application trade-offs](../explanation/packages-and-applications.md) before choosing between these paths.

## Stage a multi-file project for Pyodide

Create `myproject/lab_entry.py` with a `run()` function that reads a fixture, performs useful work and returns a printable result. Include `myproject/__init__.py` and the files that function needs.

From your project root, create an archive. The archive root must contain `myproject/` and `fixtures/`, without an extra enclosing directory:

```sh
python3 -m zipfile -c /tmp/myproject.zip myproject fixtures
```

Prepare a deployment directory using the [publishing guide](publish.md), then copy the archive:

```sh
mkdir -p "$publish_dir/experiments/wasm/python/apps/myproject"
cp /tmp/myproject.zip "$publish_dir/experiments/wasm/python/apps/myproject/app.zip"
```

Serve that deployment, select Pyodide and paste this bootstrap into the editor. Keep automatic package loading off; explicitly install any required dependencies before the final import.

```python
import os
import sys
from pyodide.http import pyfetch

response = await pyfetch("./apps/myproject/app.zip")
if not response.ok:
    raise RuntimeError("Project archive HTTP %s" % response.status)
await response.unpack_archive(format="zip", extract_dir="/app")
os.chdir("/app")
sys.path.insert(0, "/app")

from myproject.lab_entry import run
print(run())
```

Archive extraction does not install dependencies. For a packaged distribution, install its compatible wheel through micropip instead; use the [closed-network procedure](deploy-offline.md) when its dependencies must remain internal. Pyodide documents both [custom-code loading paths](https://pyodide.org/en/stable/usage/loading-custom-python-code.html).

## Adapt local CPython builds

The Pyodide bootstrap above does not run on the bare CPython adapters. For those builds, add project files to the builder's filesystem bundle, rebuild/export it, and put the virtual project directory on `sys.path`. The modern recipe uses Emscripten's `--preload-file /bundle@/`; follow the selected [family recipe](rebuild.md) for older versions. The current worker has no arbitrary host-directory mount or file-upload protocol.

## Validate application behavior

Check a representative successful operation, a handled failure, resource lookup and output serialization. For a web framework, test startup, a real request and shutdown in-process; opening a listening server is not the browser integration.

Each run loses files and state. A navigable application needs a resident worker, request/response messages, assets and explicit persistence. Those require application changes beyond this harness. Record the project revision, runtime identity, dependency artifacts and expected results, then [check external requests](verify-no-egress.md).
