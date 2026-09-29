# Python WebAssembly lab

A browser playground for comparing CPython releases and Pyodide, with editable examples, interpreter diagnostics and separate output streams. This repository owns the playground; the separate [Python-only builder](https://github.com/lewiscowles-netizen/python-wasm-builder) owns compilation and version-family recipes.

## Documentation

| You need | Read |
| --- | --- |
| Start the playground | [Run the lab](docs/how-to/run-lab.md) |
| Learn by trying examples | [Compare two Python interpreters](experiments/wasm/python/LAB-NOTES.md) |
| Check versions and available modules | [Runtime compatibility reference](docs/reference/runtimes.md) |
| Understand the controls and worker messages | [Playground interface](experiments/wasm/python/README.md) |
| Choose between runtime approaches | [Runtime alternatives](docs/explanation/runtime-alternatives.md) |
| Understand package and application support | [Packages and applications](docs/explanation/packages-and-applications.md) |
| Rebuild, verify or deploy | [Documentation index](docs/README.md) |
| Assess what has actually passed | [Validation reference](docs/reference/validation.md) |
| Identify upstream sources and commits | [Source provenance appendix](appendix.md) |

The documents follow the writing preferences in [AGENTS.md](AGENTS.md): each has one purpose, facts have one home, and explanations are separate from procedures and interface details.

## Repository map

| Path | Responsibility |
| --- | --- |
| `experiments/wasm/python/` | Active browser application, runtime adapters and examples |
| `scripts/import-runtimes.py` | Bridge to the builder's artifact exporter |
| `serve.py` | Local static server |
| `tests/`, `playwright.config.cjs` | Browser acceptance checks |
| `docs/` | Current documentation and standalone validation evidence |
| `research/`, `legacy/`, `transitional/`, `mid-modern/`, `initial-builder-staging/` | Preserved investigation history |
| `appendix.md` | Provenance of upstream sources, with immutable commits and archive checksums |

Historical research contains earlier assumptions and build attempts. Downloaded sources and generated research output are ignored local files; their provenance is recorded in the appendix. Use the current documentation and the builder's locked recipes for repeatable work. Generated runtime bundles are covered by the [artifact contract](docs/reference/artifacts.md) and [publishing guide](docs/how-to/publish.md).
