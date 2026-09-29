import createPython from './python.mjs';
import { readFile } from 'node:fs/promises';
process.on('uncaughtException', error => { console.error(error.stack); process.exit(1); });
const output = [], errors = [];
const expected = process.argv[2];
if (process.env.REQUIRE_JSPI && typeof WebAssembly.promising !== 'function') throw Error('JSPI-enabled engine required for this check');
const wasmBinary = await readFile(new URL('./python.wasm', import.meta.url));
const data = await readFile(new URL('./python.data', import.meta.url));
if (!wasmBinary.subarray(0, 4).equals(Buffer.from([0, 97, 115, 109]))) throw Error('Not WebAssembly');
let exitCode = 0;
const module = await createPython({
  noInitialRun: true,
  wasmBinary,
  getPreloadedPackage: () => data.buffer.slice(data.byteOffset, data.byteOffset + data.byteLength),
  print: line => output.push(line),
  printErr: line => errors.push(line),
  onExit: status => { exitCode = status; },
});
try {
  module.callMain(['-c', `import sys, json, math, re, os, sysconfig\nassert sysconfig.get_config_var('SIZEOF_VOID_P') == 4\nassert sysconfig.get_config_var('HAVE_FORK') == 0\nassert sys.version.split()[0] == ${JSON.stringify(expected)}\nassert sum(x*x for x in range(10)) == 285\nassert json.loads('{"x":42}')['x'] == 42\nassert math.sqrt(81) == 9\nassert re.match('a+', 'aaa').group(0) == 'aaa'\nf=open('/tmp/smoke.txt','w'); f.write('wasm'); f.close()\nf=open('/tmp/smoke.txt'); assert f.read() == 'wasm'; f.close()\nmodules={}\nfor name in ['sqlite3','zlib','bz2','decimal','ssl','ctypes','pip','micropip']:\n try:\n  __import__(name); modules[name]=True\n except ImportError:\n  modules[name]=False\nprint(json.dumps({'version':sys.version,'platform':sys.platform,'modules':modules,'checks':['version','arithmetic','json','math','regex','filesystem']}))`]);
} catch (error) {
  if (error.name !== 'ExitStatus') throw error;
  exitCode = error.status;
}
if (exitCode) throw Error(`Python exited ${exitCode}: ${errors.join('\n')}`);
if (errors.length) throw Error(`Unexpected startup or smoke stderr: ${errors.join('\n')}`);
const result = JSON.parse(output.at(-1));
if (!result.version.startsWith(expected + ' ')) throw Error('Version mismatch');
let failureExit = 0;
const failureOut = [], failureErr = [];
const failing = await createPython({
  noInitialRun: true, wasmBinary,
  getPreloadedPackage: () => data.buffer.slice(data.byteOffset, data.byteOffset + data.byteLength),
  print: line => failureOut.push(line), printErr: line => failureErr.push(line),
  onExit: status => { failureExit = status; },
  quit: (status, error) => { failureExit = status; throw error; },
});
try {
  const status = failing.callMain(['-c', "raise ValueError('expected-wasm-smoke-failure')"]);
  if (Number.isInteger(status)) failureExit = status;
} catch (error) {
  if (error.name !== 'ExitStatus') throw error;
  failureExit = error.status;
}
if (failureExit !== 1 || failureOut.length || !failureErr.join('\n').includes('ValueError: expected-wasm-smoke-failure')) {
  throw Error(`Exception behavior mismatch: ${failureExit}; ${failureErr.join('\n')}`);
}
process.exitCode = 0;
process.stdout.write(JSON.stringify({ ...result, stderr: errors, failureExit,
  engine: process.version, jsStackSwitching: typeof WebAssembly.promising === 'function' }, null, 2) + '\n');
