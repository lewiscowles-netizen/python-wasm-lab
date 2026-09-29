# CPython WebAssembly builder

Read the [technical teardown with diagrams](docs/pyodide-teardown.md) and the
[live progress and compatibility log](docs/PROGRESS.md).

This directory applies the repository's PHP pattern—Docker Buildx, a small
JavaScript entry point, and local artifact export—to CPython. The existing PHP
builder remains independently usable. Python compatibility work is split into
family branches so historical configure systems and modern build helpers do not
accumulate in one conditional Dockerfile.

## Build

```sh
python3 python/scripts/build.py 3.15
python3 python/scripts/build.py 3.14 3.15 --jobs 2
python3 python/scripts/build.py 3.14 3.15 --print
```

The command feeds a pinned target matrix to `docker buildx bake`. The output is
`python/builds/build-<exact-version>/`. Each build compiles a native CPython from
the same source as the target CPython, then cross-compiles the interpreter with
Emscripten. Native Python is a build tool; the shipped interpreter is WebAssembly.

The modern image is pinned by digest. Source URLs and SHA-256 hashes come from
the recorded pyenv commit in `versions.json`; pyenv's native installer itself
does not supply a Wasm port. The registry includes the requested 2.7 and every
3.x minor through 3.15, with validation kept separate from source availability.
3.15.0rc2 is a release candidate, not the final 3.15 release.

## Artifact contract

- `python.mjs`: default-exported Emscripten factory.
- `python.wasm`: genuine wasm32 binary.
- `python.data`: preloaded virtual filesystem, including that interpreter's
  standard library, packaged from source without foreign-version bytecode.
- `manifest.json`: exact source, compiler identity, file hashes, declared
  capabilities, and measured Node smoke output.
- `smoke.json`: actual `sys.version`, import probes, arithmetic, JSON, regex,
  and virtual filesystem checks.
- `CPYTHON-LICENSE.txt`: license accompanying the distributed interpreter.

Use `await createPython({noInitialRun: true, print, printErr})`, then
`module.callMain(['-c', source])`. Create a fresh module worker per run. Files are
ephemeral MEMFS; persistence requires an explicit adapter. Threading and dynamic
extension loading are disabled in this initial profile. Package installation is
not implied by CPython being available: pip, Pyodide's micropip, JS FFI, and a
compatible wheel index are separate features.

## Reproducibility boundary

The source hashes, Emscripten image digest, deterministic stdlib archive,
fixed source epoch, and artifact hashes make inputs and outputs auditable.
The apt repository still resolves current host build-tool packages; no claim of
byte-for-byte repeatability across time or host architectures is made until
independent clean rebuilds are compared. Preserve all three runtime files from
the same build, together with its manifest. Do not combine runtime and data
files across versions.

Build success requires executing the generated Wasm in Node. Browser status is
recorded separately after running the exported artifact in the site playground.
