# Run a Python HTTP application as a WASI component

Build a Python application into a WebAssembly System Interface (WASI) component, serve JavaScript Object Notation (JSON) through a native host, then grant access to one directory. Start at the repository root on macOS arm64 with Python 3.12 or newer. The first step needs internet access for pinned tool downloads.

## Build and check the application

Run:

```sh
python3 scripts/check-wasi-edge.py --download
```

The checker verifies the [toolchain pins](../examples/wasi-edge/toolchain.lock.json), creates an isolated build environment, packages [app.py](../examples/wasi-edge/app.py), and runs native Wasmtime hosts on temporary loopback ports. It stops those hosts after checking the application. No application container is involved.

Expect `"passed": true`. The ignored `test-results/wasi-edge.json` records the commands and results. The generated component and package are under `docs/examples/wasi-edge/.build/`.

## Serve the component yourself

In the same terminal, start a host:

```sh
lab=docs/examples/wasi-edge
wasmtime="$lab/.build/wasmtime-v49.0.1-aarch64-macos/wasmtime"
"$wasmtime" serve -Scli --addr 127.0.0.1:8134 \
  --max-instance-reuse-count 1 "$lab/.build/app.wasm"
```

In another terminal, send real Hypertext Transfer Protocol (HTTP) requests:

```sh
curl --noproxy '*' http://127.0.0.1:8134/info
curl --noproxy '*' -H 'Content-Type: application/json' \
  --data '{"sku":"widget","quantity":2}' \
  http://127.0.0.1:8134/quote
curl --noproxy '*' -i http://127.0.0.1:8134/data
```

The quote totals 250 cents. `/data` returns 403 because the guest cannot open `/data/message.txt`. The fixture exists on the host, but this launch has not granted its directory to the component. The JSON response preserves the actual Python exception and WASI error number.

## Grant the directory

Stop Wasmtime with Ctrl-C. Restart it in the first terminal with one explicit directory mapping:

```sh
"$wasmtime" serve -Scli --addr 127.0.0.1:8134 \
  --max-instance-reuse-count 1 \
  --dir "$(pwd)/$lab/.build/fixture::/data" "$lab/.build/app.wasm"
```

Request `/data` again. It now returns `{"message":"explicit directory capability"}`. Both runs use the same component; the host configuration changes its filesystem access.

## Inspect the portable payload

```sh
tar -tf docs/examples/wasi-edge/.build/wasi-edge-app.tar
```

The archive contains `app.wasm` and `manifest.json`. The manifest records the component’s imports, exports and checksum. Deployment still needs a compatible WASI HTTP host supplying those interfaces. The fixture directory is supplied separately at runtime.

See the [lab reference](../reference/wasi-edge-lab.md) for the interface, generated files and precise limits of the recorded proof.
