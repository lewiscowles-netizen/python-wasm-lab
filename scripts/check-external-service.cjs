#!/usr/bin/env node
const assert = require('node:assert/strict');
const { spawn, execFileSync } = require('node:child_process');
const crypto = require('node:crypto');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const { chromium } = require('@playwright/test');

const repository = path.resolve(__dirname, '..');
const arguments_ = process.argv.slice(2);
function argument(name, fallback) {
  const index = arguments_.indexOf(name);
  return index < 0 ? fallback : arguments_[index + 1];
}
if (arguments_.includes('--help') || !argument('--runtime-dir')) {
  console.log('Usage: node scripts/check-external-service.cjs --runtime-dir /path/to/pyodide-314.0.7 [--python python3] [--output /path/to/raw-evidence.json] [--summary-output /path/to/summary.json]\nThe runtime directory must contain the five pinned core files. No downloads are performed.\nDefault raw output: test-results/external-service.json. --summary-output optionally writes a curated summary.');
  process.exit(arguments_.includes('--help') ? 0 : 2);
}
const runtimeDirectory = path.resolve(argument('--runtime-dir'));
const output = path.resolve(argument('--output', path.join(repository, 'test-results/external-service.json')));
const python = argument('--python', 'python3');
const summaryOutput = argument('--summary-output') ? path.resolve(argument('--summary-output')) : null;
const runtimeHashes = {
  'pyodide.mjs': '6f1d60f7bf529beb300f0f47983c921d3982363640ba20af0e38efdddbc66109',
  'pyodide.asm.mjs': 'f7cdc8ece80678ceb712f8e65ebe6d3a83203a180c399865f49612a051693635',
  'pyodide.asm.wasm': 'cc36e3cab04fdfc9a63ff13eb52eae2b911bf46c025cc7b281f394bd3de1d5e6',
  'python_stdlib.zip': 'fa1957e5777068fc4f7437f96d860ae2fbe9c19732ba06c84e004ec16dd7dd7a',
  'pyodide-lock.json': '5dc2fc119108bc148c7457dc86e7675b5c87e1cafd420b9c34c1eaef7b36c010',
};
const sourcePaths = {
  worker: 'experiments/wasm/python/worker.mjs',
  service: 'docs/examples/external-service.py',
  client: 'docs/examples/external-service-client.py',
  harness: 'scripts/check-external-service.cjs',
};
const digest = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const sources = Object.fromEntries(Object.entries(sourcePaths).map(([name, relative]) => [name, fs.readFileSync(path.join(repository, relative))]));
const evidence = {
  schemaVersion: 1,
  checkedAt: new Date().toISOString(),
  method: 'Real Chromium worker Fetch requests to an unmodified native Python HTTP service; no request routing, fulfillment, CORS bypass, service worker, or package download during verification.',
  scope: 'Observed requests from these fresh browser contexts were loopback-only. This is an observation of this run, not a firewall or arbitrary-code isolation claim.',
  sources: Object.fromEntries(Object.entries(sourcePaths).map(([name, relative]) => [name, { path: relative, sha256: digest(sources[name]) }])),
  runtime: { distribution: '314.0.7', expectedPython: '3.14.2', hashProvenance: 'Hashes observed in prior downloads from the recorded pinned CDN URLs, not an upstream signature or signed manifest; this run only verifies existing local files.', assets: [] },
  scenarios: [],
  serviceLog: [],
  staticServerRequests: [],
  nativeValidation: [],
};
const servers = [];
let browser;
let service;
let serviceOutput = '';
let serviceOrigin;

