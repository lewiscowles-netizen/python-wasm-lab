import asyncio, json, traceback
from contextlib import asynccontextmanager
from importlib.metadata import version
import anyio, certifi, httpcore, httpx, idna, sniffio
from fastapi import Depends, FastAPI, Response
from pydantic import BaseModel, Field

lifecycle_events = []
mock_requests = []

async def mock_service(request):
    mock_requests.append({'method': request.method, 'url': str(request.url)})
    if request.method == 'GET' and str(request.url) == 'https://catalog.fixture.invalid/stock/widget':
        return httpx.Response(200, json={'sku': 'widget', 'available': 7})
    raise AssertionError('Unconfigured outbound request: ' + request.method + ' ' + str(request.url))

@asynccontextmanager
async def lifespan(app):
    lifecycle_events.append('startup')
    app.state.started = True
    async with httpx.AsyncClient(transport=httpx.MockTransport(mock_service), trust_env=False) as service_client:
        app.state.service_client = service_client
        yield
    app.state.started = False
    lifecycle_events.append('shutdown')

app = FastAPI(lifespan=lifespan)
app.state.started = False

class Item(BaseModel):
    name: str
    quantity: int = Field(gt=0)

@app.get('/hello/{name}')
async def hello(name: str, response: Response):
    response.headers['x-simulated-http'] = 'asgi'
    response.set_cookie('fixture', 'fastapi')
    return {'hello': name, 'started': app.state.started}

@app.post('/items', status_code=201)
async def create_item(item: Item):
    return item.model_dump()

async def get_service_client():
    return app.state.service_client

@app.get('/stock/{sku}')
async def stock(sku: str, service: httpx.AsyncClient = Depends(get_service_client)):
    response = await service.get('https://catalog.fixture.invalid/stock/' + sku)
    response.raise_for_status()
    return {'source': 'mock-service', 'stock': response.json()}

@app.get('/sync')
def sync_route():
    return {'sync': 'ran'}

result = {'versions': {name: version(name) for name in ('fastapi', 'starlette', 'anyio', 'httpx', 'httpcore', 'pydantic', 'pydantic-core', 'annotated-doc', 'annotated-types', 'typing-extensions', 'typing-inspection', 'sniffio', 'idna', 'certifi', 'h11', 'jinja2', 'markupsafe')}, 'http': []}

async def capture(client, method, path, **kwargs):
    response = await client.request(method, path, **kwargs)
    item = {'method': method, 'path': path, 'status': response.status_code, 'json': response.json(), 'headers': dict(response.headers)}
    result['http'].append(item)
    return response

transport = httpx.ASGITransport(app=app)
async with httpx.AsyncClient(transport=transport, base_url='http://in-process.invalid', trust_env=False) as client:
    initial = await capture(client, 'GET', '/hello/BeforeStartup')
    assert initial.status_code == 200
    assert initial.json()['started'] is False
    assert lifecycle_events == []
    result['transportStartsLifespan'] = False

    incoming = asyncio.Queue()
    outgoing = asyncio.Queue()
    task = asyncio.create_task(app({'type': 'lifespan', 'asgi': {'version': '3.0', 'spec_version': '2.0'}, 'state': {}}, incoming.get, outgoing.put))
    await incoming.put({'type': 'lifespan.startup'})
    startup_message = await asyncio.wait_for(outgoing.get(), timeout=5)
    assert startup_message == {'type': 'lifespan.startup.complete'}
    result['lifespanStartup'] = startup_message
    try:
        greeting = await capture(client, 'GET', '/hello/Ada')
        assert greeting.status_code == 200
        assert greeting.json() == {'hello': 'Ada', 'started': True}
        assert greeting.headers['x-simulated-http'] == 'asgi'
        assert greeting.cookies['fixture'] == 'fastapi'
        created = await capture(client, 'POST', '/items', json={'name': 'widget', 'quantity': 3})
        assert created.status_code == 201
        assert created.json() == {'name': 'widget', 'quantity': 3}
        invalid = await capture(client, 'POST', '/items', json={'name': 'widget', 'quantity': 0})
        assert invalid.status_code == 422
        assert invalid.json()['detail'][0]['loc'] == ['body', 'quantity']
        missing = await capture(client, 'GET', '/missing')
        assert missing.status_code == 404
        assert missing.json() == {'detail': 'Not Found'}
        mocked = await capture(client, 'GET', '/stock/widget')
        assert mocked.status_code == 200
        assert mocked.json() == {'source': 'mock-service', 'stock': {'sku': 'widget', 'available': 7}}
        try:
            await client.get('/stock/not-configured')
        except AssertionError as error:
            result['unknownOutbound'] = {'blocked': True, 'message': str(error)}
        else:
            raise AssertionError('Unknown outbound destination was not blocked')
        assert mock_requests == [
            {'method': 'GET', 'url': 'https://catalog.fixture.invalid/stock/widget'},
            {'method': 'GET', 'url': 'https://catalog.fixture.invalid/stock/not-configured'},
        ]
        result['mockOutboundRequests'] = mock_requests
        try:
            response = await asyncio.wait_for(client.get('/sync'), timeout=3)
            result['syncRoute'] = {'completed': True, 'status': response.status_code, 'body': response.text}
        except Exception as error:
            result['syncRoute'] = {'completed': False, 'type': type(error).__name__, 'message': str(error), 'traceback': traceback.format_exc()}
    finally:
        await incoming.put({'type': 'lifespan.shutdown'})
        shutdown_message = await asyncio.wait_for(outgoing.get(), timeout=5)
        assert shutdown_message == {'type': 'lifespan.shutdown.complete'}
        await task
        result['lifespanShutdown'] = shutdown_message

assert lifecycle_events == ['startup', 'shutdown']
assert app.state.started is False
result['lifecycleEvents'] = lifecycle_events
print('__FASTAPI_PROBE_RESULT__' + json.dumps(result))
