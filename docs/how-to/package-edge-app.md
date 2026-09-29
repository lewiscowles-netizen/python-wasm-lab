# Package a Python application for a chosen edge host

Choose a supported host contract before choosing a file extension. Use the dated [platform matrix](../reference/edge-platforms.md) and [WASI interface reference](../reference/wasi-interfaces.md); the latter expands WebAssembly System Interface (WASI) and names the relevant versions.

## Extract one useful operation

Choose a route-independent function with deterministic inputs and outputs. Keep its validation and domain rules in a normal Python package. Introduce explicit interfaces for storage, time, randomness and external services that affect results. Use fixtures first, following [complexity isolation](../explanation/complexity-isolation.md).

Inventory Python-version requirements, native extensions, package data, dynamic imports, threads, processes and networking. Test required operations rather than importability alone. Identify which features must move behind a host service. The browser [project-import guide](import-project.md) supplies an inventory approach, but its archive loader is not an edge deployment format.

## Select and pin one adapter

For Cloudflare's Python entrypoint, start with the [local Worker tutorial](../tutorials/cloudflare-edge.md). Pin its package resolver, development tools, compatibility date and dependencies; measure the actual interpreter supplied by the runtime.

For a standard component interface, use the [WASI component tutorial](../tutorials/wasi-edge.md). Pin the component builder, interpreter, interface definitions and host together. Keep generated bindings out of source control when they are deterministically regenerated from pinned inputs; retain the source and generation procedure.

A current interpreter in either path does not port our historical CPython builds. Preserve version-family differences in the separate builder rather than claiming all browser artifacts meet the new host contract.

## Assemble and inspect the artifact

Package source, compatible dependencies, data and the chosen request adapter. Treat build-time imports carefully: snapshotting or preinitialisation may run application code during packaging. Do not load request-specific secrets or make environment-dependent service calls at import time.

Record the fields in the [packaging reference](../reference/wasi-interfaces.md#packaging-record-fields). For components, inspect actual imports and exports with the pinned toolchain. Record raw component bytes separately from archive size and from any platform-supplied interpreter. Publish generated binaries to an artifact store with checksums and provenance rather than adding vendor trees to Git.

Using a container for the build is optional. If you use Docker Buildx, lock image digests and all downloaded inputs, export the component as an artifact, then run it with the selected host. A Dockerfile alone does not make network-dependent builds reproducible or create a production container requirement.

## Verify the whole contract

Run valid and invalid requests, a missing route, a dependency/data lookup, denied capability access and exhausted resource budgets. Compare state across requests and restart. Test cancellation around external writes using an idempotent fixture. Audit grants with [the capability procedure](audit-edge-capabilities.md).

Retain source/artifact hashes, commands, host versions and expected failures. Local development success establishes local behaviour. A provider deployment additionally needs its account configuration, accepted artifact, service bindings, limits and production tests; the checked-in labs do not claim that deployment.

Finally, measure representative workloads using [the evaluation procedure](measure-edge-app.md). Promote the exact validated artifact through your normal release process, preserving its configuration and a rollback path. Do not rebuild an unpinned replacement between validation and release.
