# Edge and WASI study map

This reference maps the edge investigation to its Diátaxis documents. It extends the [Python WebAssembly learning path](learning-path.md) from browser execution to application packaging, host interfaces and isolation. Platform claims and experiments are dated **2026-09-29**.

## Start with the question

| Your question | Document | Type |
| --- | --- | --- |
| Can Python run at the edge without an application container? | [Edge packaging architecture](explanation/edge-packaging.md) | Explanation |
| Is Cloudflare's Python runtime the same thing as WASI? | [Platform contracts](reference/edge-platforms.md) | Reference |
| What do core modules, components and WASI versions mean? | [WASI interfaces](reference/wasi-interfaces.md) | Reference |
| How can I try Cloudflare's runtime without an account? | [Run a Python Worker locally](tutorials/cloudflare-edge.md) | Tutorial |
| How can I package and serve a Python component? | [Run the WASI application](tutorials/wasi-edge.md) | Tutorial |
| What does memory isolation actually do? | [Observe isolation boundaries](tutorials/isolation-boundaries.md) | Tutorial |
| What precisely do the examples accept and demonstrate? | [Cloudflare](reference/cloudflare-edge-lab.md), [WASI](reference/wasi-edge-lab.md), [core isolation](reference/isolation-lab.md) | Reference |
| How do I bring my application across? | [Package an edge application](how-to/package-edge-app.md) | How-to |
| How do I contain provider and dependency complexity? | [Complexity isolation](explanation/complexity-isolation.md) | Explanation |
| Can I pass a pointer or Python object between components? | [Pointers, values and resources](explanation/component-memory.md) | Explanation |
| Which isolation claims are defensible? | [Isolation guarantees and limits](explanation/isolation-guarantees.md) | Explanation |
| How do I inspect authority and resource limits? | [Audit capabilities and budgets](how-to/audit-edge-capabilities.md) | How-to |
| How do I evaluate cost and performance? | [Measure an edge application](how-to/measure-edge-app.md) | How-to |
| What should I read and investigate next? | [Annotated primary sources](reference/edge-reading.md), [research questions](reference/edge-research-questions.md) | Reference |

WASI expands to WebAssembly System Interface. Its precise interface contracts belong in the linked reference, separate from a vendor's deployment contract.

## Suggested study sequence

Read the packaging explanation and platform matrix first. Run the Cloudflare and WASI tutorials to observe the two application contracts. Then run the core isolation tutorial before reading the pointer and isolation explanations. Use the packaging and audit procedures on one of your own application's operations.

For a seminar or design review, bring an artifact manifest, a positive result, a controlled failure and one explicit untested assumption. Choose a question from the research reference and specify what observation would refute the proposed answer. The measurement guide describes how to collect meaningful comparative evidence.

## Scope and provenance

The [evidence matrix](reference/edge-research-questions.md#available-evidence) is the single summary of tested and untested surfaces. Local request handling, artifact creation, cloud deployment and hostile-tenant isolation are separate claims.

The [platform source ledger](reference/edge-sources.json) records primary documentation and pinned source revisions. Each lab reference links its toolchain/dependency locks and recorded source hashes. Generated runtimes, packages and vendor directories remain local ignored files; no production credentials are required by these local exercises.
