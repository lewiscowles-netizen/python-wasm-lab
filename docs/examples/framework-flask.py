import importlib.metadata, json, sqlite3, sys
from flask import Flask, jsonify, request, session
print('IMPORT_OK Flask')
print('VERSIONS', json.dumps({name: importlib.metadata.version(name) for name in ['Flask', 'Werkzeug', 'Jinja2', 'MarkupSafe', 'itsdangerous', 'click', 'blinker', 'micropip']}, sort_keys=True))
print('PYTHON', sys.version)
app = Flask('wasm_flask_probe', root_path='/tmp')
app.config.update(TESTING=True, SECRET_KEY='local-probe-only')
connection = sqlite3.connect(':memory:')
connection.execute('create table notes (text text)')
connection.execute('insert into notes values (?)', ('SQLite in Flask',))
@app.get('/hello')
def hello():
    return jsonify(message='hello from Flask', method=request.method)
@app.post('/echo')
def echo():
    return jsonify(body=request.get_json(), method=request.method)
@app.get('/cookie/set')
def cookie_set():
    session['counter'] = 42
    return jsonify(saved=True)
@app.get('/cookie/read')
def cookie_read():
    return jsonify(counter=session.get('counter'))
@app.get('/database')
def database():
    return jsonify(rows=[row[0] for row in connection.execute('select text from notes')])
client = app.test_client()
for label, response in [
    ('GET', client.get('/hello')),
    ('POST', client.post('/echo', json={'hello':'wasm'})),
    ('404', client.get('/missing')),
    ('COOKIE_SET', client.get('/cookie/set')),
    ('COOKIE_READ', client.get('/cookie/read')),
    ('SQLITE', client.get('/database')),
]:
    print('RESPONSE', json.dumps({'case':label, 'status':response.status_code, 'json':response.get_json(silent=True), 'set_cookie':response.headers.getlist('Set-Cookie')}, sort_keys=True))
print('SQLITE_VERSION', sqlite3.sqlite_version)
print('PROBE_DONE Flask')
