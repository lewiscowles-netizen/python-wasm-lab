const { defineConfig } = require('@playwright/test');

const port = process.env.PYTHON_WASM_PORT || '8129';

module.exports = defineConfig({
  testDir: './tests',
  testMatch: 'python-wasm.spec.js',
  workers: 2,
  use: {
    baseURL: `http://127.0.0.1:${port}`,
    browserName: 'chromium',
    trace: 'retain-on-failure',
  },
  webServer: {
    command: `python3 serve.py --port ${port}`,
    url: `http://127.0.0.1:${port}/experiments/wasm/python/`,
    reuseExistingServer: true,
  },
});
