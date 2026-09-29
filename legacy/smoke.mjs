import fs from 'fs';
import assert from 'assert';
import { createHash } from 'crypto';
import createPython from './python.mjs';
const stdout = [];
const stderr = [];
createPython({
  print: text => { stdout.push(text); console.log(text); },
  printErr: text => { stderr.push(text); console.error(text); },
}).then(module => {
module.callMain(['-c', "import sys, json, math, hashlib, re, time; assert sys.version_info[:3] == (2,7,18); assert 7/2 == 3; assert math.sqrt(81) == 9; assert time.gmtime(0).tm_year == 1970; assert '%d' % -9223372036854775807 == '-9223372036854775807'; assert re.findall('[0-9]+', 'wasm42') == ['42']; open('/tmp/wasm-smoke.txt', 'w').write('roundtrip'); assert open('/tmp/wasm-smoke.txt').read() == 'roundtrip'; print(json.dumps({'version':sys.version,'platform':sys.platform,'integer_division':7/2,'sha256':hashlib.sha256(b'wasm').hexdigest(),'maxunicode':sys.maxunicode,'astralLength':len(u'\\U0001f600'),'modules':{'json':True,'math':True,'hashlib':True,'re':True,'time':True,'filesystem':True}}))"]);
assert(stdout.some(line => line.includes('2.7.18')));
assert.equal(stderr.length, 0);
assert.equal(JSON.parse(stdout[stdout.length - 1]).sha256, createHash('sha256').update('wasm').digest('hex'));
assert.equal(fs.readFileSync(new URL('./python.wasm', import.meta.url)).subarray(0, 4).toString('hex'), '0061736d');
fs.writeFileSync(new URL('./smoke-result.json', import.meta.url), JSON.stringify({status:'passed',stdout,stderr}, null, 2));
fs.writeFileSync(new URL('./smoke.json', import.meta.url), JSON.stringify(JSON.parse(stdout[stdout.length - 1]), null, 2));
}).then(async () => {
  const errors = [];
  const failing = await createPython({print: () => {}, printErr: text => errors.push(text)});
  assert.equal(failing.callMain(['-c', "raise ValueError('failure-probe')"]), 1);
  assert(errors.some(line => line.includes('ValueError: failure-probe')));
}).catch(error => { console.error(error); process.exitCode = 1; });
