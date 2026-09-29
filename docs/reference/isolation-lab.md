# Core Wasm isolation lab reference

This native command-line lab exercises core WebAssembly (Wasm) modules. It does not load Python into Wasm or use WebAssembly System Interface (WASI) imports. Native Python orchestrates the checks; the [Python WASI application lab](wasi-edge-lab.md) covers the higher-level application contract.

## Inputs and invocation

| Input | Contract |
| --- | --- |
| [Checker](../../scripts/check-isolation.py) | Python 3.9+ standard library |
| `--wasmtime` | Required path to a Wasmtime 49.0.1 executable |
| `--output` | Optional JavaScript Object Notation (JSON) results path; default ignored `test-results/isolation.json` |
| [`memory.wat`](../examples/isolation/memory.wat) | One initial 64-KiB page, at most two pages; initial bytes 42 and 43 |
| [`instances.wat`](../examples/isolation/instances.wat) | Imports functions from two separately instantiated copies of the memory module |
| [`consumer.wat`](../examples/isolation/consumer.wat) | Imports `catalog.price: (i32) → i32` |
| [`catalog.wat`](../examples/isolation/catalog.wat) | Pure arithmetic provider: quantity × 125 |
| [`wrong-catalog.wat`](../examples/isolation/wrong-catalog.wat) | Deliberately incompatible `(i64) → i32` provider |

WAT means WebAssembly text format; KiB means 1,024 bytes. The source files are handwritten, small and tracked. Wasmtime parses/compiles them during each invocation. The checker disables WASI command-line interface (CLI) support with `-S cli=n` and applies a ten-second outer timeout to each command.

## Observed cases

| Case | Expected observation |
| --- | --- |
| Read byte 0 | 42 |
| Read byte 65,535 | 0 |
| Read byte 65,536 | Out-of-bounds memory trap |
| Overwrite the neighbouring in-bounds byte | 99; no object-level protection |
| Grow memory without a host cap | Returns previous page count 1 |
| Grow with `max-memory-size=65536` | Returns −1; growth refused |
| Run infinite loop with `fuel=1000` | Fuel exhaustion trap |
| Omit catalog provider | Unknown-import linking failure |
| Link compatible provider | Quote for two returns 250 |
| Link wrong provider signature | Incompatible-import-type failure |
| Mutate only the left instance | Left 77, right 42 |

## Evidence and limits

[Evidence recorded on 2026-09-29](../evidence/isolation-2026-09-29.json) includes source hashes, native runtime identity and all 11 outcomes. The recorded host is macOS on Apple silicon. Other supported hosts can replay the commands; this record does not claim those hosts were tested.

The provider example demonstrates explicit linking and type compatibility, not user authentication. The separate memories do not imply that explicit shared memory is impossible. Core module bounds do not enforce C object ownership or establish constant-time execution.

Fuel is an execution budget for guest instructions, not a general wall-clock budget for imported host work. A per-memory growth limit is not a complete host-process memory limit. These controls and their limitations belong to the [isolation explanation](../explanation/isolation-guarantees.md).

The [tutorial](../tutorials/isolation-boundaries.md) supplies the replay sequence. Runtime download provenance belongs to the [WASI lab](wasi-edge-lab.md); the recorded binary hash identifies the executable actually used here.
