# Framework request support reference

These are measured 2026-09-29 probes in the actual lab worker with Pyodide 314.0.7, its CPython 3.14.2 and Chromium 151.0.7922.34. They establish specific application requests, not complete framework compatibility or a browser-hosted website. [Replay the probes](../how-to/probe-frameworks.md).

## Observed request behavior

| Framework | Request boundary | Passed | Boundary encountered |
| --- | --- | --- | --- |
| Flask 3.1.3 | `app.test_client()` | GET, JSON POST, 404, signed session round-trip, SQLite query | Only synchronous views and built-in session behavior tested |
| Django 6.1.1 | `Client(enforce_csrf_checks=True)` with CSRF middleware | GET, JSON POST with token, 403 without token, 404, cookie round-trip | Object-relational mapper (ORM) schema creation raised `SynchronousOnlyOperation` |
| FastAPI 0.136.1 | HTTPX `AsyncClient` with `ASGITransport` | Async GET, POST 201, validation 422, 404, response headers/cookie, explicit lifespan startup/shutdown, mocked outbound service | Synchronous `def` route raised `RuntimeError: can't start new thread` |

Cross-site request forgery (CSRF) checks in the Django probe are enabled explicitly; framework test clients can otherwise relax checks. Cookie results above belong to in-process clients, not the browser cookie jar. Sources: [Flask testing](https://flask.palletsprojects.com/en/stable/testing/), [Django testing](https://docs.djangoproject.com/en/6.1/topics/testing/tools/), [FastAPI async testing](https://fastapi.tiangolo.com/advanced/async-tests/).

## Execution and dependency constraints

Flask and Django can expose a Web Server Gateway Interface (WSGI) application. FastAPI exposes an Asynchronous Server Gateway Interface (ASGI) application. A browser adapter would supply these protocols instead of running `flask run`, Django's `runserver`, Gunicorn or Uvicorn.

Flask's [async-view implementation](https://flask.palletsprojects.com/en/stable/async-await/) can start an event loop in a thread. The synchronous Flask probe does not establish support for that path.

Django's direct ORM call and its `sync_to_async` variant both failed in this worker. A trivial `sync_to_async(lambda: 42)` did return successfully: Pyodide's [WebLoop executor](https://github.com/pyodide/pyodide/blob/314.0.7/src/py/pyodide/webloop.py) executes the function on the same thread, so that result does not demonstrate thread support or escape Django's async context. No async-safety override was used. See [Django's async boundaries](https://docs.djangoproject.com/en/6.1/topics/async/).

FastAPI's probe used the distribution's matching Starlette, AnyIO, Pydantic and compiled `pydantic-core` wheels. It also used Pyodide's adapted HTTPX wheel; a matching version label on a different wheel does not establish equivalent behavior. Synchronous endpoints and dependencies can invoke [Starlette's thread pool](https://starlette.dev/threadpool/). The tested async path avoids that call, but other features may still need it.

HTTPX's transport did not run ASGI lifespan automatically. The probe separately sent startup and shutdown messages; skipping them leaves application resources uninitialized. [HTTPX lifecycle documentation](https://www.python-httpx.org/advanced/transports/#asgi-startup-and-shutdown).

## Evidence and scope

The [evidence record](../evidence/frameworks-2026-09-29.json) contains package identities, source hashes and observed responses. Flask and Django downloaded packages from public hosts. FastAPI used a local mirror: only loopback asset requests were observed, and its fixture service calls produced no browser requests. These are different deployment checks.

No Django admin/database workflow, real browser login, navigation bridge, persistent hosting, streaming, WebSocket session or production service integration was validated. No framework matrix was run across Python 2.7–3.15. Historical interpreters need their own compatible framework and dependency versions. The [proposed bridge reference](framework-bridge.md) defines the next interface, separately from these measured results.
