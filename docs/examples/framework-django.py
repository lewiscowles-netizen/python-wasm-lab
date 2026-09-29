import asyncio, importlib.metadata, json, sys, types
import django
from django.conf import settings
print('IMPORT_OK Django')
print('VERSIONS', json.dumps({name: importlib.metadata.version(name) for name in ['Django', 'asgiref', 'sqlparse', 'micropip']}, sort_keys=True))
print('PYTHON', sys.version)
settings.configure(DEBUG=False, SECRET_KEY='local-probe-only', ALLOWED_HOSTS=['testserver'], ROOT_URLCONF='wasm_probe_urls', MIDDLEWARE=['django.middleware.csrf.CsrfViewMiddleware'], INSTALLED_APPS=[], DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}})
django.setup()
from django.http import JsonResponse
from django.urls import path
from django.middleware.csrf import get_token
from django.test import Client
from django.db import connection, models
module = types.ModuleType('wasm_probe_urls')
sys.modules['wasm_probe_urls'] = module
def csrf(request):
    return JsonResponse({'csrfToken':get_token(request)})
def hello(request):
    return JsonResponse({'message':'hello from Django', 'method':request.method})
def echo(request):
    return JsonResponse({'body':json.loads(request.body), 'method':request.method})
def cookie_set(request):
    response = JsonResponse({'saved':True})
    response.set_cookie('counter','42')
    return response
def cookie_read(request):
    return JsonResponse({'counter':request.COOKIES.get('counter')})
module.urlpatterns = [path('csrf',csrf), path('hello',hello), path('echo',echo), path('cookie/set',cookie_set), path('cookie/read',cookie_read)]
client = Client(enforce_csrf_checks=True)
token_response = client.get('/csrf')
token = json.loads(token_response.content)['csrfToken']
print('CSRF_SETUP',token_response.status_code,'csrftoken' in client.cookies)
for label, method, url, kwargs in [
    ('GET','get','/hello',{}),
    ('POST_NO_CSRF','post','/echo',{'data':{'hello':'wasm'},'content_type':'application/json'}),
    ('POST','post','/echo',{'data':{'hello':'wasm'},'content_type':'application/json','HTTP_X_CSRFTOKEN':token}),
    ('404','get','/missing',{}),
    ('COOKIE_SET','get','/cookie/set',{}),
    ('COOKIE_READ','get','/cookie/read',{}),
]:
    try:
        response = getattr(client,method)(url,**kwargs)
        content = json.loads(response.content) if response.headers.get('Content-Type','').startswith('application/json') else None
        print('RESPONSE', json.dumps({'case':label,'status':response.status_code,'json':content,'set_cookie':response.cookies.output()},sort_keys=True))
    except Exception as error:
        print('REQUEST_ERROR',json.dumps({'case':label,'type':type(error).__name__,'message':str(error)},sort_keys=True))
try:
    loop = asyncio.get_running_loop()
    print('ASYNC_CONTEXT',type(loop).__name__)
except RuntimeError:
    print('ASYNC_CONTEXT none')
class Note(models.Model):
    text = models.CharField(max_length=100)
    class Meta:
        app_label = 'wasm_probe'
try:
    with connection.schema_editor() as editor:
        editor.create_model(Note)
    Note.objects.create(text='SQLite ORM in Django')
    print('ORM_OK',json.dumps(list(Note.objects.values_list('text',flat=True))))
except Exception as error:
    print('ORM_ERROR',json.dumps({'type':type(error).__name__,'message':str(error)},sort_keys=True))
try:
    from asgiref.sync import sync_to_async
    result = await sync_to_async(lambda: 42)()
    print('SYNC_TO_ASYNC_OK',result)
except Exception as error:
    print('SYNC_TO_ASYNC_ERROR',json.dumps({'type':type(error).__name__,'message':str(error)},sort_keys=True))
def orm_work():
    with connection.schema_editor() as editor:
        editor.create_model(Note)
    Note.objects.create(text='SQLite ORM through sync_to_async')
    return list(Note.objects.values_list('text',flat=True))
try:
    print('ORM_VIA_SYNC_TO_ASYNC_OK',json.dumps(await sync_to_async(orm_work)()))
    print('ASYNC_ORM_COUNT_OK',await Note.objects.acount())
except Exception as error:
    print('ORM_VIA_SYNC_TO_ASYNC_ERROR',json.dumps({'type':type(error).__name__,'message':str(error)},sort_keys=True))
try:
    import threading
    values=[]
    thread=threading.Thread(target=lambda: values.append(42))
    thread.start()
    thread.join(timeout=0.1)
    print('THREAD_PROBE',json.dumps({'alive':thread.is_alive(),'values':values}))
except Exception as error:
    print('THREAD_ERROR',json.dumps({'type':type(error).__name__,'message':str(error)},sort_keys=True))
print('PROBE_DONE Django')
