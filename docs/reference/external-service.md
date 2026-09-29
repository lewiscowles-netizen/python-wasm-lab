# External-service example reference

The [native service](../examples/external-service.py) and [browser client](../examples/external-service-client.py) demonstrate real Hypertext Transfer Protocol (HTTP) requests. They are stateless development fixtures, without authentication, persistent storage or production server hardening. Start with the [tutorial](../tutorials/external-service.md).

JSON below means JavaScript Object Notation; HTTPS means HTTP protected by Transport Layer Security (TLS).

## Execution and configuration

| Component | Interface |
| --- | --- |
| Service | Native Python 3.9+ standard library; binds `127.0.0.1` only |
| `--port` | Default `8132`; `0` requests an available port |
| `--allow-origin` | Default `http://127.0.0.1:8129`; one exact HTTP(S) origin, without trailing slash |
| Client | Pyodide 314.0.7; no optional packages required |
| `SERVICE_URL` | Default `http://127.0.0.1:8132`; base address without trailing slash |
| `request(path, payload=None, timeout_ms=5000)` | GET without payload; otherwise JSON POST; returns `status`, `body`, `request_id` |

The lab's bare CPython adapters do not expose `pyodide.http` or the JavaScript bridge. This example does not add network support to those interpreters.

## Service endpoints

Paths ignore query strings. Supported handlers return JSON, except an empty successful preflight. Other HTTP methods use the standard server's 501 response.

| Request | Response |
| --- | --- |
| `GET /health` | 200, `{"ok":true}` |
| `GET /stock/widget` | 200, `sku`, `available:7`, `unit_price_cents:125` |
| `POST /quote` with `{"sku":"widget","quantity":2}` | 200, `sku`, `quantity`, `total_cents:250`; no inventory mutation |
| `GET /slow` | Waits two seconds, then 200, `{"ok":true}` |
| Unknown GET/POST path | 404, `error:not_found` |

Quote quantity must be an integer from 1 to 7; booleans are rejected. Invalid fields produce 422, `invalid_quote`. Invalid JSON produces 400, `invalid_json`; unsupported content type produces 415, `json_required`. A positive `Content-Length` of at most 4096 bytes is required: missing/invalid length or transfer encoding produces 400, `content_length_required`; out-of-range length produces 413, `body_size`.

## Browser-origin contract

For an allowed origin, the service emits `Access-Control-Allow-Origin`, exposes `X-Request-ID`, and supports GET/POST preflights with `Content-Type`. It emits `Vary: Origin` and `Cache-Control: no-store`. A mismatched origin receives 403 without permission to read that response. Requests without `Origin` are accepted; this policy is not authentication.

`OPTIONS` rejects an unsupported requested method/header with 403; otherwise it returns 204. No credential permission is supplied. Cross-Origin Resource Sharing (CORS) governs browser access; see [the browser protocol](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS).

## Client failures

The client omits credentials, rejects redirects, consumes JSON once, and raises `ServiceError` for a readable non-success response. That exception retains status, body and request identifier. A non-JSON response fails during decoding instead.

The deadline uses [`AbortSignal.timeout`](https://developer.mozilla.org/en-US/docs/Web/API/AbortSignal/timeout_static), covering fetch and body reading in browser active time. The client translates an expired signal into `TimeoutError`. Pyodide's [`AbortError` wrapper](https://github.com/pyodide/pyodide/blob/314.0.7/src/py/pyodide/http/_pyfetch.py) also represents network/CORS failures; its name alone does not establish timeout. Cancellation does not roll back server work.

## Verification

[Recorded browser evidence](../evidence/external-service-2026-09-29.json) identifies the tested sources, runtime and cases. To repeat with a previously obtained Pyodide distribution and [installed browser-test prerequisites](../how-to/test.md):

```sh
node scripts/check-external-service.cjs --runtime-dir /absolute/path/to/pyodide
```

The checker starts temporary loopback servers and uses real browser networking. It does not download the distribution or establish firewall isolation. Raw results go to ignored `test-results/external-service.json`; `--output` changes that path, `--summary-output` writes a concise evidence record, and `--python` selects the native interpreter.
