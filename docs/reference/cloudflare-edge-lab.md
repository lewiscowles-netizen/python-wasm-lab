# Cloudflare Python edge lab

This lab runs a Python Hypertext Transfer Protocol (HTTP) handler in local workerd, the Cloudflare Workers runtime. Cloudflare injects Pyodide into a V8 isolate; this example exports `Default.fetch(request)` through the Workers software development kit (SDK). It does not produce a WebAssembly System Interface (WASI) component or a `wasi:http` interface. See [how Python Workers work](https://developers.cloudflare.com/workers/languages/python/how-python-workers-work/).

## Prerequisites and inputs

The checked environment is macOS arm64. The checker uses POSIX process groups; Windows is unverified. Install Node 22 or newer, Yarn 1 and uv 0.12.3 or newer. Setup requires package-registry and runtime-download access; running the local example needs no account login. Follow the [tutorial](../tutorials/cloudflare-edge.md).

[pyproject.toml](../examples/cloudflare-edge/pyproject.toml) pins application and development packages. `uv.lock` locks host tools; `pylock.toml` locks vendored Worker wheels and their hashes; `yarn.lock` locks Wrangler and workerd. Generated environments, vendor modules and bundles are ignored.

[wrangler.toml](../examples/cloudflare-edge/wrangler.toml) selects compatibility date `2026-09-26` and `python_workers`, with one text binding, `LAB_MESSAGE`. The observed runtime is CPython 3.14.2 / Pyodide 314.0.6. Pywrangler's compatible wheel index is 314.0.7: the resolver's index version is not the injected runtime version. Changing tool pins or compatibility settings requires a new check.

## HTTP interface

| Method and path | Result |
|---|---|
| `GET /` | Runtime identifiers, binding value and process-local request counter |
| `GET /packages` | Installed versions, stemmer output and certificate resource size/count |
| `POST /stem` | JSON `words` string array → stems; invalid JSON or shape returns 400 |
| `GET /resources` | Thread-start result and `/tmp` file round-trip, including prior existence |
| Other routes | JSON 404 |

The handler is [src/entry.py](../examples/cloudflare-edge/src/entry.py). It makes no outbound application requests. Certifi is a package-resource probe, not configuration of the host's Transport Layer Security (TLS) trust store. Native Linux or macOS wheels are not interchangeable with PyEmscripten wheels; see [supported package surfaces](https://developers.cloudflare.com/workers/languages/python/packages/).

## Validation

[The evidence ledger](../evidence/cloudflare-edge-2026-09-29.json) records real HTTP results, versions, logs, source hashes and dry-run artifacts. [The checker](../../scripts/check-cloudflare-edge.py) replays them without a cloud deployment. Its default output is ignored `.local/check-result.json`; `--output` chooses another evidence file.

Local requests demonstrated package imports, bundled data access, input validation and errors. Thread creation failed. The counter and temporary file survived warm requests and reset after the local process restarted. These observations do not demonstrate isolate eviction, production quotas, cloud cold-start latency or durable storage.

## Platform constraints

As checked on 2026-09-29, Cloudflare documents 64 MiB uncompressed Worker size, no compressed-size limit, 128 MB memory per isolate including Wasm, and a one-second startup limit. Free and paid central processing unit (CPU) allowances differ. These are platform limits, not measurements enforced by this local test. See [Workers limits](https://developers.cloudflare.com/workers/platform/limits/).

Cloud deployment snapshots top-level Python initialization to reduce request-time startup. A local dry-run builds upload artifacts; it does not validate that deployment lifecycle. No external deployment was attempted. Application state that must survive eviction belongs in an explicit storage service, not this example's globals or temporary files.