async function startLab(label) {
  const server = http.createServer((request, response) => {
    const pathname = new URL(request.url, 'http://localhost').pathname;
    evidence.staticServerRequests.push({ label, method: request.method, path: pathname });
    let bytes, mime;
    if (pathname === '/') {
      bytes = Buffer.from('<!doctype html><meta charset="utf-8"><title>External service verification</title><link rel="icon" href="data:,">');
      mime = 'text/html';
    } else if (pathname === '/worker.mjs') {
      bytes = sources.worker;
      mime = 'text/javascript';
    } else if (pathname.startsWith('/runtime/') && Object.hasOwn(runtimeHashes, pathname.slice('/runtime/'.length))) {
      const filename = pathname.slice('/runtime/'.length);
      bytes = fs.readFileSync(path.join(runtimeDirectory, filename));
      mime = filename.endsWith('.mjs') ? 'text/javascript' : filename.endsWith('.wasm') ? 'application/wasm' : filename.endsWith('.json') ? 'application/json' : 'application/zip';
    } else {
      response.writeHead(404);
      response.end('missing');
      return;
    }
    response.writeHead(200, { 'Content-Type': mime, 'Content-Length': bytes.length, 'Cache-Control': 'no-store' });
    response.end(bytes);
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  servers.push(server);
  return `http://127.0.0.1:${server.address().port}`;
}

async function startService(allowedOrigin) {
  service = spawn(python, ['-u', path.join(repository, sourcePaths.service), '--port', '0', '--allow-origin', allowedOrigin], { stdio: ['ignore', 'pipe', 'pipe'] });
  let stderr = '';
  service.stderr.on('data', bytes => {
    stderr += bytes.toString();
    const lines = stderr.split('\n');
    stderr = lines.pop();
    evidence.serviceLog.push(...lines.filter(Boolean));
  });
  return await new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error('Service did not announce its ephemeral port')), 10000);
    service.once('error', error => { clearTimeout(timeout); reject(error); });
    service.once('exit', code => { clearTimeout(timeout); reject(new Error(`Service exited before startup: ${code}`)); });
    service.stdout.on('data', bytes => {
      serviceOutput += bytes.toString();
      const match = serviceOutput.match(/External service: (http:\/\/127\.0\.0\.1:\d+) /);
      if (match) { clearTimeout(timeout); resolve(match[1]); }
    });
  });
}

async function stopService() {
  if (!service || service.exitCode !== null || service.signalCode !== null) return;
  await new Promise(resolve => { service.once('exit', resolve); service.kill('SIGTERM'); });
}

async function runWorker(name, origin, code) {
  const scenario = { name, origin, sourceSHA256: digest(Buffer.from(code)), expectedBrowserFailure: name === 'documented-client' ? 'The slow request is aborted by its 50 ms deadline.' : name === 'rejected-origin' ? 'CORS blocks a GET response and rejects the POST preflight.' : 'The stopped service refuses the connection.', requests: [], responses: [], failedRequests: [], console: [], pageErrors: [] };
  evidence.scenarios.push(scenario);
  const context = await browser.newContext({ serviceWorkers: 'block' });
  context.on('request', request => scenario.requests.push({ method: request.method(), url: request.url(), resourceType: request.resourceType(), originHeader: request.headers().origin ?? null, contentType: request.headers()['content-type'] ?? null }));
  context.on('response', response => scenario.responses.push({ method: response.request().method(), url: response.url(), status: response.status(), corsAllowOrigin: response.headers()['access-control-allow-origin'] ?? null, corsExposeHeaders: response.headers()['access-control-expose-headers'] ?? null, requestID: response.headers()['x-request-id'] ?? null }));
  context.on('requestfailed', request => scenario.failedRequests.push({ method: request.method(), url: request.url(), failure: request.failure() }));
  try {
    const page = await context.newPage();
    page.on('console', message => scenario.console.push({ type: message.type(), text: message.text() }));
    page.on('pageerror', error => scenario.pageErrors.push(error.message));
    await page.goto(origin);
    scenario.messages = await page.evaluate(({ origin, code }) => new Promise((resolve, reject) => {
      const worker = new Worker(`${origin}/worker.mjs`, { type: 'module' });
      const messages = [];
      const timeout = setTimeout(() => { worker.terminate(); reject(new Error('Worker exceeded 60 seconds')); }, 60000);
      worker.onmessage = ({ data }) => {
        messages.push(data);
        if (data.type === 'done' || data.type === 'error') {
          clearTimeout(timeout);
          worker.terminate();
          resolve(messages);
        }
      };
      worker.onerror = event => { clearTimeout(timeout); worker.terminate(); reject(new Error(event.message)); };
      worker.postMessage({ type: 'run', runtime: { adapter: 'pyodide', module: './runtime/pyodide.mjs', baseURL: `${origin}/` }, code, options: { autoPackages: false, micropip: false, packages: [] } });
    }), { origin, code });
    scenario.stdout = scenario.messages.filter(message => message.type === 'output' && message.stream === 'stdout').map(message => message.text).join('');
    scenario.stderr = scenario.messages.filter(message => message.type === 'output' && message.stream === 'stderr').map(message => message.text).join('');
    assert.deepEqual(scenario.messages.at(-1), { type: 'done', exitCode: 0 });
    const version = scenario.messages.find(message => message.type === 'version');
    assert.match(version.version, /^3\.14\.2\b/);
    assert.equal(scenario.pageErrors.length, 0);
    assert.equal(scenario.stderr, '');
    return scenario;
  } finally {
    await context.close();
  }
}

