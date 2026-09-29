# Audit an edge application's capabilities and budgets

Start with a specific guest artifact and host configuration. State whether the guest is trusted application code, an untrusted dependency or a hostile tenant. Use [the isolation explanation](../explanation/isolation-guarantees.md) to distinguish the claims you need to test.

## Inventory authority before running

Inspect every import and configured service binding. For each, record the implementing host/provider, accessible objects, allowed operations and who grants them. For WebAssembly System Interface (WASI), include preopened directories, environment variables, clocks, randomness, sockets and outgoing Hypertext Transfer Protocol (HTTP).

A broad interface name does not tell you its runtime policy. A host can implement an interface while denying a particular operation. Conversely, a narrow-looking function can delegate broad authority if it accepts arbitrary paths, destinations or queries.

| Capability | Evidence to collect |
| --- | --- |
| Files | Exact mapped path, permissions, outside-path and symlink behaviour |
| Network | Destinations, name resolution, redirects, proxy policy and actual requests |
| Identity | Which principal each operation represents; tenant scoping and secret injection |
| Persistence | Ownership, transaction/retry semantics and cleanup |
| Environment | Explicit names and values passed, without recording secret contents |

## Start with no grant, then add one

Replay the [WASI lab](../tutorials/wasi-edge.md) without its data preopen, then with the single intended directory. Keep the artifact and input unchanged. Record the guest failure, successful result and exact configuration difference.

For your application, repeat this paired test for each necessary capability. Probe an adjacent denied operation too: a sibling path, disallowed service or another tenant's key. Ensure the host or policy actually denied it; a missing test fixture, unexecuted branch or application-generated 403 is insufficient evidence by itself.

Avoid inherited environment and broad filesystem/network grants as a debugging shortcut. Add the smallest missing resource and rerun the failing operation. For offline deployments, distinguish denied internet access from permitted internal service requests using the [network verification guide](verify-no-egress.md).

## Bound both sides of the call

Configure guest memory and execution limits, then bound host handles, transfer sizes, request bodies, buffering and concurrency. In the pinned Wasmtime command-line interface, relevant controls include `-W fuel`, `-W max-memory-size`, `-W timeout`, `-S max-resources` and `-S hostcall-fuel`; consult that version's `-W help-long` and `-S help-long` for semantics.

Do not treat guest fuel as a wall-clock or host-work limit. Use independent deadlines for external operations, and observe whether cancellation reaches them. Verify a bounded runaway computation using the [isolation lab](../tutorials/isolation-boundaries.md). Do not run uncontrolled exhaustion tests against shared production infrastructure.

## Record the residual assumptions

Record runtime/toolchain versions and applicable security fixes, the trusted host code, instance-reuse policy and external-service assumptions. Check that one tenant's mutable state is not reused as another's authority. Test restart and error cleanup.

Keep a capability manifest beside the deployment configuration and require review when grants expand. A successful denial test validates that case; it is not a penetration test or proof against runtime exploits and side channels. The [research sources](../reference/edge-reading.md) identify those wider questions.
