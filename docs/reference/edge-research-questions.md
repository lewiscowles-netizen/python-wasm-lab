# Edge research questions and evidence limits

This reference separates the questions answered by our local fixtures from questions requiring further experiments. It is a research agenda, not a claim of original research or production certification. The [reading list](edge-reading.md) connects each area to primary literature.

## Available evidence

| Record | Establishes | Does not establish |
| --- | --- | --- |
| [Cloudflare lab](cloudflare-edge-lab.md) | Named application paths in a pinned local Worker runtime; dry-run packaging | Account acceptance, global deployment, production tenant isolation or billing |
| [WASI lab](wasi-edge-lab.md) | A Python component runs on the recorded native host; a specific grant changes a file operation | Same binary works on every edge host or every Python package works |
| [Core isolation lab](isolation-lab.md) | Eleven controlled memory, linking and budget outcomes | Absence of runtime bugs, side channels or host resource exhaustion |
| [Existing browser validation](validation.md) | Recorded Emscripten/Pyodide examples across selected interpreters | WASI support for the historical Python version matrix |

“WASI” means WebAssembly System Interface. “Local” identifies the tested environment, not an estimate of a managed service's behaviour.

## Falsifiable follow-on questions

| Question | Controlled comparison | Evidence that would change the conclusion |
| --- | --- | --- |
| Does a narrow adapter reduce provider coupling? | Keep domain tests fixed; replace Cloudflare adapter with a compatible component adapter | Domain rules require provider-specific changes or semantics diverge |
| Is the emitted component portable? | Run the identical hash on a second host implementing every required interface | Missing imports, different error behaviour or lifecycle assumptions |
| What does a component boundary cost? | Vary bytes and call count independently against the same computation in-process | Conversion, allocation or scheduling dominates useful work |
| Does fresh instantiation prevent request-state leakage? | Alternate synthetic tenant markers under fresh and reused policies | A marker appears in the wrong request or external resource |
| Does least authority reduce reachable operations? | Remove one grant at a time while holding artifact and inputs fixed | A denied operation remains reachable through another host interface |
| Do quotas bound total resource use? | Separately stress bounded guest computation, host transfers and handle counts | Process memory, queues or host work escape the guest budget |
| Does native async improve composition? | Compare equivalent interface chains on pinned 0.2 and 0.3 toolchains | Wake-ups, cancellation or throughput differ from the proposed mechanism |

These are proposed studies. No comparative latency, efficiency or side-channel result is asserted by the functional fixtures.

## Standards of evidence

For each study, preserve inputs, interface versions, configuration, artifact hashes, raw observations and a reproducible harness. Specify the threat model or performance hypothesis before running. Include negative cases, repeats and uncertainty; a single successful request is not a distribution.

Separate semantic claims from implementation and deployment claims. A formal language property assumes an implementation that respects it. A patched runtime still depends on its embedder and host services. A local compatibility test does not inherit a cloud provider's operational guarantees.

The [measurement procedure](../how-to/measure-edge-app.md) and [capability audit](../how-to/audit-edge-capabilities.md) define repeatable starting methods. A useful discussion can then challenge a specific assumption, reproduce a result or propose a discriminating experiment.
