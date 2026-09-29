const elements = Object.fromEntries([
  'runtime', 'timeout', 'example', 'code', 'run', 'stop', 'status', 'stdout', 'stderr',
  'reported-version', 'elapsed', 'capabilities', 'runtime-description', 'runtime-count', 'manifest-note',
  'package-controls', 'auto-packages', 'enable-micropip', 'packages', 'package-note',
  'example-note',
].map(id => [id, document.getElementById(id)]));

const examples = {
  hello: 'from __future__ import print_function\nimport sys\n\nprint("Hello from Python", sys.version.split()[0])\nprint("The sum of squares is", sum(x * x for x in range(10)))\nprint("Integer division:", 7 // 2)\nprint("Slash division:", 7 / 2)\n',
  stdlib: 'from __future__ import print_function\n\nmodules = ["json", "math", "re", "decimal", "csv", "sqlite3",\n           "zlib", "ssl", "socket", "subprocess", "pip", "micropip"]\nfor name in modules:\n    try:\n        __import__(name)\n        print(name + ": import succeeded")\n    except Exception as error:\n        print(name + ": " + str(error))\n\nprint("Importing a module does not prove all of its operations work.")\n',
  sqlite: 'from __future__ import print_function\nimport sqlite3\n\nconnection = sqlite3.connect(":memory:")\nconnection.execute("CREATE TABLE releases (language TEXT, year INTEGER)")\nconnection.executemany("INSERT INTO releases VALUES (?, ?)",\n                       [("Python 2.7", 2010), ("Python 3.0", 2008)])\nfor row in connection.execute("SELECT language, year FROM releases ORDER BY year"):\n    print(row)\nprint("SQLite version:", sqlite3.sqlite_version)\nconnection.close()\n',
  syntax: 'from __future__ import print_function\nimport sys\n\nprint("Python", sys.version.split()[0])\nprint("7 / 2 =", 7 / 2)\nprint("range(3) =", range(3))\n\n# Uncomment a feature to discover which versions accept it:\n# print(f"An f-string: {2 + 2}")\n# print((answer := 42))\n',
  files: 'from __future__ import print_function\nimport os\n\npath = "/tmp/python-wasm-example.txt"\nwith open(path, "w") as output:\n    output.write("Hello, virtual filesystem!\\n")\nwith open(path) as source:\n    print(source.read())\nprint("File size:", os.path.getsize(path))\nprint("This file disappears when the worker stops.")\n',
  packages: 'import snowballstemmer\n\nprint(snowballstemmer.stemmer("english").stemWords(["running", "jumping"]))\n',
  arrays: 'import numpy as np\n\nprint("NumPy", np.__version__)\nprint(np.arange(6).reshape(2, 3).sum(axis=0).tolist())\n',
  browser: 'from js import URL\nfrom pyodide.http import pyfetch\n\nurl = URL.new("https://example.com/lab?python=wasm")\nprint("JavaScript URL hostname:", url.hostname)\nprint("Query value:", url.searchParams.get("python"))\n\nresponse = await pyfetch("./runtimes.json")\ncatalog = await response.json()\nprint("Local catalog schema:", catalog["schemaVersion"])\n',
  errors: 'from __future__ import print_function\nimport sys\n\nprint("This is standard output.")\nsys.stderr.write("This is standard error.\\n")\nraise ValueError("An intentional example error")\n',
  loop: 'while True:\n    pass\n',
};

