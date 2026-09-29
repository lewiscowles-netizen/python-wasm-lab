# Proposed browser application bridge

This reference defines a candidate interface for a navigable framework playground. It is **not the current worker protocol**. The current lab has a one-shot [script interface](../../experiments/wasm/python/README.md); the [architecture explanation](../explanation/framework-playgrounds.md) describes why a resident application needs more.

## Lifecycle and messages

| Message | Proposed responsibility |
| --- | --- |
| `start` | Load the pinned runtime, stage the project, initialize the application and its data; reply `ready` only after startup |
| `request` | Carry `appId`, unique request ID, method, URL, ordered header pairs and body bytes |
| `response` | Match the request ID; carry status, ordered header pairs and body bytes |
| `cancel` | Signal a disconnected caller; apply the adapter's cancellation policy |
| `stop` | Stop accepting requests, attempt application shutdown, then dispose of the worker |
| `reset` | Recreate application state from a declared fixture or saved snapshot |

The initial profile would serialize buffered requests through one interpreter. Define request, response, queue and time limits separately from the script runner's output limits. Keep logs outside response bodies. Worker termination can stop a stuck synchronous call, but loses that interpreter's state and pending requests; it cannot guarantee shutdown hooks ran.

## Gateway mappings

| Interface | Request mapping | Response mapping |
| --- | --- | --- |
| [WSGI](https://peps.python.org/pep-3333/) | `REQUEST_METHOD`, `SCRIPT_NAME`, `PATH_INFO`, `QUERY_STRING`, scheme, server fields, translated headers and `wsgi.input` byte stream | Capture `start_response`, consume the byte iterable and close it |
| [ASGI](https://asgi.readthedocs.io/en/latest/specs/www.html) | HTTP scope including path, raw path, query bytes, `root_path` and byte headers; `http.request` body events | Capture `http.response.start` and body events; model completion and disconnect |

Application startup/shutdown through ASGI lifespan is distinct from an HTTP request. Preserve repeated response headers, especially `Set-Cookie`; preserve binary bodies, including PUT/PATCH requests, and status-specific empty-body rules. Forward the visible host, scheme and mount prefix consistently so redirects, generated links and origin checks agree.

## Browser routing and state

| Concern | Required behavior |
| --- | --- |
| Service-worker scope | Intercept only the chosen virtual application routes; leave runtime/control assets and unrelated requests outside that routing rule |
| Activation | Wait until the application iframe is controlled before its first virtual navigation; recover if the owning page or worker disappears |
| Message routing | Associate the caller and request with the correct application instance; path prefixes alone do not isolate browser origins |
| Static files | Route collected framework assets with correct media types, or serve them from a distinct static prefix |
| Cookies | Maintain a scoped virtual cookie jar and define how browser JavaScript sees non-HttpOnly cookies; do not assume a synthetic `Set-Cookie` updates the browser jar |
| State | Keep the database and uploads across requests; define explicit export/import or persistent-storage synchronization |

Framework session, redirect and cross-site request forgery (CSRF) tests must cover this adapter, beyond test-client behavior. Browser [cookie restrictions](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie) still apply.

WebSockets, streaming responses and concurrent execution are outside the initial buffered profile. They require separate messages, backpressure, disconnect handling and framework-specific checks. Outbound service mocks are an independent dependency of the application; the inbound bridge does not replace them.
