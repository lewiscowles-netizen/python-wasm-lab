# Debug a lab on an intranet

Start from a [prepared internal deployment](deploy-offline.md). Keep the failing input and identify the first failed request or execution phase before changing packages or rebuilding Python.

## Capture a cold failure

Open developer tools before loading the page. Use a fresh browser profile, disable its HTTP cache, and remove any existing service-worker registration for the deployment. Keep the Network log across navigation. Block external destinations while allowing the internal host; the browser's universal **Offline** switch would also block your intranet server.

Run the smallest example first, then the application. Record the full failing address, initiating script, status, response headers, console error, selected runtime and reported Python version. Save the worker's console or stack while it exists: completion, Stop and the time limit terminate it. For stepped debugging, use a temporary local harness without the page deadline; do not misdiagnose a paused worker's timeout as an interpreter failure.

## Follow the first broken layer

| Observation | Next check |
| --- | --- |
| Connection refused | Correct host/port and server listener; `serve.py` binds only to loopback |
| Name lookup or certificate failure | Internal name resolution and browser trust for the server's certificate chain |
| HTTP 200 with HTML for a runtime file | Authentication redirect or fallback route; inspect the body and final address |
| Missing catalog or asset | Case-sensitive paths, deployment prefix and complete matching bundle |
| Module or WebAssembly compilation fails | Correct media types, response bytes and browser policy; then compare artifact hashes |
| Package lookup contacts a public host | Find the initiating install call, missing dependency or external link in an index/lock file |
| Wheel rejected | Python version, platform and application binary interface (ABI) match; an available download can still be incompatible |
| Python import succeeds but operation fails | Missing host facility, resource file or application configuration; test that operation directly |
| Only a warm browser works | Missing deployment asset hidden by cache; repeat in a fresh profile |

Use the [network reference](../reference/network-dependencies.md) to map each phase to its owner. A manifest-loading warning and an interpreter failure are different observations.

## Inspect browser restrictions

Check content security policy (CSP) violations for script imports, workers, connections and WebAssembly compilation. WebAssembly may require `wasm-unsafe-eval`; some generated JavaScript also uses dynamic evaluation. Test the actual loader before selecting policy allowances. Do not assume that one policy works across all historical toolchains. Worker execution has its own policy context, controlled by the worker script's response. See [script policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/script-src) and [worker policy](https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API/Using_web_workers#content_security_policy).

For a separate internal asset or package host, check cross-origin resource sharing (CORS), credentials, redirects and mixed HTTP/HTTPS content. Prefer the same origin when feasible. A successful command-line download does not prove browser access: browser policy and authentication may differ. See [CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS).

## Isolate application behavior

Run Python info, then the first required import, then one operation with a local fixture. Print `sys.path`, `os.getcwd()` and expected resource paths when imports or data loading fail. Compare versions and files against the [runtime reference](../reference/runtimes.md). Missing native modules need a different build; retrying a package index cannot supply a host process or socket service.

Repeat with [external-request recording](verify-no-egress.md). Keep the source revision, hashes, browser version, request failures and smallest reproducer with the result. A page screenshot alone cannot establish that every required asset was local.
