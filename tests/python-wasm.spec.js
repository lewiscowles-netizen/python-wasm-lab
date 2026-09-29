const { test, expect } = require('@playwright/test');
const fs = require('node:fs');
const path = require('node:path');

const catalog = JSON.parse(fs.readFileSync(path.join(__dirname, '../experiments/wasm/python/runtimes.json'), 'utf8'));
const localCatalogPath = path.join(__dirname, '../experiments/wasm/python/runtimes.local.json');
const localCatalog = fs.existsSync(localCatalogPath) ? JSON.parse(fs.readFileSync(localCatalogPath, 'utf8')) : { runtimes: [] };
const runtimes = [...new Map([...catalog.runtimes, ...localCatalog.runtimes].map(runtime => [runtime.id, runtime])).values()];
const localRuntimes = runtimes.filter(runtime => runtime.adapter === 'emscripten');
const pyodide = runtimes.find(runtime => runtime.adapter === 'pyodide');
const enablePyodide = process.env.PYTHON_WASM_TEST_PYODIDE === '1';
const librarySmoke = `from __future__ import print_function
import sys, json, re, math
print("WASM_STDOUT", sum(x*x for x in range(10)))
print("Unicode: café")
print("JSON", json.loads(json.dumps({"x":42}))["x"])
print("Regex", re.match("a+", "aaa").group(0))
print("Math", math.sqrt(81))
with open("/tmp/browser-smoke.txt", "w") as f:
    f.write("wasm")
with open("/tmp/browser-smoke.txt") as f:
    print("File", f.read())
sys.stderr.write("WASM_STDERR\\n")
`;

async function selectRuntime(page, runtime) {
  await page.goto('/experiments/wasm/python/');
  await page.getByLabel('Python build', { exact: true }).selectOption(runtime.id);
  await page.getByLabel('Time limit', { exact: true }).selectOption('120');
}

async function runCode(page, code) {
  await page.getByLabel('Python source code', { exact: true }).fill(code);
  await page.getByRole('button', { name: 'Run Python', exact: true }).click();
}

test('version selector orders local CPython builds and separates Pyodide', async ({ page }) => {
  await page.goto('/experiments/wasm/python/');
  await expect(page.getByRole('status')).toHaveText('Ready. The first run downloads the selected runtime.');
  const selector = page.getByLabel('Python build', { exact: true });
  await expect(selector.locator('option')).toHaveCount(runtimes.length);
  if (localRuntimes.length) {
    const expected = [...localRuntimes].sort((a, b) => a.version.localeCompare(b.version, 'en', { numeric: true }));
    const group = selector.locator('optgroup[label="CPython — local builds"]');
    expect(await group.locator('option').evaluateAll(options => options.map(option => option.value))).toEqual(expected.map(runtime => runtime.id));
    const stable = expected.filter(runtime => /^\d+\.\d+\.\d+$/.test(runtime.version));
    await expect(selector).toHaveValue((stable.at(-1) ?? expected.at(-1)).id);
    for (const runtime of expected.filter(runtime => /rc\d+$/.test(runtime.version))) {
      await expect(group.locator(`option[value="${runtime.id}"]`)).toContainText('prerelease');
    }
  }
  if (pyodide) {
    await selector.selectOption(pyodide.id);
    await expect(page.getByLabel('Enable micropip for this run')).toBeEnabled();
    await expect(page.getByLabel('Enable micropip for this run')).not.toBeChecked();
  }
});

test('clean checkout loads the baseline without a local runtime catalog', async ({ page }) => {
  await page.route('**/runtimes.local.json', route => route.fulfill({ status: 404, body: '' }));
  await page.goto('/experiments/wasm/python/');
  await expect(page.getByRole('status')).toHaveText('Ready. The first run downloads the selected runtime.');
  await expect(page.getByLabel('Python build', { exact: true }).locator('option')).toHaveCount(catalog.runtimes.length);
  await expect(page.getByRole('button', { name: 'Run Python', exact: true })).toBeEnabled();
});

