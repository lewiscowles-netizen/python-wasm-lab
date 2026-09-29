import json
from js import AbortSignal
from pyodide.http import AbortError, pyfetch

SERVICE_URL = "http://127.0.0.1:8132"


class ServiceError(Exception):
    def __init__(self, status, payload, request_id):
        self.status = status
        self.payload = payload
        self.request_id = request_id
        super().__init__("HTTP %s: %s (request %s)" % (status, payload, request_id))


async def request(path, payload=None, timeout_ms=5000):
    signal = AbortSignal.timeout(timeout_ms)
    options = {
        "method": "GET" if payload is None else "POST",
        "credentials": "omit",
        "redirect": "error",
        "signal": signal,
    }
    if payload is not None:
        options["headers"] = {"Content-Type": "application/json"}
        options["body"] = json.dumps(payload)
    try:
        response = await pyfetch(SERVICE_URL + path, **options)
        body = await response.json()
    except AbortError as error:
        if signal.aborted and signal.reason.name == "TimeoutError":
            raise TimeoutError("Service request deadline expired") from error
        raise
    request_id = response.headers.get("x-request-id")
    if not response.ok:
        raise ServiceError(response.status, body, request_id)
    return {"status": response.status, "body": body, "request_id": request_id}


stock = await request("/stock/widget")
assert stock["body"]["available"] == 7
print("stock:", json.dumps(stock, sort_keys=True))
quote = await request("/quote", {"sku": "widget", "quantity": 2})
assert quote["body"]["total_cents"] == 250
print("quote:", json.dumps(quote, sort_keys=True))

for path, payload, expected in [
    ("/missing", None, 404),
    ("/quote", {"sku": "widget", "quantity": 0}, 422),
]:
    try:
        await request(path, payload)
    except ServiceError as error:
        assert error.status == expected
        print("expected_error:", error)
    else:
        raise AssertionError("Expected HTTP %s" % expected)

try:
    await request("/slow", timeout_ms=50)
except TimeoutError as error:
    print("expected_timeout:", error)
else:
    raise AssertionError("Expected service timeout")