const exampleNotes = {
  hello: 'Runs on Python 2.7 and Python 3. Compare slash division and the actual version reported below.',
  info: 'A portable interpreter and build report, similar in purpose to phpinfo(). Missing modules or target build metadata are reported as unavailable. It does not dump environment variables or launch processes.',
  stdlib: 'Import tests distinguish bundled modules from missing ones. An import does not prove every operation works.',
  sqlite: 'Creates and queries an in-memory database. Requires a working sqlite3 module in the selected build.',
  syntax: 'Uncomment newer syntax and compare which Python versions parse it.',
  files: 'Writes to the runtime’s virtual /tmp directory. The worker discards this file after execution.',
  packages: 'Choose Pyodide, enable micropip, and enter snowballstemmer==3.0.1 above. Then disable micropip and rerun to verify a fresh environment.',
  arrays: 'Choose Pyodide and check Load known Pyodide packages named in imports. Leave micropip unchecked. This loads the compiled NumPy package built for the pinned Pyodide distribution.',
  browser: 'Requires Pyodide. Uses the browser’s URL API and fetches the local catalog with top-level await. It does not visit example.com.',
  datasette: 'Choose Pyodide, enable micropip, and leave the packages box empty. This example installs pinned requirements from the local lab file, then requests JSON and HTML from Datasette. Allow 2 minutes for first-time downloads.',
  errors: 'Deliberately raises an exception after writing to both streams. This run should fail.',
  loop: 'This code never exits by itself. Use Stop or select a 10-second time limit before running.',
};

const capabilityLabels = {
  stdlib: 'Standard library', sqlite3: 'SQLite', pip: 'pip', micropip: 'micropip',
  nativeWheels: 'Native wheels', network: 'Network', filesystem: 'Filesystem',
};
let runtimes = [];
let worker = null;
let timeoutId;
let started;
let selectionToken = 0;
const exampleFiles = { datasette: './examples/datasette.py', info: './examples/python-info.py' };

function selectedRuntime() {
  return runtimes.find(runtime => runtime.id === elements.runtime.value);
}

function setRunning(running) {
  elements.run.disabled = running || !selectedRuntime();
  elements.stop.disabled = !running;
  elements.runtime.disabled = running || runtimes.length === 0;
  elements['package-controls'].disabled = running || selectedRuntime()?.adapter !== 'pyodide';
}

function finish(message) {
  worker?.terminate();
  worker = null;
  clearTimeout(timeoutId);
  setRunning(false);
  elements.status.textContent = message;
  if (started !== undefined) {
    elements.elapsed.textContent = ((performance.now() - started) / 1000).toFixed(2) + ' seconds';
  }
}

function capabilityText(capability) {
  if (capability === true) return 'Included';
  if (capability === false) return 'Not included';
  if (typeof capability === 'string') return capability;
  if (capability && typeof capability === 'object') {
    return capability.detail ?? capability.status ?? 'Not declared';
  }
  return 'Not declared';
}

function renderCapabilities(capabilities = {}) {
  elements.capabilities.replaceChildren();
  for (const [key, label] of Object.entries(capabilityLabels)) {
    const item = document.createElement('div');
    const term = document.createElement('dt');
    const value = document.createElement('dd');
    term.textContent = label;
    value.textContent = capabilityText(capabilities[key]);
    item.append(term, value);
    elements.capabilities.append(item);
  }
}

function manifestCapabilities(manifest, fallback) {
  if (manifest.capabilities) return manifest.capabilities;
  if (!manifest.features) return fallback;
  const features = manifest.features;
  const modules = features.modules ?? {};
  return {
    ...fallback,
    stdlib: Object.values(modules).some(value => value === true) ? 'Import smoke tests recorded in manifest' : fallback?.stdlib,
    sqlite3: modules.sqlite3 === true ? 'Import smoke test passed' : modules.sqlite3,
    pip: features.pip ?? modules.pip,
    micropip: features.micropip ?? modules.micropip,
    filesystem: features.filesystem,
    nativeWheels: features.dynamicLinking === false ? 'Dynamic linking disabled' : undefined,
  };
}