async function nativeRequest(name, method, requestPath, headers, body, expectedStatus, expectedError) {
  const result = await new Promise((resolve, reject) => {
    const request = http.request(serviceOrigin + requestPath, { method, headers, timeout: 3000 }, response => {
      let text = '';
      response.setEncoding('utf8');
      response.on('data', value => { text += value; });
      response.on('end', () => resolve({ status: response.statusCode, headers: response.headers, body: text ? JSON.parse(text) : null }));
    });
    request.on('error', reject);
    request.on('timeout', () => request.destroy(new Error('Native request timeout')));
    request.end(body);
  });
  evidence.nativeValidation.push({ name, method, path: requestPath, expectedStatus, expectedError, ...result });
  assert.equal(result.status, expectedStatus, name);
  if (expectedError) assert.equal(result.body.error, expectedError, name);
}


function summarize(raw) {
  const parseServiceLog = lines => lines.flatMap(line => {
    const match = line.match(/"(\S+) (\S+) HTTP\/[^"]+" (\d+) .*request_id=([a-f0-9]+)/);
    return match ? [{ method: match[1], path: match[2], status: Number(match[3]), requestID: match[4] }] : [];
  });
  const countOrigins = requests => {
    const counts = {};
    for (const request of requests) {
      const origin = new URL(request.url).origin;
      counts[origin] = (counts[origin] ?? 0) + 1;
    }
    return counts;
  };
  const serviceRecords = parseServiceLog(raw.serviceLog);
  const requestIDs = [raw.happyPath?.stock.request_id, raw.happyPath?.quote.request_id];
  return {
    schemaVersion: 1,
    checkedAt: raw.checkedAt,
    passed: raw.passed,
    method: raw.method,
    scope: raw.scope,
    sources: raw.sources,
    runtime: raw.runtime,
    nativePython: raw.nativePython,
    browser: raw.browser,
    playwright: raw.playwright,
    origins: raw.origins,
    clientSubstitution: raw.clientSubstitution,
    scenarios: raw.scenarios.map(scenario => ({
      name: scenario.name,
      sourceSHA256: scenario.sourceSHA256,
      terminalMessage: scenario.messages?.at(-1),
      reportedPython: scenario.messages?.find(message => message.type === 'version'),
      expectedBrowserFailure: scenario.expectedBrowserFailure,
      requestEventOrigins: countOrigins(scenario.requests),
      observedBrowserFailures: scenario.failedRequests.map(request => ({ method: request.method, path: new URL(request.url).pathname, error: request.failure.errorText })),
      pageErrors: scenario.pageErrors,
    })),
    happyPath: raw.happyPath,
    requestIDLogCorrelation: serviceRecords.filter(record => requestIDs.includes(record.requestID)),
    successfulJSONPreflights: serviceRecords.filter(record => record.method === 'OPTIONS' && record.path === '/quote' && record.status === 204),
    rejectedOrigin: raw.corsRejection ? {
      pythonResults: raw.corsRejection.results,
      serviceRecords: parseServiceLog(raw.corsRejection.serviceLog),
      quotePOSTReachedService: raw.corsRejection.serviceLog.some(line => /"POST \/quote /.test(line)),
    } : undefined,
    unavailableService: raw.unavailableService,
    nativeValidation: raw.nativeValidation.map(result => ({ name: result.name, method: result.method, path: result.path, status: result.status, error: result.body?.error })),
    originAudit: {
      browserRequestEventOrigins: countOrigins(raw.scenarios.flatMap(scenario => scenario.requests)),
      unexpectedOrigins: raw.unexpectedOrigins,
      interpretation: 'Browser request events include blocked attempts; native service logs establish whether a request reached the service. No internet request was observed, and no network firewall was installed.',
    },
    failure: raw.failure,
  };
}

(async () => {
  try {
    for (const [filename, expected] of Object.entries(runtimeHashes)) {
      const bytes = fs.readFileSync(path.join(runtimeDirectory, filename));
      const sha256 = digest(bytes);
      assert.equal(sha256, expected, `Cached runtime differs: ${filename}`);
      evidence.runtime.assets.push({ filename, sha256, bytes: bytes.length, originalURL: `https://cdn.jsdelivr.net/pyodide/v314.0.7/full/${filename}` });
    }
    evidence.nativePython = execFileSync(python, ['--version'], { encoding: 'utf8' }).trim();
    const allowedOrigin = await startLab('allowed');
    const rejectedOrigin = await startLab('rejected');
    serviceOrigin = await startService(allowedOrigin);
    evidence.origins = { allowedOrigin, rejectedOrigin, serviceOrigin };
    evidence.serviceAnnouncement = serviceOutput.trim();
    browser = await chromium.launch({ headless: true });
    evidence.browser = browser.version();
    evidence.playwright = require('@playwright/test/package.json').version;
    const originalClient = sources.client.toString('utf8');
    const placeholder = 'SERVICE_URL = "http://127.0.0.1:8132"';
    assert.equal(originalClient.split(placeholder).length, 2, 'Expected one service URL constant');
    const client = originalClient.replace(placeholder, `SERVICE_URL = ${JSON.stringify(serviceOrigin)}`);
    evidence.clientSubstitution = { onlyChange: 'SERVICE_URL uses the native service ephemeral loopback port', originalSHA256: digest(sources.client), executedSHA256: digest(Buffer.from(client)) };
    const happy = await runWorker('documented-client', allowedOrigin, client);
    const parseLine = (text, prefix) => JSON.parse(text.split('\n').find(line => line.startsWith(prefix)).slice(prefix.length));
    const stock = parseLine(happy.stdout, 'stock: ');
    const quote = parseLine(happy.stdout, 'quote: ');
    assert.equal(stock.status, 200);
    assert.equal(quote.status, 200);
    assert.equal(quote.body.total_cents, 250);
    assert.match(stock.request_id, /^[a-f0-9]{32}$/);
    assert.match(quote.request_id, /^[a-f0-9]{32}$/);
    assert.match(happy.stdout, /expected_error: HTTP 404:/);
    assert.match(happy.stdout, /expected_error: HTTP 422:/);
    assert.match(happy.stdout, /expected_timeout: Service request deadline expired/);
    evidence.happyPath = { stock, quote, expectedHTTPStatuses: [404, 422], timeout: 'TimeoutError: Service request deadline expired', exposedRequestIDs: true };
    const definitions = client.slice(0, client.indexOf('\nstock = await request('));
    assert(definitions.length > 0 && definitions.length < client.length);
    const logStart = evidence.serviceLog.length;
    const rejected = await runWorker('rejected-origin', rejectedOrigin, definitions + `\nresults = []\nfor path, payload in [("/stock/widget", None), ("/quote", {"sku": "widget", "quantity": 2})]:\n    try:\n        await request(path, payload)\n    except Exception as error:\n        assert isinstance(error, AbortError)\n        assert not isinstance(error, (ServiceError, TimeoutError))\n        results.append({"path": path, "type": type(error).__name__, "message": str(error), "responseReadable": False, "isOSError": isinstance(error, OSError)})\n    else:\n        raise AssertionError("Rejected origin read a service response")\nprint("cors_results:", json.dumps(results))\n`);
    await new Promise(resolve => setTimeout(resolve, 50));
    evidence.corsRejection = { results: parseLine(rejected.stdout, 'cors_results: '), serviceLog: evidence.serviceLog.slice(logStart) };
    assert.equal(evidence.corsRejection.results.length, 2);
    assert(evidence.corsRejection.serviceLog.some(line => /"GET \/stock\/widget HTTP\/1\.1" 403/.test(line)));
    assert(evidence.corsRejection.serviceLog.some(line => /"OPTIONS \/quote HTTP\/1\.1" 403/.test(line)));
    assert(!evidence.corsRejection.serviceLog.some(line => /"POST \/quote /.test(line)), 'Browser sent POST despite rejected preflight');
    assert(evidence.serviceLog.some(line => /"OPTIONS \/quote HTTP\/1\.1" 204/.test(line)), 'Successful JSON preflight missing from native log');
    assert(evidence.serviceLog.some(line => line.includes('request_id=' + stock.request_id)), 'Stock request ID not found in service log');
    assert(evidence.serviceLog.some(line => line.includes('request_id=' + quote.request_id)), 'Quote request ID not found in service log');
    evidence.happyPath.requestIDsCorrelateWithServiceLog = true;
    const jsonHeaders = body => ({ 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) });
    for (const [name, body, status, error] of [
      ['malformed JSON', '{', 400, 'invalid_json'],
      ['boolean quantity', '{"sku":"widget","quantity":true}', 422, 'invalid_quote'],
      ['fractional quantity', '{"sku":"widget","quantity":2.5}', 422, 'invalid_quote'],
      ['quantity above stock', '{"sku":"widget","quantity":8}', 422, 'invalid_quote'],
      ['wrong object shape', '[]', 422, 'invalid_quote'],
      ['empty body', '', 413, 'body_size'],
      ['oversized body', 'x'.repeat(4097), 413, 'body_size'],
    ]) await nativeRequest(name, 'POST', '/quote', jsonHeaders(body), body, status, error);
    await nativeRequest('non-JSON media type', 'POST', '/quote', { 'Content-Type': 'text/plain', 'Content-Length': 2 }, '{}', 415, 'json_required');
    await nativeRequest('unsupported preflight header', 'OPTIONS', '/quote', { Origin: allowedOrigin, 'Access-Control-Request-Method': 'POST', 'Access-Control-Request-Headers': 'x-unapproved' }, undefined, 403, 'preflight_not_allowed');
    await stopService();
    const unavailable = await runWorker('service-unavailable', allowedOrigin, definitions + `\ntry:\n    await request("/stock/widget", timeout_ms=2000)\nexcept Exception as error:\n    assert isinstance(error, AbortError)\n    assert not isinstance(error, (TimeoutError, ServiceError))\n    print("unavailable:", json.dumps({"type": type(error).__name__, "message": str(error), "isTimeout": isinstance(error, TimeoutError), "isOSError": isinstance(error, OSError)}))\nelse:\n    raise AssertionError("Stopped service unexpectedly answered")\n`);
    evidence.unavailableService = parseLine(unavailable.stdout, 'unavailable: ');
    const allowed = new Set([allowedOrigin, rejectedOrigin, serviceOrigin]);
    evidence.unexpectedOrigins = evidence.scenarios.flatMap(scenario => scenario.requests.filter(request => !allowed.has(new URL(request.url).origin)).map(request => request.url));
    assert.deepEqual(evidence.unexpectedOrigins, []);
    for (const [name, relative] of Object.entries(sourcePaths)) assert.equal(digest(fs.readFileSync(path.join(repository, relative))), evidence.sources[name].sha256, `Source changed during verification: ${relative}`);
    evidence.passed = true;
  } catch (error) {
    evidence.passed = false;
    evidence.failure = { message: error.message, stack: error.stack };
    process.exitCode = 1;
  } finally {
    if (browser) await browser.close();
    await stopService();
    await Promise.all(servers.map(server => new Promise(resolve => server.close(resolve))));
    fs.mkdirSync(path.dirname(output), { recursive: true });
    fs.writeFileSync(output, JSON.stringify(evidence, null, 2) + '\n');
    if (summaryOutput) {
      fs.mkdirSync(path.dirname(summaryOutput), { recursive: true });
      fs.writeFileSync(summaryOutput, JSON.stringify(summarize(evidence), null, 2) + '\n');
    }
    console.log(JSON.stringify({ passed: evidence.passed, output, summaryOutput, scenarios: evidence.scenarios.map(scenario => ({ name: scenario.name, lastMessage: scenario.messages?.at(-1), requests: scenario.requests.length })), failure: evidence.failure }, null, 2));
  }
})();