const infoRuntimes = [
  localRuntimes.find(runtime => runtime.version?.startsWith('2.7.')),
  localRuntimes.find(runtime => runtime.version?.startsWith('3.0.')),
  ...localRuntimes.filter(runtime => /^3\.(11|12|13|14|15)\./.test(runtime.version)),
  pyodide,
].filter(Boolean);
for (const runtime of infoRuntimes) {
  test(`${runtime.label}: Python info survives missing optional metadata`, async ({ page }) => {
    test.skip(runtime.adapter === 'pyodide' && !enablePyodide, 'Opt in to CDN tests with PYTHON_WASM_TEST_PYODIDE=1');
    test.setTimeout(150_000);
    await selectRuntime(page, runtime);
    await page.getByLabel('Example', { exact: true }).selectOption('info');
    await expect(page.getByLabel('Python source code', { exact: true })).toHaveValue(/Diagnostics complete/);
    await page.getByRole('button', { name: 'Run Python', exact: true }).click();
    await expect(page.getByRole('status')).toHaveText('Finished with exit code 0.', { timeout: 120_000 });
    const output = page.locator('#stdout');
    await expect(output).toContainText('Platform: emscripten');
    await expect(output).toContainText('Pointer width (bits): 32');
    await expect(output).toContainText('Length of one astral character:');
    await expect(output).toContainText('Target build metadata:');
    if (runtime.adapter === 'emscripten' && /^3\.(11|12|13|14|15)\./.test(runtime.version)) {
      await expect(output).toContainText('Target build metadata: available');
      await expect(output).toContainText('SIZEOF_VOID_P: 4');
    }
    await expect(output).toContainText('Diagnostics complete.');
    await expect(page.locator('#stderr')).toBeEmpty();
  });
}

for (const runtime of localRuntimes) {
  test(`${runtime.label}: version, library, files, streams and exceptions`, async ({ page }) => {
    test.setTimeout(150_000);
    await selectRuntime(page, runtime);
    await expect(page.getByLabel('Enable micropip for this run')).toBeDisabled();
    await runCode(page, librarySmoke);
    await expect(page.getByRole('status')).toHaveText('Finished with exit code 0.', { timeout: 120_000 });
    await expect(page.locator('#reported-version')).toContainText(runtime.version);
    await expect(page.locator('#stdout')).toHaveText('WASM_STDOUT 285\nUnicode: café\nJSON 42\nRegex aaa\nMath 9.0\nFile wasm\n');
    await expect(page.locator('#stderr')).toHaveText('WASM_STDERR\n');

    await runCode(page, 'raise RuntimeError("WASM_EXPECTED_EXCEPTION")\n');
    await expect(page.getByRole('status')).toHaveText('Finished with exit code 1.', { timeout: 120_000 });
    await expect(page.locator('#stderr')).toHaveText('Traceback (most recent call last):\n  File "<playground>", line 1, in <module>\nRuntimeError: WASM_EXPECTED_EXCEPTION\n');
    await expect(page.locator('#stdout')).toBeEmpty();

    const manifestPath = runtime.manifest && path.join(__dirname, '../experiments/wasm/python', runtime.manifest);
    const manifest = manifestPath && fs.existsSync(manifestPath) ? JSON.parse(fs.readFileSync(manifestPath, 'utf8')) : {};
    if (manifest.features?.modules?.sqlite3 === true) {
      await page.getByLabel('Example', { exact: true }).selectOption('sqlite');
      await page.getByRole('button', { name: 'Run Python', exact: true }).click();
      await expect(page.getByRole('status')).toHaveText('Finished with exit code 0.', { timeout: 120_000 });
      await expect(page.locator('#stdout')).toContainText("('Python 3.0', 2008)\n('Python 2.7', 2010)\nSQLite version:");
      await expect(page.locator('#stderr')).toBeEmpty();
      await test.info().attach('sqlite-result', { body: await page.locator('#stdout').innerText(), contentType: 'text/plain' });
    }
  });
}

test('worker stop and time limit terminate Python loops', async ({ page }) => {
  test.skip(localRuntimes.length === 0 && (!enablePyodide || !pyodide), 'No local builds; CDN tests require PYTHON_WASM_TEST_PYODIDE=1');
  test.setTimeout(150_000);
  const runtime = localRuntimes[0] ?? pyodide;
  await selectRuntime(page, runtime);
  await runCode(page, 'while True:\n    pass\n');
  await expect(page.locator('#reported-version')).toContainText('emscripten', { timeout: 120_000 });
  await page.getByRole('button', { name: 'Stop', exact: true }).click();
  await expect(page.getByRole('status')).toHaveText('Stopped by you.');
  await expect(page.getByRole('button', { name: 'Run Python', exact: true })).toBeEnabled();

  await page.getByLabel('Time limit', { exact: true }).selectOption('10');
  await runCode(page, 'while True:\n    pass\n');
  await expect(page.getByRole('status')).toHaveText('Stopped: time limit reached.', { timeout: 15_000 });
  await runCode(page, 'print("RECOVERED")');
  await expect(page.getByRole('status')).toHaveText('Finished with exit code 0.', { timeout: 15_000 });
  await expect(page.locator('#stdout')).toHaveText('RECOVERED\n');
});

