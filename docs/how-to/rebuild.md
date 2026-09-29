# Rebuild the interpreters

Use the adjacent `python-wasm-builder` checkout with Git, Python 3, a running Docker engine and Docker Buildx. Make the five recipe histories available locally before starting. Builds need access to their pinned source archives, container images and build dependencies; older recipes also need a builder capable of running Linux/amd64 images.

## Inspect the replay plan

From the lab repository root, enter the builder and select its coordinator branch:

```sh
cd ../python-wasm-builder
git switch feat/python-modern-wasm
docker buildx version
python3 scripts/build-all.py --series 2.7 3.15 --parallel 2 --print
```

Inspect the selected versions, source hashes and recipe commits. This dry run checks the local Git objects and source locks without building containers. It does not establish that an image can be downloaded or that an interpreter runs.

The coordinator replays the five immutable recipe commits recorded in `recipes.lock.json`, using detached worktrees. Keep the locked commits and matching source pins together; see [build tradeoffs](../explanation/build-tradeoffs.md) for the family design.

## Build the selected versions

Remove `--print` to execute the plan:

```sh
python3 scripts/build-all.py --series 2.7 3.15 --parallel 2
```

To rebuild every locked interpreter instead, omit `--series`:

```sh
python3 scripts/build-all.py --parallel 2
```

Add `--jobs 2` if you need to limit compiler jobs within each interpreter build. `--parallel` limits the number of interpreters built concurrently. Otherwise the pinned family settings choose compiler parallelism.

Check `builds/build-results.json` and the per-version files in `builds/logs/`. Require a passed result for each requested version before proceeding.

## Import and verify

Return to the lab and import the completed output:

```sh
cd ../python-wasm-lab
python3 scripts/import-runtimes.py
```

The importer runs the validating exporter. Then follow [Run the browser tests](test.md) against the newly imported artifacts. A completed container build and its Node.js smoke checks do not replace browser execution. Use the [validation reference](../reference/validation.md) when recording new results or checking whether older evidence matches the rebuilt bytes.

## Resolve build failures

- If a locked commit cannot be resolved, obtain the missing builder history and repeat the dry run.
- If a replay worktree has edits or a different commit, inspect that checkout and resolve the mismatch before retrying; the coordinator refuses to overwrite it.
- If an image pull or source download fails, restore access to the pinned input before retrying. Do not treat its version entry as a successful build.
- For a compiler failure, start with that version's log rather than changing the shared source lock.
