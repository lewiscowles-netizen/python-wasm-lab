# Exercise framework requests without a network server

Use the existing lab to test a framework application in-process before building a navigable frontend. These probes run real routing and response code. Their setup and expected boundaries are recorded in the [framework reference](../reference/framework-support.md).

## Replay a measured probe

[Start the lab](run-lab.md), select Pyodide 314.0.7 and choose the 120-second time limit. Open one of the source files below and paste its contents into the Python editor.

| Probe source | Package controls |
| --- | --- |
| [Flask](../examples/framework-flask.py) | Enable micropip, disable automatic import loading, and copy [these requirements](../examples/framework-flask-requirements.txt) into the requirements box |
| [Django](../examples/framework-django.py) | Enable micropip, disable automatic import loading, and copy [these requirements](../examples/framework-django-requirements.txt) into the requirements box |
| [FastAPI](../examples/framework-fastapi.py) | Enable automatic import loading; keep micropip off and the requirements box empty |

Run the script and compare each recorded case with the reference. A final exit code zero means the probe completed; Django and FastAPI deliberately catch and report some unsupported operations. Inspect those records rather than interpreting completion as universal compatibility.

The baseline Pyodide entry downloads assets. For a closed network, use a [self-hosted distribution and local wheels](deploy-offline.md). FastAPI's automatic imports use the pinned distribution package set; do not replace its adapted wheels with desktop packages of the same version.

## Substitute your application

First [stage your package and data](import-project.md). Replace the fixture application with your application factory or module and keep the request harness small.

For Flask, construct the application and use `app.test_client()`. For Django, configure your project's settings, run `django.setup()` and use `Client(enforce_csrf_checks=True)`. Keep the current ORM limitation visible; route-only success does not validate your database workflow.

For FastAPI, import your ASGI application and construct `httpx.ASGITransport(app=app)`. Use `httpx.AsyncClient` and `await client.get(...)` or `await client.post(...)`. Follow the probe's explicit lifespan exchange when your app allocates resources at startup. The ordinary synchronous test client can require threads; changing a route to `async def` does not fix synchronous dependencies or blocking libraries inside it.

Exercise a valid request, invalid input, a missing route, state across two requests and an application-specific failure. Assert status, headers and body independently. These clients do not open the virtual addresses in a browser.

## Replace outbound services with fixtures

In the FastAPI source, the injected `service_client` uses HTTPX `MockTransport`. It returns stock data for one exact method/address and raises for any unconfigured call. The application's `/stock/widget` route consumes that response normally. Replace its fixture with your service contract, including error responses and malformed data.

Pass this client into the application through its factory or dependency injection. A mock only affects calls that use that client; unrelated `requests`, socket or database calls are unchanged. Keep unknown destinations explicit failures so a missing fixture does not silently fall through to a real service.

To make a real browser request instead, complete the [external-service tutorial](../tutorials/external-service.md), then adapt its callable client at the same application boundary.

After the in-process checks pass, use the [browser-playground design](../explanation/framework-playgrounds.md) for links, forms and navigation. That step requires a resident worker and request bridge; these scripts alone do not install them.
