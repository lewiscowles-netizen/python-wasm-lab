const VERSION_PREFIX = '__PYTHON_WASM_VERSION__';
const OUTPUT_LIMIT = 1_000_000;
const outputEncoder = new TextEncoder();
let outputLength = 0;

function sendOutput(stream, value, appendNewline = true) {
  const text = String(value);
  if (stream === 'stdout' && text.startsWith(VERSION_PREFIX)) {
    try {
      postMessage({ type: 'version', ...JSON.parse(text.slice(VERSION_PREFIX.length)) });
      return;
    } catch {
      // An ordinary output line can happen to share the prefix.
    }
  }
  const emitted = text + (appendNewline ? '\n' : '');
  outputLength += outputEncoder.encode(emitted).byteLength;
  if (outputLength > OUTPUT_LIMIT) {
    throw new Error('Output exceeded the 1 MB limit. Execution stopped.');
  }
  postMessage({ type: 'output', stream, text: emitted });
}

function pythonBytes(source) {
  // Preserve source encoding with a UTF-8 signature and byte literal.
  const bytes = new TextEncoder().encode('\ufeff' + source.replace(/^\ufeff/, ''));
  return 'b"' + Array.from(bytes, byte => '\\x' + byte.toString(16).padStart(2, '0')).join('') + '"';
}

function versionProbe() {
  return [
    'import sys as _wasm_sys, json as _wasm_json',
    '_wasm_sys.stdout.write(' + JSON.stringify(VERSION_PREFIX) + ' + _wasm_json.dumps({"version": _wasm_sys.version, "platform": _wasm_sys.platform}) + "\\n")',
    '_wasm_sys.stdout.flush()',
  ].join('\n');
}

function wrapSource(source) {
  // Compile separately so future imports remain legal in the submitted source.
  return versionProbe() + '\n' + [
    '_wasm_source = ' + pythonBytes(source),
    'try:',
    '    exec(compile(_wasm_source, "<playground>", "exec"))',
    'except Exception:',
    '    import traceback as _wasm_traceback_module',
    '    _wasm_type, _wasm_error, _wasm_tb = _wasm_sys.exc_info()',
    '    _wasm_traceback_module.print_exception(_wasm_type, _wasm_error, _wasm_tb.tb_next)',
    '    _wasm_sys.exit(1)',
  ].join('\n');
}

async function runEmscripten(runtime, source) {
  const moduleUrl = new URL(runtime.module, runtime.baseURL);
  const artifactDirectory = new URL('.', moduleUrl);
  async function fetchArtifact(name) {
    const url = new URL(name, artifactDirectory);
    const response = await fetch(url);
    if (!response.ok) throw new Error('Could not load ' + name + ': HTTP ' + response.status);
    return response.arrayBuffer();
  }
  postMessage({ type: 'status', message: 'Downloading Python and its standard library…' });
  const [imported, wasm, data] = await Promise.all([
    import(moduleUrl.href),
    fetchArtifact(runtime.wasm ?? 'python.wasm'),
    runtime.data === false ? null : fetchArtifact(runtime.data ?? 'python.data'),
  ]);
  if (typeof imported.default !== 'function') {
    throw new Error('The runtime does not export an Emscripten module factory.');
  }
  postMessage({ type: 'status', message: 'Starting Python…' });
  let exitStatus = 0;
  const invocation = runtime.invocation ?? 'callMain';
  const options = {
    arguments: invocation === 'arguments' ? ['-c', source] : [],
    noInitialRun: invocation !== 'arguments',
    wasmBinary: new Uint8Array(wasm),
    ...(data ? { getPreloadedPackage: () => data } : {}),
    preRun: [module => {
      if (module.ENV) {
        module.ENV.PYTHON_COLORS = '0';
        module.ENV.NO_COLOR = '1';
        module.ENV.TERM = 'dumb';
      }
    }],
    locateFile: file => new URL(file, artifactDirectory).href,
    print: value => sendOutput('stdout', value),
    printErr: value => sendOutput('stderr', value),
    stdin: () => null,
    onExit: status => { exitStatus = status; },
    // Capture CLI exit status; see README.md.
    quit: (status, error) => { exitStatus = status; throw error; },
    onAbort: reason => { throw new Error('Python aborted: ' + reason); },
    onRuntimeInitialized: () => postMessage({ type: 'status', message: 'Running Python…' }),
  };
  try {
    const python = await imported.default(options);
    if (invocation === 'callMain') {
      if (typeof python.callMain !== 'function') {
        throw new Error('This build must export callMain, or declare invocation: "arguments".');
      }
      const result = python.callMain(['-c', source]);
      if (typeof result === 'number') exitStatus = result;
    } else if (invocation !== 'arguments') {
      throw new Error('Unknown Emscripten invocation: ' + invocation);
    }
  } catch (error) {
    if (error?.name === 'ExitStatus' && typeof error.status === 'number') {
      exitStatus = error.status;
    } else {
      throw error;
    }
  }
  return exitStatus;
}

async function runPyodide(runtime, source, options) {
  const moduleUrl = new URL(runtime.module, runtime.baseURL);
  const { loadPyodide } = await import(moduleUrl.href);
  const python = await loadPyodide({
    indexURL: new URL('.', moduleUrl).href,
    stdout: value => sendOutput('stdout', value),
    stderr: value => sendOutput('stderr', value),
    stdin: () => null,
  });
  python.runPython(versionProbe());
  // Use stream writers after Python initializes.
  const decoders = { stdout: new TextDecoder(), stderr: new TextDecoder() };
  const writer = stream => ({
    write(buffer) {
      const text = decoders[stream].decode(buffer, { stream: true });
      if (text) sendOutput(stream, text, false);
      return buffer.byteLength;
    },
  });
  python.setStdout(writer('stdout'));
  python.setStderr(writer('stderr'));
  if (options.autoPackages) {
    postMessage({ type: 'status', message: 'Loading packages found in imports…' });
    await python.loadPackagesFromImports(source);
  }
  if (options.micropip) {
    postMessage({ type: 'status', message: 'Loading micropip…' });
    await python.loadPackage('micropip');
    const micropip = python.pyimport('micropip');
    try {
      for (const requirement of options.packages) {
        postMessage({ type: 'status', message: 'Installing ' + requirement + '…' });
        await micropip.install(requirement);
      }
    } finally {
      micropip.destroy();
    }
  }
  postMessage({ type: 'status', message: 'Running Python…' });
  try {
    const result = await python.runPythonAsync(source, { filename: '<playground>' });
    result?.destroy?.();
    return 0;
  } finally {
    // Flush both streams before returning to the page.
    python.runPython('import sys as _wasm_sys\n_wasm_sys.stdout.flush()\n_wasm_sys.stderr.flush()');
    for (const [stream, decoder] of Object.entries(decoders)) {
      const remaining = decoder.decode();
      if (remaining) sendOutput(stream, remaining, false);
    }
  }
}

self.onmessage = async ({ data }) => {
  if (data.type !== 'run') return;
  try {
    let exitCode;
    if (data.runtime.adapter === 'emscripten') {
      exitCode = await runEmscripten(data.runtime, wrapSource(data.code));
    } else if (data.runtime.adapter === 'pyodide') {
      exitCode = await runPyodide(data.runtime, data.code, data.options);
    } else {
      throw new Error('Unsupported runtime adapter: ' + data.runtime.adapter);
    }
    postMessage({ type: 'done', exitCode });
  } catch (error) {
    postMessage({ type: 'error', message: error?.message ?? String(error) });
  }
};
