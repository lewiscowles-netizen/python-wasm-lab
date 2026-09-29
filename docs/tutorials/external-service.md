# Call your first real service from Python in WebAssembly

You will run a small service on your computer, call it from Python inside the browser, and inspect both ends of the connection. You need a terminal, native Python 3.9 or newer, and the [running lab](../how-to/run-lab.md). No artificial intelligence service or account is involved.

## Start the service

In a second terminal, from the repository root, run:

```sh
python3 docs/examples/external-service.py
```

Leave it running. Open this address in another browser tab:

```text
http://127.0.0.1:8132/health
```

You should see `{"ok": true}`. This Python process runs on your computer. The Python you will use next runs inside WebAssembly (Wasm).

## Make the browser call it

Open the playground at `http://127.0.0.1:8129/experiments/wasm/python/`. Use this exact host spelling for the tutorial. Select **Pyodide 314.0.7**, choose the 120-second time limit, turn off both package checkboxes and clear the requirements box.

Open [the client source](../examples/external-service-client.py), copy all its code into the editor, and run it. The printed records should include:

- `stock`: seven widgets available.
- `quote`: two widgets cost 250 cents.
- Two `expected_error` lines: Hypertext Transfer Protocol (HTTP) statuses 404 and 422.
- `expected_timeout`: the deliberately slow request exceeded its deadline.

The successful responses also contain a request identifier. The run should finish with exit code zero: the deliberate failures were handled and checked. Exact interfaces and limits live in the [service reference](../reference/external-service.md).

## Watch the connection

Open browser developer tools, select **Network**, clear its log, and run again. Filter by `8132`. Inspect `/stock/widget`, `/quote` and `/slow`; the service terminal also records requests.

For `/quote`, find the browser's `OPTIONS` permission check before its JavaScript Object Notation (JSON) `POST`. If it is absent, wait several seconds before repeating: clearing the log does not clear the browser's short preflight cache. Compare the request's `Origin` header with the service's `Access-Control-Allow-Origin` response. Inspect the 422 response body: a server error response is still readable when the origin is allowed. `/slow` should show a cancelled request.

## Change one input

Change the successful quote's quantity from `2` to `3` and its expected total from `250` to `375`. Run again and check both the printed result and network body. You have changed Python executing in the browser without restarting the service.

Now stop the service with Ctrl-C and run again. The client should fail on its first request; inspect the browser console for the connection error. Restart the service to restore the successful run.

## Continue the experiment

Read [why host services matter](../explanation/host-services.md), then [connect an intranet service](../how-to/connect-service.md). To repeat the experiment without public asset downloads, first prepare [self-hosted Pyodide](../how-to/deploy-offline.md). The tutorial's service is local; the default Pyodide catalog still downloads its interpreter.
