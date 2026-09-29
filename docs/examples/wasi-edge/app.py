"""WASI HTTP JSON application for the capability lab."""
import json
import sys

from componentize_py_types import Err, Ok
from wit_world import exports
from wit_world.imports.streams import StreamError_Closed
from wit_world.imports.types import Fields, IncomingBody, Method_Get, Method_Post, OutgoingBody, OutgoingResponse, ResponseOutparam

requests_in_instance = 0


def read_json(request):
    body = request.consume()
    chunks = []
    size = 0
    try:
        with body.stream() as stream:
            while True:
                try:
                    chunk = stream.blocking_read(4096)
                except Err as error:
                    if isinstance(error.value, StreamError_Closed):
                        break
                    raise
                size += len(chunk)
                if size > 4096:
                    raise OverflowError('Request body exceeds 4096 bytes')
                chunks.append(chunk)
    finally:
        with IncomingBody.finish(body):
            pass
    return json.loads(b''.join(chunks))


def route(request):
    method = request.method()
    request_path = (request.path_with_query() or '/').split('?', 1)[0]
    if isinstance(method, Method_Get) and request_path == '/info':
        return 200, {'python': sys.version.split()[0], 'platform': sys.platform, 'requests_in_instance': requests_in_instance}
    if isinstance(method, Method_Get) and request_path == '/data':
        try:
            with open('/data/message.txt', encoding='utf-8') as fixture:
                return 200, {'message': fixture.read().strip()}
        except OSError as error:
            return 403, {'error': 'filesystem_unavailable', 'exception': type(error).__name__, 'errno': error.errno}
    if isinstance(method, Method_Post) and request_path == '/quote':
        try:
            data = read_json(request)
        except OverflowError:
            return 413, {'error': 'body_size'}
        except (ValueError, UnicodeDecodeError):
            return 400, {'error': 'invalid_json'}
        if not isinstance(data, dict) or data.get('sku') != 'widget' or type(data.get('quantity')) is not int or not 1 <= data['quantity'] <= 7:
            return 422, {'error': 'invalid_quote'}
        return 200, {'sku': 'widget', 'quantity': data['quantity'], 'total_cents': 125 * data['quantity']}
    return 404, {'error': 'not_found'}


class IncomingHandler(exports.IncomingHandler):
    def handle(self, request, response_out):
        global requests_in_instance
        requests_in_instance += 1
        status, payload = route(request)
        encoded = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')
        response = OutgoingResponse(Fields.from_list([('content-type', b'application/json'), ('content-length', str(len(encoded)).encode('ascii'))]))
        response.set_status_code(status)
        body = response.body()
        ResponseOutparam.set(response_out, Ok(response))
        with body.write() as stream:
            stream.blocking_write_and_flush(encoded)
        OutgoingBody.finish(body, None)
