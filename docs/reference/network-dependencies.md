# Network dependency reference

This reference describes network use by the current lab. An intranet deployment still serves files over HTTP or HTTPS; “no internet egress” means those requests stay within approved internal origins. It differs from disconnecting the browser from every server.

## Requests by execution phase

| Phase | Requested resources | Current source |
| --- | --- | --- |
| Page load | HTML, styles, page controller, baseline and optional local catalogs | Lab origin |
| Runtime selection | Optional build manifest | Catalog address |
| Local CPython run | Worker, loader, `python.wasm`, `python.data` | Lab origin for imported builds |
| Pyodide startup | Worker, loader, interpreter, standard-library archive and package lock | jsDelivr in the tracked catalog; can be self-hosted |
| Automatic import loading | Recognized Pyodide packages and their dependencies | Selected Pyodide distribution |
| Micropip setup | Micropip and its distribution dependencies | Selected Pyodide distribution |
| Micropip requirements | Compatible wheels and, when resolving names, package metadata | Distribution, supplied wheel addresses or configured indexes |
| Datasette example | Requirements text followed by package installation | Lab origin for text; external package sources in the current example |
| Application execution | Project archives, datasets, models, templates or service requests | Whatever the application names |

The [worker](../../experiments/wasm/python/worker.mjs) derives Pyodide's `indexURL` from the directory containing its configured `module`. That setting locates the distribution; it is not a micropip index setting. Catalog fields and merge precedence belong to the [artifact reference](artifacts.md).

## Package controls and limits

The two checkboxes control automatic loading only. They neither prohibit application networking nor configure an internal package index. Import scanning examines the submitted editor source, not every module inside your project archive. The requirements box calls `micropip.install(requirement)` with default dependency resolution; it cannot express `deps=False` or `index_urls`. Supply those options in Python bootstrap code.

The bundled micropip 0.11.1 defaults to `https://pypi.org/simple`. Its pinned implementation accepts Python Packaging Authority index formats with HTML or JSON responses, plus legacy Python Package Index (PyPI) JSON metadata. This differs from older micropip documentation describing a JSON-only default. See [index fetching](https://github.com/pyodide/micropip/blob/70cef478300b6881c45cbf0c652a57c8c3b34e17/micropip/package_index.py); actual server response type matters.

A full Pyodide distribution contains its vendored packages, not all packages available on PyPI. A lock file or [`micropip.freeze()` output](https://github.com/pyodide/micropip/blob/70cef478300b6881c45cbf0c652a57c8c3b34e17/micropip/freeze.py) identifies artifacts but does not copy them; frozen entries can retain external addresses. A package directory also does not become an index merely by containing wheels.

## Preparation dependencies

Interpreter rebuilding additionally consumes container images, operating-system packages, compiler tools and pinned source downloads. Automated browser checks need Node.js dependencies and a Playwright browser. These preparation requirements are separate from serving completed runtime bundles. A successful browser run with blocked external requests does not prove a Docker build can run disconnected.

Use [closed-network deployment](../how-to/deploy-offline.md) to prepare artifacts, [intranet debugging](../how-to/debug-intranet.md) to locate failures, and [request checks](../how-to/verify-no-egress.md) to record evidence. The lab currently has no service worker or complete offline dependency exporter.

## Recorded checks

The [2026-09-29 evidence](../evidence/no-egress-2026-09-29.json) records local CPython 2.7/3.14 runs, a blocked external Pyodide loader, and an isolated self-hosted Pyodide worker importing a multi-file project and local wheel. These checks cover the named fixtures with HTTP interception; they do not establish complete application compatibility or network-level isolation.
