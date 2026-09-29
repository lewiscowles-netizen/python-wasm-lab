# WASI and component interface reference

Checked on **2026-09-29**. WebAssembly System Interface (WASI) versions identify host contracts, not Python releases or edge vendors. The [release registry](https://wasi.dev/releases) is the source for current standard status; [platform support](edge-platforms.md) is a separate record.

| Surface | Artifact and entrypoint | Compatibility boundary |
| --- | --- | --- |
| Core WebAssembly (Wasm) | Module with typed imports/exports and optional memories | Does not itself define files, sockets or an HTTP server |
| WASI 0.1 / Preview 1 | Usually core module importing `wasi_snapshot_preview1`; command convention includes `_start` | POSIX-inspired calls; not the component HTTP handler contract |
| WASI 0.2 / Preview 2 | Component interfaces described using Wasm Interface Type (WIT) | `wasi:cli/command` for commands; `wasi:http/proxy` for HTTP; explicit resource and stream interfaces |
| WASI 0.3 / Preview 3 | Component interfaces using native asynchronous functions, futures and streams | HTTP `service` and `middleware` worlds replace the older proxy shape; not a textual version-number substitution |
| Cloudflare Python Worker | Python entrypoint and platform package/configuration bundle | Provider-managed Pyodide integration; not evidence that arbitrary WASI components are accepted |

“HTTP” means Hypertext Transfer Protocol. A WIT **interface** groups types and functions. A **world** specifies a component's imports and exports. The **Canonical ABI**, or application binary interface, defines how those values cross the low-level boundary. A WIT **resource** has runtime-managed identity and lifetime; it is not a portable raw memory pointer. [WIT reference](https://component-model.bytecodealliance.org/design/wit.html).

## Version and linking rules

WASI 0.3.0 was released on 2026-06-11; 0.3.1 followed on 2026-08-11. The [0.3 reference](https://wasi.dev/releases/wasi-p3) identifies Wasmtime 46 as the first final-0.3 implementation and distinguishes earlier release-candidate snapshots. Many language toolchains still emit 0.2 artifacts.

An artifact can contain imports from multiple packages or versions. Record the emitted interface names, not just the requested build world or compiler's marketing label. A host must provide a compatible implementation of every required import. Version compatibility also depends on the actual linker; do not infer successful linking from semantic versioning alone.

A Preview 1 adapter can bridge certain existing module imports into a component host. It does not automatically turn a command into a request handler, supply unsupported native extensions, or translate arbitrary Emscripten imports. Compatibility needs execution evidence.

## Packaging record fields

| Field | Required content |
| --- | --- |
| Inputs | Application commit, Python/runtime version, dependency hashes and licenses |
| Toolchain | Compiler, bindings generator, adapter, host and target configuration |
| Output | Artifact hash, raw bytes and format; separate deployment archive/compressed sizes |
| Interfaces | Exported world/handler and complete required import versions |
| Grants | Preopened directories, environment, service bindings and network policy |
| Limits | Guest memory, execution budget, host resources, request/body/concurrency limits |
| Lifecycle | Initialization, per-request state, reuse, cancellation and persistence contract |
| Evidence | Host identity, test inputs/results, local/deployed status and limitations |

The [WASI lab record](wasi-edge-lab.md) and [Cloudflare lab record](cloudflare-edge-lab.md) instantiate this model. Their sizes and Python versions describe different artifacts; they are not a like-for-like platform performance comparison.
