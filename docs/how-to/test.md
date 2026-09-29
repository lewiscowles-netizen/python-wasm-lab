# Run the browser tests

Use Node.js 20 or later, Yarn Classic 1 and Python 3. First [import the completed runtimes](run-lab.md#import-completed-builds) you intend to test; discovery follows the merged catalogs, so a clean clone cannot validate absent local interpreters.

## Install the test tools

From the lab repository root, preserve the locked dependency versions and install their matching Chromium browser:

```sh
yarn install --frozen-lockfile --registry https://registry.npmjs.org
yarn playwright install chromium
```

These tools are needed for automated checks, not for ordinary playground use.

## Check local interpreters

Use an unused port so the suite tests this checkout independently of a lab already running on 8129:

```sh
PYTHON_WASM_PORT=8130 yarn test:e2e --reporter=line
```

Playwright starts the repository's server when needed. It reuses a server already at the chosen address, so choose another free port if that address serves a different checkout.

Review failures and skipped tests separately. The default run skips the optional Pyodide checks. Consult the [validation reference](../reference/validation.md) to distinguish the standalone result from historical full-browser results; historical totals describe the test suite that existed for that run.

## Include Pyodide and application checks

Enable the network-dependent checks explicitly:

```sh
PYTHON_WASM_TEST_PYODIDE=1 PYTHON_WASM_PORT=8130 yarn test:e2e --reporter=line
```

This also exercises Pyodide diagnostics, package loading, NumPy, Datasette and partial output. Allow access to the configured content delivery network and package hosts.

## Record and diagnose a run

Record the command, source revision, runtime hashes and results using the [validation reference](../reference/validation.md). Rerun browser acceptance after source or artifact changes; results for previous bytes do not validate a replacement bundle.

If Chromium is missing, rerun its installation command after installing the locked dependencies. If a local runtime is missing or has mismatched files, re-import its complete build. For execution failures, inspect the failing assertion and the retained trace under `test-results/`; a package download failure requires checking network access before drawing a compatibility conclusion.
