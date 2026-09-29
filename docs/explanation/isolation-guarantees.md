# What an isolate or Wasm sandbox actually isolates

“Isolated” needs an object and an adversary: a request from stale state, a plugin from application memory, a tenant from another tenant, or a service from unauthorised filesystem access. These are different claims. No successful hello-world test establishes all of them.

## Separate the enforcement layers

| Layer | Mechanism | Remaining responsibility |
| --- | --- | --- |
| Core WebAssembly (Wasm) | Typed control flow and checked linear-memory access | In-bounds corruption, guest logic and explicit sharing |
| Component interfaces | Typed values, resource identity and lifetime rules | Correct meanings, bounded data and authority behind imported operations |
| WebAssembly System Interface (WASI) host | Granted resources and host policy | Correct grant configuration and host implementation |
| Runtime scheduling | Fuel, deadlines, memory/resource limits | Blocking host work, queues, aggregate load and cancellation |
| Process/machine boundary | Operating-system and hardware protections | Patching, side channels and deployment policy |
| Application | Authentication, authorisation, tenant keys and transactions | Must remain correct inside any runtime |

Wasmtime's [security model](https://docs.wasmtime.dev/security.html) describes module memory boundaries and imported host access. The [isolation tutorial](../tutorials/isolation-boundaries.md) demonstrates those limited properties, including an in-bounds overwrite that remains legal.

## An isolate is not a request

A reused interpreter may retain globals, caches and resources across requests. A fresh instance can remove some state channels at a startup cost, while shared external stores remain shared. Request-local state belongs in the handler's invocation context; persistent state needs an explicit ownership and consistency model. The edge lab references record observed lifecycle behaviour, not a universal provider promise.

V8 isolates, Wasmtime instances, processes and virtual machines have different boundaries. Cloudflare's [managed security architecture](https://developers.cloudflare.com/workers/reference/security-model/) combines mechanisms around V8. The [workerd project](https://github.com/cloudflare/workerd/blob/ab1b3926727b2fdc1f104d99eef93a878a93f665/README.md) explicitly cautions that workerd alone is insufficient for safely hosting malicious workers. Running its local development server does not reproduce the managed service's protection system.

## Resource isolation extends beyond guest memory

A guest can request expensive work through an otherwise legitimate import. Limits on linear memory do not account for every buffer, handle or allocation created by the host. Wasmtime's [2026 resource-exhaustion advisory](https://github.com/bytecodealliance/wasmtime/security/advisories/GHSA-852m-cvvp-9p4w) is a concrete example: mitigation required limits on host resources and transfers, not merely valid Wasm instructions.

Fuel limits instrumented guest execution; host calls need their own deadlines and allocation budgets. A timeout must define whether it stops waiting, interrupts computation, cancels a host operation or terminates an instance. None of these implies rollback of an external write. [Wasmtime interruption mechanisms](https://docs.wasmtime.dev/examples-interrupting-wasm.html).

## Architectural isolation is not a side-channel proof

Speculative execution can expose information outside the ordinary language execution model. [Swivel](https://www.usenix.org/conference/usenixsecurity21/presentation/narayan) studies compiler/runtime hardening. The [2026 Remote-Timer-as-a-Service preprint](https://arxiv.org/abs/2608.17043) reports a historical production attack and coordinated mitigations; [Cloudflare's disclosure](https://blog.cloudflare.com/revisiting-spectre-attacks-on-workers/) states that the presented attack is mitigated. Neither our smoke tests nor that mitigation establishes immunity to every future attack.

The defensible claim is a documented threat model, specified mechanisms, negative tests and remaining assumptions. Use [the capability audit](../how-to/audit-edge-capabilities.md) to make that claim reviewable, and [the reading list](../reference/edge-reading.md) to examine its foundations.
