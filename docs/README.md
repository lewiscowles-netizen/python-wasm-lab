# Documentation index

Choose a document by the question you need answered. The types follow [Diátaxis](https://diataxis.fr/): tutorials teach, how-to guides accomplish a task, references specify interfaces, and explanations describe reasons and trade-offs.

For a structured progression, use the [Python WebAssembly learning path](learning-path.md), with a practical checkpoint at each stage.

## Tutorial

- [Compare two Python interpreters](../experiments/wasm/python/LAB-NOTES.md): learn version selection, capabilities, state lifetime and packages by running examples.
- [Call a real external service](tutorials/external-service.md): start a native service, send requests from browser Python, and inspect errors and cancellation.

## How-to guides

- [Run the lab](how-to/run-lab.md): import completed builds and start the playground.
- [Rebuild interpreters](how-to/rebuild.md): replay the builder's version-family recipes and refresh the lab.
- [Run browser checks](how-to/test.md): verify local interpreters and optional network-dependent applications.
- [Publish the playground](how-to/publish.md): stage a complete static deployment with its matching runtime files.
- [Bring in a project](how-to/import-project.md): stage multiple source files, dependencies and data, then validate an application boundary.
- [Probe Django, Flask and FastAPI](how-to/probe-frameworks.md): replay measured request handling and mock an outbound service.
- [Connect an intranet service](how-to/connect-service.md): define an operation, choose a gateway or separate origin, and verify browser access.
- [Deploy without internet access](how-to/deploy-offline.md): mirror runtimes, wheels and application assets for an internal host.
- [Debug an intranet deployment](how-to/debug-intranet.md): locate loader, package, browser-policy and application failures.
- [Check external requests](how-to/verify-no-egress.md): run a reproducible browser check with an explicit origin boundary.

## Reference

- [Runtime compatibility](reference/runtimes.md): measured versions, sizes, modules and language differences.
- [Playground interface](../experiments/wasm/python/README.md): controls, execution results and worker messages.
- [Runtime artifacts](reference/artifacts.md): catalog fields, bundles, loader expectations and import checks.
- [Validation evidence](reference/validation.md): recorded tests, matching artifacts and untested boundaries.
- [Source provenance appendix](../appendix.md): upstream repositories, immutable commits, release downloads and checksums.
- [Network dependencies](reference/network-dependencies.md): request phases, package-index behavior and measured local-hosting checks.
- [Framework support](reference/framework-support.md): measured request results, pinned dependencies and execution limits.
- [Proposed application bridge](reference/framework-bridge.md): candidate request, response and lifecycle contracts for a navigable playground.
- [External-service example](reference/external-service.md): service routes, client options, error handling and repeatable browser verification.

## Explanation

- [Architecture](explanation/architecture.md): why compilation, static hosting and disposable workers are separate.
- [Build trade-offs](explanation/build-tradeoffs.md): historical branches, host tools, module selection and reproducibility limits.
- [Runtime alternatives](explanation/runtime-alternatives.md): where CPython, Pyodide, WebAssembly hosts and other Python implementations differ.
- [Packages and applications](explanation/packages-and-applications.md): package compatibility, feature toggles and the gap between a Datasette experiment and a complete application.
- [Framework playgrounds](explanation/framework-playgrounds.md): how WordPress Playground's request-routing architecture could transfer to Python.
- [Host services](explanation/host-services.md): where local computation, browser networking and server capabilities meet.

The [writing conventions](../AGENTS.md) govern new documentation. Old research folders are retained as investigation history; they are not the current operating instructions.
