# Run the lab locally

Use Python 3 and a current browser. To run the local CPython interpreters, first obtain completed builds in the adjacent `../python-wasm-builder` checkout; follow [Rebuild the interpreters](rebuild.md) if they are missing.

## Import completed builds

From the lab repository root, run:

```sh
python3 scripts/import-runtimes.py
```

The importer delegates validation and copying to the builder's exporter. Check that it reports 17 imported builds if you intend to use the complete [runtime set](../reference/runtimes.md). It imports the completed directories it finds; it does not compile missing interpreters.

For a builder stored elsewhere, supply its path:

```sh
python3 scripts/import-runtimes.py --builder /path/to/python-wasm-builder
```

## Start the server

```sh
python3 serve.py
```

Open [the local playground](http://127.0.0.1:8129/experiments/wasm/python/), choose a runtime and example, and press **Run Python**. See the [playground reference](../../experiments/wasm/python/README.md) for selector ordering and its stable-version default, or follow the [guided experiments](../../experiments/wasm/python/LAB-NOTES.md).

Keep the server terminal open while using the lab. Press Ctrl+C there when finished. This is an ordinary static web server: Python execution happens in the browser. No artificial intelligence service, assistant session, account or JavaScript dependency installation is required to use it.

If port 8129 is occupied, start another instance on a free port:

```sh
python3 serve.py --port 8130
```

Then open `http://127.0.0.1:8130/experiments/wasm/python/`. The launcher serves its own repository directory even when invoked by an absolute path from another working directory.

## Run without imported builds

On a fresh clone, skip the import and start the server. Choose the Pyodide comparison from the tracked baseline catalog. Running it downloads the interpreter from a content delivery network, so internet access is required. For local CPython, import its completed bundles and refresh the page. Follow [closed-network deployment](deploy-offline.md) when internet access is unavailable.

## Resolve startup problems

- If the exporter is missing, correct `--builder`; if no completed builds are found, rebuild them first.
- If a runtime asset returns a missing-file response, re-import the complete bundle rather than copying an individual binary. Check the [artifact reference](../reference/artifacts.md).
- If the catalog does not load, use the served web address rather than opening `index.html` directly from disk.
