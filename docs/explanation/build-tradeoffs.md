# Why the builder has separate recipe families

Historical CPython releases disagree about configure probes, generated files, interpreter internals and linking. Five branches keep those differences with the releases they serve, while a common artifact contract lets the browser consume their outputs. The builder's [recipe lock](https://github.com/lewiscowles-netizen/python-wasm-builder/blob/feat/python-modern-wasm/recipes.lock.json) selects immutable commits; branch names remain convenient development labels.

| Family | Reason for separation |
| --- | --- |
| Legacy: Python 2.7 | Historical port patches and Python 2 behavior. |
| Early Python 3: 3.0–3.3 | Older configure systems and changing startup metadata. |
| Transitional: 3.4–3.10 | Browser adaptations before upstream WebAssembly support. |
| Earlier upstream support: 3.11–3.13 | Earlier upstream build helpers and linking conventions. |
| Modern: 3.14–3.15 | Current upstream helper layout and call trampolines. |

The [runtime reference](../reference/runtimes.md) owns exact releases and measurements. The [rebuild guide](../how-to/rebuild.md) owns commands. The builder's [replay script](https://github.com/lewiscowles-netizen/python-wasm-builder/blob/feat/python-modern-wasm/scripts/build-all.py) checks that each pinned recipe agrees with the shared source lock before building.

## Build machines and target machines differ

Docker chooses the Linux environment that runs the compiler. Emscripten chooses the WebAssembly target. The two oldest families use the Emscripten software development kit (SDK) 2.0.2 image for amd64, which requires emulation on an arm64 Docker host. Later families use SDK 5.0.3 without forcing amd64, allowing a native container architecture on supported hosts. Both produce wasm32 interpreters.

The upstream-support families first build a native Python from the same release to generate target build inputs. That executable stays in the build environment. Older profiles reuse release-generated grammar, syntax-tree and import data, with a failing build-Python sentinel guarding against accidental regeneration. Their static-library path therefore avoids a native historical interpreter. The [modern Dockerfile](https://github.com/lewiscowles-netizen/python-wasm-builder/blob/b52814de00d1774e76191e7b1ee60f0f72154e95/Dockerfile) and [early-family porting record](https://github.com/lewiscowles-netizen/python-wasm-builder/blob/c3ebd315276c4aca6c0c64127b870eadfa3fa365/PORTING.md) show these choices.

## Compatibility requires specific repairs

Cross-compilation needs target answers to configure probes that would otherwise execute a test program. Legacy recipes also rename a private C helper that collides with musl, guard thread-only diagnostic calls, supply Python 3.2's installed configuration files, and remove references to obsolete signal objects. WebAssembly's strict indirect-call signatures require legacy function-pointer emulation and corrections to mismatched C declarations in transitional releases. These repairs support the selected profile; they do not certify the complete CPython regression suite.

The local profiles link selected C extensions statically and disable dynamic extension loading, process creation and Python threads. A packaged Python module still needs its compiled dependencies and host services. Compatible dynamic extensions require a matching application binary interface and loader. The package implications belong in [packages and applications](packages-and-applications.md).

## Size and reproducibility need qualified claims

Interpreter bytes and complete-bundle bytes measure different things. Recipes differ in linked modules, compiler settings, loader code, standard-library contents and packaging layout. The recorded sizes are not a controlled experiment isolating these variables, so a size difference cannot establish that a Python release or SDK change alone caused it.

Source checksums, SDK image digests, recipe commits, fixed timestamps and artifact hashes make builds auditable. Some newer Dockerfiles still install unpinned packages through `apt`, and independent clean builds have not established byte-for-byte reproduction. Cache success demonstrates a working build path, not that stronger property. The [validation reference](../reference/validation.md) defines the evidence boundary.
