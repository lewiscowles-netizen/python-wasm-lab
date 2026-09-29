# Appendix: source provenance

This reference identifies upstream material used during development, verified on 2026-09-29. Downloaded source trees, source archives, generated output and local dependency checkouts are excluded from this repository's versioned files. Handwritten build scripts, patches, source pins and curated evidence remain tracked.

## Git checkouts

| Former local path | Repository | Recorded commit |
| --- | --- | --- |
| `cpython-modern/` | [CPython](https://github.com/python/cpython) | [`435c9e5a798c99653e3ab64ce29baed0e4f3dfee`](https://github.com/python/cpython/commit/435c9e5a798c99653e3ab64ce29baed0e4f3dfee) |
| `pyenv/` | [pyenv](https://github.com/pyenv/pyenv) | [`699e27fb27b465bcd3226e8192bb635ce90eecb0`](https://github.com/pyenv/pyenv/commit/699e27fb27b465bcd3226e8192bb635ce90eecb0) |
| `legacy/python-emscripten/` | [Python Emscripten port](https://github.com/python-emscripten/python) | [`b8f7eafbb238e150f2f2e032b10d362d83b2aed6`](https://github.com/python-emscripten/python/commit/b8f7eafbb238e150f2f2e032b10d362d83b2aed6) |
| `legacy/branch27/` | [Python-only builder](https://github.com/lewiscowles-netizen/python-wasm-builder) | [`809b8a526878f834c224d1289d8af78d55e4696c`](https://github.com/lewiscowles-netizen/python-wasm-builder/commit/809b8a526878f834c224d1289d8af78d55e4696c) |
| `legacy/branch30_33/` | [Python-only builder](https://github.com/lewiscowles-netizen/python-wasm-builder) | [`c3ebd315276c4aca6c0c64127b870eadfa3fa365`](https://github.com/lewiscowles-netizen/python-wasm-builder/commit/c3ebd315276c4aca6c0c64127b870eadfa3fa365) |

These were local Git checkouts or worktrees, not configured submodules. The builder's [recipe lock](https://github.com/lewiscowles-netizen/python-wasm-builder/blob/ce8b58b131eec715ad7380688508c5bc9bf27905/recipes.lock.json) records all five compiler-family commits. The CPython research checkout above is not the source identity of every built interpreter.

## Release archives and copied reference files

The [source provenance record](docs/reference/source-provenance.json) lists exact download addresses, 256-bit Secure Hash Algorithm (SHA-256) checksums, official release-tag commits and original upstream paths. Release archives are identified by their checksums; a tag commit is a source-history reference, not a claim that an archive is identical to a Git checkout.

| Removed copy | Upstream identity |
| --- | --- |
| `legacy/Python-*` archives and extracted directories | Official Python 2.7.18, 3.0.1, 3.1.5, 3.2.6 and 3.3.7 release downloads |
| `Makefile-3.13.in`, `configure-3.13.ac` | CPython 3.13.15, `Makefile.pre.in` and `configure.ac` |
| `transitional/posixmodule-3.10.c` | CPython 3.10.21, `Modules/posixmodule.c` |
| `transitional/source-reference-3.4-pythonrun.c` | CPython 3.4.10, `Python/pythonrun.c` |
| `transitional/source-reference-3.6-{object,pylifecycle}.c` | CPython 3.6.15, `Objects/object.c` and `Python/pylifecycle.c` |
| `legacy/pyenv-definitions/` and its listing | `plugins/python-build/share/python-build/` at the pyenv commit above |

All five extracted trees and six standalone CPython references matched their upstream bytes. No local edits were hidden in those copies. The early 3.0.1 investigation used a `.tar.bz2` archive; the final builder locks a different `.tgz` archive. Both identities are kept distinct. The [builder source lock](https://github.com/lewiscowles-netizen/python-wasm-builder/blob/ce8b58b131eec715ad7380688508c5bc9bf27905/versions.json) is authoritative for final builds.

## Patches and generated artifacts

The two retained `legacy/patches/python2-*.patch` files and their license match the Python Emscripten port commit above. Their presence is intentional source, not a downloaded working tree.

`legacy/dist/`, `transitional/dist/`, `mid-modern/builds/`, configuration exports, logs, bytecode and temporary commit messages are generated investigation material, not upstream dependencies. The [validation reference](docs/reference/validation.md) owns retained results; the [rebuild guide](docs/how-to/rebuild.md) describes artifact regeneration.

## Edge investigation

The [edge source ledger](docs/reference/edge-sources.json) records platform documentation and pinned interface/runtime source revisions. The [Cloudflare lab reference](docs/reference/cloudflare-edge-lab.md) identifies its dependency locks; the [WASI lab reference](docs/reference/wasi-edge-lab.md) identifies its toolchain archive checksums and source commit. Those generated tools and dependency trees are ignored locally.
