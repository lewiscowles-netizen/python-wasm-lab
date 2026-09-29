# WASI edge lab reference

This lab packages a Python application using JavaScript Object Notation (JSON) as a WebAssembly System Interface (WASI) Hypertext Transfer Protocol (HTTP) component and tests directory access on native Wasmtime.

## Usage

From the repository root:

```sh
python3 scripts/check-wasi-edge.py --download
```

The [checker](../../scripts/check-wasi-edge.py) accepts:

| Option | Meaning |
|---|---|
| `--download` | Fetch missing pinned archives; every cached or downloaded archive is hash-checked |
| `--work-dir PATH` | Generated tools, bindings and artifacts; defaults to the example’s ignored `.build` directory |
| `--output PATH` | Full run evidence; defaults to ignored `test-results/wasi-edge.json` |
| `--summary-output PATH` | Optional curated evidence output |

## Prerequisites and inputs

The supplied native tool pins cover macOS arm64. The checker requires Python 3.12 or newer and does not install global tools. Internet access is needed only for missing downloads when requested.

[toolchain.lock.json](../examples/wasi-edge/toolchain.lock.json) owns the tool versions, download URLs, SHA-256 checksums, Wasm Interface Type (WIT) source commit and selected world. The handwritten application is [app.py](../examples/wasi-edge/app.py). The application uses the bundled Python standard library and generated interface bindings.

## HTTP interface

| Request | Result |
|---|---|
| `GET /info` | Python version, `wasi` platform and calls handled by this instance |
| `POST /quote` | JSON object with `sku: "widget"` and integer quantity 1–7; total is quantity × 125 cents |
| `GET /data` | Reads `/data/message.txt`; maps an operating-system error to JSON HTTP 403 |
| Other route | JSON HTTP 404 |

The quote handler returns 400 for malformed JSON, 413 above 4,096 body bytes and 422 for invalid fields. It does not negotiate request media types.

## Outputs

The work directory contains `app.wasm`, its extracted `app.wit`, `manifest.json`, a fixture directory, and `wasi-edge-app.tar`. The archive includes only the component and manifest. Generated tools, downloads and binaries are ignored by Git.

The tested component embeds CPython 3.14.0. It exports `wasi:http/incoming-handler@0.2.0`; the compiler’s runtime imports use WASI 0.2.9, including filesystem, sockets, command-line interface (CLI) and HTTP interfaces. The manifest records the complete interface list. The requested source world alone does not describe every runtime import.

## Constraints

Wasmtime owns the listening socket and supplies HTTP resources to the guest. `-Scli` enables the runtime’s additional WASI interfaces. Directory access is granted through `--dir HOST::/data`; this CLI grant is not asserted to be read-only. The probe tests filesystem access, not outbound-network denial or complete tenant isolation.

The checker sets `--max-instance-reuse-count 1` explicitly and verifies that two sequential requests each observe a fresh Python counter. This is a host lifecycle policy, not a universal component behavior.

This proof covers one Python build and one native host platform. It does not validate framework adapters, WASI 0.3, other hosts or identical component bytes across rebuilds. The package needs a compatible host; it contains no operating-system image or native runtime executable.

## Verification

The [2026-09-29 evidence](../evidence/wasi-edge-2026-09-29.json) records source and artifact hashes, exact commands, real HTTP validation and the same component with and without the directory grant. Checksum provenance is recorded in the lock; the source-archive checksum is an observed pin, not an upstream signature. Follow the [tutorial](../tutorials/wasi-edge.md) to reproduce the experiment.
