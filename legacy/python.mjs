import createCore from './python-core.mjs';

/** One isolated CPython process per factory invocation. */
export default async function createPython(options = {}) {
  let exitStatus = 0;
  const config = {
    noInitialRun: true,
    locateFile: name => new URL(name, import.meta.url).href,
    ...options,
  };
  config.quit = (status, error) => {
    exitStatus = status;
    if (options.quit) return options.quit(status, error);
    throw error;
  };
  if (typeof process === 'object' && process.versions && process.versions.node) {
    const { promises: { readFile } } = await import('fs');
    const { randomFillSync } = await import('crypto');
    if (!config.entropyProvider) config.entropyProvider = { getRandomValues: randomFillSync };
    if (!config.wasmBinary) config.wasmBinary = await readFile(new URL('./python.wasm', import.meta.url));
    if (!config.getPreloadedPackage) {
      const bytes = await readFile(new URL('./python.data', import.meta.url));
      const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
      config.getPreloadedPackage = () => data;
    }
  }
  const module = await createCore(config);
  const callMain = module.callMain;
  module.callMain = args => {
    exitStatus = 0;
    callMain(args);
    return exitStatus;
  };
  return module;
}