async function describeRuntime() {
  const runtime = selectedRuntime();
  const token = ++selectionToken;
  if (!runtime) return;
  const isPyodide = runtime.adapter === 'pyodide';
  elements['package-controls'].disabled = !isPyodide;
  elements['auto-packages'].checked = false;
  elements['enable-micropip'].checked = false;
  elements.packages.disabled = true;
  elements['package-note'].textContent = isPyodide
    ? 'Off by default. These options download packages from jsDelivr, PyPI, or the supplied wheel URL. Packages must match Pyodide’s Python and WebAssembly ABI. Unchecking these controls skips automatic loading; it does not prohibit networking from your code.'
    : 'Package installation is unavailable for bare CPython builds.';
  elements['runtime-description'].textContent = runtime.description ?? runtime.label;
  elements['manifest-note'].textContent = 'Capabilities are declarations from this build; run the library probe to check imports.';
  renderCapabilities(runtime.capabilities);
  if (!runtime.manifest) return;
  try {
    const response = await fetch(new URL(runtime.manifest, import.meta.url));
    if (!response.ok) throw new Error('HTTP ' + response.status);
    const manifest = await response.json();
    if (token !== selectionToken) return;
    renderCapabilities(manifestCapabilities(manifest, runtime.capabilities));
    const link = document.createElement('a');
    link.href = new URL(runtime.manifest, import.meta.url).href;
    link.textContent = 'Build manifest';
    elements['manifest-note'].append(' ', link);
  } catch (error) {
    if (token === selectionToken) {
      elements['manifest-note'].textContent = 'Build manifest could not be read (' + error.message + '). Undeclared capabilities are unknown.';
    }
  }
}

function run() {
  const runtime = selectedRuntime();
  if (!runtime || worker || elements.run.disabled) return;
  elements.stdout.textContent = '';
  elements.stderr.textContent = '';
  elements['reported-version'].textContent = 'Waiting for Python to report its version…';
  elements.elapsed.textContent = 'Running';
  elements.status.textContent = 'Loading and running ' + runtime.label + '…';
  started = performance.now();
  setRunning(true);
  try {
    worker = new Worker(new URL('./worker.mjs', import.meta.url), { type: 'module' });
    worker.onmessage = ({ data }) => {
      if (data.type === 'output' && (data.stream === 'stdout' || data.stream === 'stderr')) {
        elements[data.stream].append(document.createTextNode(data.text));
      } else if (data.type === 'version') {
        elements['reported-version'].textContent = data.version + ' · ' + data.platform;
      } else if (data.type === 'done') {
        finish('Finished with exit code ' + data.exitCode + '.');
      } else if (data.type === 'error') {
        elements.stderr.append(document.createTextNode(data.message + '\n'));
        finish('Execution failed.');
      } else if (data.type === 'status') {
        elements.status.textContent = data.message;
      }
    };
    worker.onerror = event => {
      event.preventDefault();
      elements.stderr.append(document.createTextNode((event.message || 'Worker failed to load.') + '\n'));
      finish('Execution failed.');
    };
    timeoutId = setTimeout(() => finish('Stopped: time limit reached.'), Number(elements.timeout.value) * 1000);
    worker.postMessage({
      type: 'run', runtime: { ...runtime, baseURL: import.meta.url }, code: elements.code.value,
      options: {
        autoPackages: runtime.adapter === 'pyodide' && elements['auto-packages'].checked,
        micropip: runtime.adapter === 'pyodide' && elements['enable-micropip'].checked,
        packages: elements.packages.value.split('\n').map(line => line.trim()).filter(Boolean),
      },
    });
  } catch (error) {
    elements.stderr.textContent = error.message;
    finish('Execution failed.');
  }
}

elements.run.addEventListener('click', run);
elements.stop.addEventListener('click', () => finish('Stopped by you.'));
elements.runtime.addEventListener('change', describeRuntime);
elements['enable-micropip'].addEventListener('change', () => { elements.packages.disabled = !elements['enable-micropip'].checked; });
elements.example.addEventListener('change', async () => {
  const selected = elements.example.value;
  elements['example-note'].textContent = exampleNotes[selected];
  if (!exampleFiles[selected]) {
    elements.code.value = examples[selected];
    return;
  }
  elements.run.disabled = true;
  try {
    const response = await fetch(new URL(exampleFiles[selected], import.meta.url));
    if (!response.ok) throw new Error('HTTP ' + response.status);
    const source = await response.text();
    if (elements.example.value === selected) elements.code.value = source;
  } catch (error) {
    elements['example-note'].textContent = 'Could not load the selected example: ' + error.message;
  } finally {
    setRunning(Boolean(worker));
  }
});
elements.code.addEventListener('keydown', event => {
  if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
    event.preventDefault();
    run();
  }
});
elements.code.value = examples.hello;
elements['example-note'].textContent = exampleNotes.hello;

