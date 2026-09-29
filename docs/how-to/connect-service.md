# Connect an application to an intranet service

First complete the [local-service tutorial](../tutorials/external-service.md). Use this guide when replacing its fixture with an existing service or a service you will deploy. The [host-boundary explanation](../explanation/host-services.md) describes the architectural trade-offs.

## Define a narrow contract

Choose one operation, such as looking up stock or calculating a quote. Specify method, path, request schema, successful response, errors, maximum body size and deadline. Add a request identifier to correlate browser and service logs. Decide whether retries are safe before enabling them.

Implement the service outside WebAssembly (Wasm) using your normal server stack. It can use Django, Flask or FastAPI natively even when parts of that stack cannot run in the browser. Test its contract directly, then adapt the [example client](../examples/external-service-client.py). Keep its request function injectable so your application can also use a fixture during tests.

## Choose the browser-facing address

Prefer an existing application gateway using secure Hypertext Transfer Protocol (HTTPS) when it can serve both the lab and a fixed service route. For example, add this location inside that gateway's Nginx `server` block:

```nginx
location /api/catalog/ {
    proxy_pass http://catalog.internal:8080/;
    proxy_connect_timeout 3s;
    proxy_read_timeout 10s;
    client_max_body_size 64k;
}
```

Replace the upstream with your service. The trailing slash maps `/api/catalog/stock/widget` to `/stock/widget`; see [Nginx proxy semantics](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_pass). This is a configuration fragment, not a tested complete deployment. Retain the gateway's authentication, transport security, logging and access rules; use verified HTTPS upstream transport where required. Validate configuration with `nginx -t` before your normal reload process.

Set the client to `SERVICE_URL = "/api/catalog"`. The browser contacts its own origin; the gateway contacts the backend. Restrict forwarding to intended services instead of accepting arbitrary destination URLs. The local tutorial service only listens on loopback and is not an intranet deployment server.

If the browser must contact a separate origin, configure that service's Cross-Origin Resource Sharing (CORS) policy for the exact lab origin, necessary methods and headers. Include permission headers on error responses. Check `OPTIONS` before investigating the application POST. Do not use `mode="no-cors"`; its opaque response cannot provide a readable application programming interface (API) result. [Fetch options](https://developer.mozilla.org/en-US/docs/Web/API/RequestInit).

## Connect identity deliberately

Keep privileged upstream credentials at the gateway. Apply user authentication and operation-level authorisation there. If your gateway uses browser session cookies, change the example's `credentials="omit"` to `"same-origin"` and include its required cross-site request forgery token for writes. Cross-origin credentials additionally require server permission and remain subject to browser cookie policy. Follow your identity system's contract rather than pasting private tokens into the editor.

## Verify from the actual browser

Run a valid request, invalid input, a missing record, denied access and an unavailable service. Inspect status, the JavaScript Object Notation (JSON) body and request identifier separately. Preserve developer-tools logs; a command-line success does not establish browser access.

Use the [intranet debugging guide](debug-intranet.md) for name resolution, certificates and content security policy. Also check browser local-network permissions: [Chrome 142 introduced a separate access prompt](https://developer.chrome.com/release-notes/142#local-network-access-restrictions). An old private-network header is not a universal fix.

Finally, [mirror runtime and package assets](deploy-offline.md), then verify application requests under the real network restrictions using the [egress checks](verify-no-egress.md). A reachable internal API cannot compensate for an interpreter still fetched from a public host.
