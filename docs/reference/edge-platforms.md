# Python edge platform contracts

Status checked **2026-09-29** against primary documentation and pinned source. These are researched deployment contracts, with separately recorded local Cloudflare and Wasmtime experiments below. No remote deployment is established. The [source ledger](edge-sources.json) records the platform research revisions and evidence limits.

## Artifact and interface families

The [interface reference](wasi-interfaces.md) defines core WebAssembly (Wasm), WebAssembly System Interface (WASI) generations and components. Those contracts must match the host; a `.wasm` extension alone establishes none of them.

## Platform matrix

| Target | Application package and entrypoint | Host contract and constraints |
| --- | --- | --- |
| [Cloudflare Python Workers](https://developers.cloudflare.com/workers/languages/python/how-python-workers-work/) | Python source, `pyproject.toml` dependencies and Wrangler configuration; `Default(WorkerEntrypoint).fetch` | Platform-selected Pyodide inside a V8 isolate; `pywrangler` bundles dependencies and deployment creates a memory snapshot. This is not a generic WASI component upload. |
| [Cloudflare JavaScript/Wasm Workers](https://developers.cloudflare.com/workers/runtime-apis/webassembly/) | JavaScript entrypoint plus imported precompiled core Wasm modules | JavaScript imports supply host functions. The linked [WASI shim](https://github.com/cloudflare/workers-wasi/blob/55d7dc2374f6ccf7a863127b4635de87f920b2e0/README.md) implements partial Preview 1; this is not evidence of a native Preview 2/3 component host. |
| [Fastly Compute Python](https://github.com/fastly/compute-sdk-python/blob/2bffcc6d596a68bcc0b4342404641deff78e68f6/README.md) | SDK 0.1.3 builds `bin/main.wasm`; `fastly.toml` and Python project configuration; Web Server Gateway Interface adapter or Fastly API | Beta SDK targets `fastly:compute/service@0.1.0` and composes adapters. Third-party C extensions are unsupported; required imports must occur during snapshot construction. |
| [Spin Python](https://github.com/spinframework/spin-python-sdk/blob/a7945b83f7000936c23fe7bdc4ddea411b8059f2/README.md) | `componentize-py` builds a component; `spin.toml` defines triggers, files and permissions | Pinned SDK 5.0.0 example uses componentize-py 0.25.1 and `spin:up/http-trigger@4.1.0`, exporting `wasi:http/handler@0.3.0`. Exact host support matters. |
| [SpinKube](https://www.spinkube.dev/docs/topics/architecture/) | Spin application in an Open Container Initiative artifact; Kubernetes `SpinApp` resources | Operator and containerd Spin shim run the workload. No application Linux image is required for this route; Kubernetes/containerd remain infrastructure dependencies. The optional [Spintainer executor](https://www.spinkube.dev/docs/misc/spintainer-executor/) explicitly uses a container. |
| [Native Wasmtime lab](wasi-edge-lab.md) | Python component plus manifest; `wasmtime serve` supplies the request host | Demonstrates a compatible native host without an application container; it does not supply managed edge distribution. |

## Compatibility conditions

- Cloudflare requires `python_workers` and a compatibility date. Its [package contract](https://developers.cloudflare.com/workers/languages/python/packages/) accepts pure Python and compatible PyEmscripten packages. Its runtime selection is separate from this lab's Pyodide pin and historical CPython builds.
- Python Workers exclude operating-system facilities; threads/processes are nonfunctional and files are ephemeral. [Standard-library contract](https://developers.cloudflare.com/workers/languages/python/stdlib/). Memory, CPU and bundle restrictions remain [platform limits](https://developers.cloudflare.com/workers/platform/limits/).
- Spin 4.1 supports final WASI 0.3, its earlier release candidate and Preview 2. Some deployed hosts still require Preview 2 templates; SDK availability does not establish a managed host's support. [Release](https://spinframework.dev/blog/announcing-spin-4-1), [host compatibility guidance](https://spinframework.dev/v4/writing-apps).
- Component interfaces do not grant resources automatically. Spin's [manifest](https://spinframework.dev/v4/manifest-reference) declares outbound hosts, mounted files and storage access; Cloudflare and Fastly expose their own bindings and services.
- The lab's Emscripten [artifact contract](artifacts.md) is not any of these deployment contracts. Application source may transfer; interpreter binaries, native wheels and host adapters require separate validation.
- Standalone `workerd` does not reproduce every managed service or its security boundary; its [sandbox warning](https://github.com/cloudflare/workerd/blob/ab1b3926727b2fdc1f104d99eef93a878a93f665/README.md#L32) requires additional protection for untrusted code.

## Verification record

The [Cloudflare lab](cloudflare-edge-lab.md) records local requests and dry-run packaging. The [WASI lab](wasi-edge-lab.md) records native component execution and paired filesystem grants. Fastly, Spin and SpinKube remain researched here. All results require their exact tool/runtime, interface and configuration pins; browser results do not establish edge compatibility.
