# Check execution without external HTTP requests

Use a fresh automated browser context to reveal missing mirrored assets and unexpected downloads. Install the [test tools](test.md#install-the-test-tools) on the preparation machine first. Start the staged lab on an available local port or use its internal address.

## Run a controlled request check

From the lab repository root, run this with an existing runtime ID from the deployment. Change `LAB_URL` for an intranet host. The sample code is deliberately small; replace it with your application's bootstrap for application acceptance.

```sh
LAB_URL=http://127.0.0.1:8129/experiments/wasm/python/ \
LAB_RUNTIME=cpython-3.14.7 node <<'JS'
const { chromium, expect } = require('@playwright/test');

(async () => {
  const target = process.env.LAB_URL;
  const allowedOrigin = new URL(target).origin;
  const external = new Set();
  const browser = await chromium.launch();
  try {
    const context = await browser.newContext({ serviceWorkers: 'block' });
    context.on('request', request => {
      if (new URL(request.url()).origin !== allowedOrigin) external.add(request.url());
    });
    await context.route('**/*', async route => {
      const url = route.request().url();
      if (new URL(url).origin !== allowedOrigin) {
        external.add(url);
        console.error('BLOCKED', url);
        return route.abort('blockedbyclient');
      }
      const response = await route.fetch({ maxRedirects: 0 });
      if (response.status() >= 300 && response.status() < 400 && response.headers().location) {
        console.error('REDIRECT', url, response.headers().location);
        return route.abort('blockedbyclient');
      }
      return route.fulfill({ response });
    });
    context.on('requestfailed', request => {
      console.error('FAILED', request.url(), request.failure()?.errorText);
    });
    const page = await context.newPage();
    await page.goto(target);
    await page.getByLabel('Python build', { exact: true })
      .selectOption(process.env.LAB_RUNTIME);
    await page.getByLabel('Time limit', { exact: true }).selectOption('120');
    await page.getByLabel('Python source code', { exact: true }).fill(
      'from __future__ import print_function\nimport sys\nprint("INTRANET_OK", sys.version.split()[0], 6 * 7)\n'
    );
    await page.getByRole('button', { name: 'Run Python', exact: true }).click();
    await expect(page.getByRole('status')).toHaveText(
      'Finished with exit code 0.', { timeout: 125000 }
    );
    await expect(page.locator('#stdout')).toContainText('INTRANET_OK');
    if (external.size) throw new Error('External requests were attempted');
    console.log(await page.locator('#stdout').innerText());
    console.log('No external HTTP requests observed in this run.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
JS
```

This diagnostic fetches allowed responses without following redirects, then supplies them to the browser. It rejects redirects, including internal ones; use final asset addresses. Ordinary routing sees only the first address in a redirect chain. Request events provide an independent origin audit. See [routing limitations](https://playwright.dev/docs/api/class-page#page-route) and [service-worker interception](https://playwright.dev/docs/network#missing-network-events-and-service-workers). Keep exact origin comparisons; for several approved hosts, use an explicit set of complete origins.

## Exercise the intended application

Repeat for every deployed runtime and required workflow, including lazy imports, plugins, dataset loading and error recovery. For Pyodide package tests, enable the required checkbox in the script after runtime selection; the sample above leaves both off. Assert application results as well as request behavior.

As a negative control, run the unmodified internet-backed Pyodide entry: its loader request should be blocked and execution should fail. This checks that the guard observes runtime downloads. After mirroring Pyodide, the same ID should resolve to the internal loader and pass.

## Interpret the result

This checks intercepted HTTP requests for the exercised paths. It is not a firewall, a complete audit of browser traffic, a WebSocket restriction or proof that an untested feature works offline. Repeat without interception under actual network controls to test browser fetch behavior, redirects and authentication. Do not use a browser-wide offline flag when reaching an intranet host.

Record the source and artifact hashes, browser version, allowed origins, application assertions and blocked addresses with the results. Follow the [debugging guide](debug-intranet.md) for failures.
