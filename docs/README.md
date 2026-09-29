# Documentation index

Choose a document by the question you need answered. The types follow [Diátaxis](https://diataxis.fr/): tutorials teach, how-to guides accomplish a task, references specify interfaces, and explanations describe reasons and trade-offs.

## Tutorial

- [Compare two Python interpreters](../experiments/wasm/python/LAB-NOTES.md): learn version selection, capabilities, state lifetime and packages by running examples.

## How-to guides

- [Run the lab](how-to/run-lab.md): import completed builds and start the playground.
- [Rebuild interpreters](how-to/rebuild.md): replay the builder's version-family recipes and refresh the lab.
- [Run browser checks](how-to/test.md): verify local interpreters and optional network-dependent applications.
- [Publish the playground](how-to/publish.md): stage a complete static deployment with its matching runtime files.

## Reference

- [Runtime compatibility](reference/runtimes.md): measured versions, sizes, modules and language differences.
- [Playground interface](../experiments/wasm/python/README.md): controls, execution results and worker messages.
- [Runtime artifacts](reference/artifacts.md): catalog fields, bundles, loader expectations and import checks.
- [Validation evidence](reference/validation.md): recorded tests, matching artifacts and untested boundaries.
- [Source provenance appendix](../appendix.md): upstream repositories, immutable commits, release downloads and checksums.

## Explanation

- [Architecture](explanation/architecture.md): why compilation, static hosting and disposable workers are separate.
- [Build trade-offs](explanation/build-tradeoffs.md): historical branches, host tools, module selection and reproducibility limits.
- [Runtime alternatives](explanation/runtime-alternatives.md): where CPython, Pyodide, WebAssembly hosts and other Python implementations differ.
- [Packages and applications](explanation/packages-and-applications.md): package compatibility, feature toggles and the gap between a Datasette experiment and a complete application.

The [writing conventions](../AGENTS.md) govern new documentation. Old research folders are retained as investigation history; they are not the current operating instructions.