test('Pyodide optional micropip installs a pure Python wheel', async ({ page }) => {
  test.skip(!enablePyodide || !pyodide, 'Opt in with PYTHON_WASM_TEST_PYODIDE=1; this downloads from jsDelivr and PyPI');
  test.setTimeout(150_000);
  await selectRuntime(page, pyodide);
  const micropip = page.getByLabel('Enable micropip for this run');
  await expect(micropip).not.toBeChecked();
  await expect(page.getByLabel('Install packages before running (one requirement per line)')).toBeDisabled();
  await micropip.check();
  await page.getByLabel('Install packages before running (one requirement per line)').fill('snowballstemmer==3.0.1');
  await runCode(page, 'import snowballstemmer\nimport sys\nprint(snowballstemmer.stemmer("english").stemWords(["running", "jumping"]))\nsys.stderr.write("PYODIDE_STDERR\\n")\n');
  await expect(page.getByRole('status')).toHaveText('Finished with exit code 0.', { timeout: 120_000 });
  await expect(page.locator('#reported-version')).toContainText('emscripten');
  await expect(page.locator('#stdout')).toContainText("['run', 'jump']");
  await expect(page.locator('#stderr')).toHaveText('PYODIDE_STDERR\n');

  await micropip.uncheck();
  await runCode(page, 'import snowballstemmer');
  await expect(page.getByRole('status')).toHaveText('Execution failed.', { timeout: 120_000 });
  await expect(page.locator('#stderr')).toContainText("No module named 'snowballstemmer'");
});

test('Pyodide runs the pinned Datasette application', async ({ page }) => {
  test.skip(!enablePyodide || !pyodide, 'Opt in with PYTHON_WASM_TEST_PYODIDE=1; this downloads Pyodide and Datasette dependencies');
  test.setTimeout(150_000);
  await selectRuntime(page, pyodide);
  await page.getByLabel('Example', { exact: true }).selectOption('datasette');
  await page.getByLabel('Enable micropip for this run').check();
  await expect(page.getByLabel('Python source code', { exact: true })).toHaveValue(/from datasette.app import Datasette/);
  await page.getByRole('button', { name: 'Run Python', exact: true }).click();
  await expect(page.getByRole('status')).toHaveText('Finished with exit code 0.', { timeout: 120_000 });
  const output = page.locator('#stdout');
  await expect(output).toContainText('JSON status: 200');
  await expect(output).toContainText('"name": "Python 2.7"');
  await expect(output).toContainText('HTML status: 200');
  await expect(output).toContainText('HTML contains our row: True');
  await expect(output).toContainText('Missing page status: 404');
  await expect(page.locator('#stderr')).toBeEmpty();
});

test('Pyodide automatic import loading enables a compiled NumPy package', async ({ page }) => {
  test.skip(!enablePyodide || !pyodide, 'Opt in with PYTHON_WASM_TEST_PYODIDE=1; this downloads NumPy from the Pyodide distribution');
  test.setTimeout(150_000);
  await selectRuntime(page, pyodide);
  await page.getByLabel('Example', { exact: true }).selectOption('arrays');
  const autoPackages = page.getByLabel('Load known Pyodide packages named in imports');
  await autoPackages.check();
  await expect(page.getByLabel('Enable micropip for this run')).not.toBeChecked();
  await page.getByRole('button', { name: 'Run Python', exact: true }).click();
  await expect(page.getByRole('status')).toHaveText('Finished with exit code 0.', { timeout: 120_000 });
  await expect(page.locator('#stdout')).toContainText('NumPy 2.4.6');
  await expect(page.locator('#stdout')).toContainText('[3, 5, 7]');
  await expect(page.locator('#stderr')).toBeEmpty();

  await autoPackages.uncheck();
  await page.getByRole('button', { name: 'Run Python', exact: true }).click();
  await expect(page.getByRole('status')).toHaveText('Execution failed.', { timeout: 120_000 });
  await expect(page.locator('#stderr')).toContainText("No module named 'numpy'");
});

test('Pyodide flushes partial output before an exception ends its worker', async ({ page }) => {
  test.skip(!enablePyodide || !pyodide, 'Opt in with PYTHON_WASM_TEST_PYODIDE=1');
  test.setTimeout(150_000);
  await selectRuntime(page, pyodide);
  await runCode(page, 'import sys\nsys.stdout.write("partial stdout")\nsys.stderr.write("partial stderr")\nraise ValueError("after partial output")\n');
  await expect(page.getByRole('status')).toHaveText('Execution failed.', { timeout: 120_000 });
  await expect(page.locator('#stdout')).toContainText('partial stdout');
  await expect(page.locator('#stderr')).toContainText('partial stderr');
  await expect(page.locator('#stderr')).toContainText('ValueError: after partial output');
});