try {
  const response = await fetch(new URL('./runtimes.json', import.meta.url), { cache: 'no-cache' });
  if (!response.ok) throw new Error('HTTP ' + response.status);
  const catalog = await response.json();
  if (catalog.schemaVersion !== 1 || !Array.isArray(catalog.runtimes)) throw new Error('Unsupported runtime catalog');
  const localResponse = await fetch(new URL('./runtimes.local.json', import.meta.url), { cache: 'no-cache' });
  let localRuntimes = [];
  if (localResponse.ok) {
    const localCatalog = await localResponse.json();
    if (localCatalog.schemaVersion !== 1 || !Array.isArray(localCatalog.runtimes)) throw new Error('Unsupported local runtime catalog');
    localRuntimes = localCatalog.runtimes;
  } else if (localResponse.status !== 404) {
    throw new Error('Local runtime catalog: HTTP ' + localResponse.status);
  }
  const merged = [...new Map([...catalog.runtimes, ...localRuntimes].map(runtime => [runtime.id, runtime])).values()];
  const compareVersions = (left, right) => (left.version ?? left.label).localeCompare(
    right.version ?? right.label, 'en', { numeric: true },
  );
  const cpython = merged.filter(runtime => runtime.adapter !== 'pyodide').sort(compareVersions);
  const pyodide = merged.filter(runtime => runtime.adapter === 'pyodide').sort(compareVersions);
  runtimes = [...cpython, ...pyodide];
  elements.runtime.replaceChildren();
  for (const [label, groupRuntimes] of [['CPython — local builds', cpython], ['Pyodide — packages and browser APIs', pyodide]]) {
    if (!groupRuntimes.length) continue;
    const group = document.createElement('optgroup');
    group.label = label;
    for (const runtime of groupRuntimes) {
      const option = document.createElement('option');
      option.value = runtime.id;
      option.textContent = runtime.label + (/^\d+\.\d+\.\d+(a|b|rc)\d+$/.test(runtime.version ?? '') ? ' · prerelease' : '');
      group.append(option);
    }
    elements.runtime.append(group);
  }
  const stable = cpython.filter(runtime => /^\d+\.\d+\.\d+$/.test(runtime.version ?? ''));
  const preferred = stable.at(-1) ?? cpython.at(-1) ?? pyodide[0];
  if (preferred) elements.runtime.value = preferred.id;
  elements['runtime-count'].textContent = runtimes.length + ' available runtime' + (runtimes.length === 1 ? '' : 's');
  setRunning(false);
  if (runtimes.length) {
    elements.status.textContent = 'Ready. The first run downloads the selected runtime.';
    await describeRuntime();
  } else {
    const option = document.createElement('option');
    option.textContent = 'No runtimes published yet';
    elements.runtime.append(option);
    elements.status.textContent = 'No runtimes available. Build and import artifacts to enable execution.';
    elements['runtime-description'].textContent = 'The playground is ready, but this checkout does not contain any registered Python builds.';
    renderCapabilities();
  }
} catch (error) {
  elements.runtime.replaceChildren(new Option('Runtime catalog unavailable'));
  elements['runtime-count'].textContent = 'Catalog unavailable';
  elements.status.textContent = 'Could not load the runtime catalog: ' + error.message;
  elements['runtime-description'].textContent = 'Serve this directory over HTTP. A file:// URL cannot load module workers.';
  renderCapabilities();
}
