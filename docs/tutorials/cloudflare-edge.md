# Run a Python Worker locally

This tutorial starts a small Hypertext Transfer Protocol (HTTP) service in Cloudflare's local runtime. You will exercise a Python handler, a bundled package and a package data file, then observe what happens when the process restarts. The [lab reference](../reference/cloudflare-edge-lab.md) defines the runtime, prerequisites and limits.

## Prepare the example

From this repository's root, install the pinned dependencies:

```sh
cd docs/examples/cloudflare-edge
yarn install --frozen-lockfile --registry https://registry.npmjs.org
uv sync --frozen
```

The first setup downloads Node packages, Python packages and a compatible WebAssembly Python runtime. Keep the generated directories local; the checked-in lockfiles describe what to restore.

Start the Worker:

```sh
uv run --frozen pywrangler dev --local --ip 127.0.0.1 --port 8791 --inspector-port 9236
```

Wait for the ready message. No Cloudflare account, Docker daemon or artificial intelligence service is needed for this local exercise.

## Send real HTTP requests

In another terminal:

```sh
curl --noproxy '*' http://127.0.0.1:8791/
curl --noproxy '*' http://127.0.0.1:8791/packages
curl --noproxy '*' -H 'Content-Type: application/json' \
  --data '{"words":["running","jumping"]}' \
  http://127.0.0.1:8791/stem
```

The first response identifies the runtime and reads a configured binding. The second executes an installed package and reads its bundled certificate resource. The POST response contains the stems `run` and `jump`: the Python handler has processed an HTTP request, not a framework test-client call.

Try a missing route and a malformed input shape:

```sh
curl --noproxy '*' -i http://127.0.0.1:8791/missing
curl --noproxy '*' -i -H 'Content-Type: application/json' \
  --data '{"words":42}' http://127.0.0.1:8791/stem
```

Compare the status codes with the [endpoint contract](../reference/cloudflare-edge-lab.md#http-interface).

## Observe lifetime

Request `/resources` twice. Compare `existed_before` in the two responses, and inspect the thread-start result. Request `/` again to see the increasing counter. Stop the server with Ctrl-C, restart it with the same command, and repeat the requests. Treat these observations as local process behavior; they do not establish cloud persistence guarantees.

## Replay the checks

Stop the manual server. From the repository root, run:

```sh
python3 scripts/check-cloudflare-edge.py
```

The checker starts its own server, exercises the routes, restarts it, creates a local dry-run bundle, and stops its processes. It writes `.local/check-result.json` inside the example. Use `--port` and `--inspector-port` if those ports are occupied. The [recorded validation](../reference/cloudflare-edge-lab.md#validation) states what this establishes.
