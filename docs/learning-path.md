# Python WebAssembly learning path

This is a navigation reference for a software developer learning WebAssembly (Wasm) through the lab. Each stage links to one purpose-built document and names evidence that demonstrates understanding. You can run the exercises without an artificial intelligence assistant.

| Stage | Start here | Observable checkpoint |
| --- | --- | --- |
| 1. Run code | [Compare interpreters](../experiments/wasm/python/LAB-NOTES.md) | Run the same input on two Python versions and explain a difference |
| 2. Locate execution | [Lab architecture](explanation/architecture.md) | Identify the server, page, worker and interpreter; predict what disappears after Run |
| 3. Choose a platform | [Runtime alternatives](explanation/runtime-alternatives.md) | Explain what CPython, Pyodide, Emscripten and WASI each supply |
| 4. Inspect capabilities | [Runtime reference](reference/runtimes.md) | Separate a successful import from a working host-dependent operation |
| 5. Load an application | [Project integration](how-to/import-project.md) | Import your multi-file package and read its fixture in the selected runtime |
| 6. Resolve dependencies | [Packages and applications](explanation/packages-and-applications.md) | Identify a pure-Python dependency, a native wheel and a missing host facility |
| 7. Cross the network boundary | [External-service tutorial](tutorials/external-service.md) | Observe a real GET, preflight, POST, handled failure and cancellation |
| 8. Exercise a framework | [Framework probes](how-to/probe-frameworks.md) | Test a route and substitute a service fixture without opening a Python socket |
| 9. Design a browser application | [Framework playgrounds](explanation/framework-playgrounds.md) | Describe what the proposed resident request bridge still needs |
| 10. Deploy internally | [Closed-network deployment](how-to/deploy-offline.md) | Run from a cold browser with approved internal assets and services |
| 11. Diagnose failures | [Intranet debugging](how-to/debug-intranet.md) | Produce a minimal reproducer and identify the first failing layer |
| 12. Reproduce an interpreter | [Rebuild guide](how-to/rebuild.md) | Build one version family, verify its manifest and import its artifacts |
| 13. Defend the result | [Validation reference](reference/validation.md) | Tie a compatibility claim to exact inputs, hashes and an observed test |

“WASI” expands to WebAssembly System Interface. It is a host interface family, not another name for the browser. Platform definitions and their limitations belong in the linked runtime comparison.

## Capstone evidence

Use one of your projects to produce a small, reviewable deployment: a pinned runtime, source archive, complete compatible dependency set, deterministic fixture, real internal-service contract and browser test. Record an expected failure as well as success. Run it with an empty browser cache and the intended network restrictions. Use the [publishing guide](how-to/publish.md) and [service connection guide](how-to/connect-service.md).

Keep unsupported capabilities explicit. The current lab is a script runner; the proposed navigable framework host is additional engineering. Finishing these stages establishes practical Python/Wasm integration skills, not proof that every package or operating-system feature works.

## Beyond this lab

For compiler and runtime depth, continue with the [WebAssembly core specification](https://webassembly.github.io/spec/core/), [Emscripten porting guide](https://emscripten.org/docs/porting/), and [Pyodide package-building guide](https://pyodide.org/en/stable/development/building-packages.html). Focus on imports/exports, linear memory, application binary interfaces, filesystem integration and host calls before attempting a new native extension. The [build trade-offs](explanation/build-tradeoffs.md) connect those topics to the historical Python ports here.
