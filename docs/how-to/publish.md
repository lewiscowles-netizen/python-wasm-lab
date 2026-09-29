# Publish a complete static lab

Prepare and verify a deployment directory before uploading it to your static host. A source push does not include the ignored local runtime catalog or compiled bundles; package those files separately when publishing CPython runtimes.

## Prepare the deployment directory

First [import the builds](run-lab.md#import-completed-builds) and [run browser acceptance](test.md). Keep the generated catalog with every matching bundle it names. Follow the [artifact reference](../reference/artifacts.md) for the required files and notices.

From the lab repository root, stage the active playground and its documentation in a new directory:

```sh
publish_dir=$(mktemp -d)
mkdir -p "$publish_dir/experiments/wasm"
cp -R experiments/wasm/python "$publish_dir/experiments/wasm/"
cp README.md AGENTS.md appendix.md "$publish_dir/"
cp -R docs "$publish_dir/"
mkdir -p "$publish_dir/scripts"
cp scripts/import-runtimes.py "$publish_dir/scripts/"
```

Copying the playground directory includes its ignored generated files when present. The extra source and convention files preserve documentation links. Check that the staged `runtimes.local.json` names only bundles included under its adjacent `builds/` directory. Retain each whole exported bundle, including its manifest and notices. Do not upload the entire research checkout, `.git`, `node_modules`, compiler source trees or test output.

If publishing only the baseline Pyodide comparison, omit the local catalog and local build directories together. Pyodide still downloads its runtime and optional packages from external hosts; this procedure does not make it offline.

## Verify the staged site

Serve the staged directory on an unused port:

```sh
python3 -m http.server 8131 --bind 127.0.0.1 --directory "$publish_dir"
```

Open `http://127.0.0.1:8131/experiments/wasm/python/`. Run a local interpreter and check its reported version, then check any Pyodide examples you intend to offer. Follow navigation links and include any additional documentation targets you retain.

## Configure the host and upload

Upload the staged directory through your host's deployment mechanism. Preserve the relative directory layout. If hosted beneath a prefix such as `/lab/`, the playground address becomes `/lab/experiments/wasm/python/`; keep its scripts, catalogs, examples and bundles under the same prefix.

Serve `.mjs` files with a JavaScript media type and `.wasm` files as `application/wasm`. Ensure missing asset requests return an error rather than an HTML fallback page. Keep the page and worker on the same origin; configure cross-origin resource sharing (CORS) for any intentionally separate runtime or package host.

Repeat the staged-site checks at the public address, including version reporting and asset loading. Do not infer deployment success from a Git push or from a working local server.
