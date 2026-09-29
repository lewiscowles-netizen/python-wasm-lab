# Observe what a Wasm boundary permits and rejects

You will run small WebAssembly (Wasm) modules and observe memory, linking and execution limits directly. These examples use native Wasmtime, without a container or cloud account. They complement the Python application labs by exposing the lower-level mechanism.

## Prepare the runtime

Use native Python 3.9+ and the Wasmtime **49.0.1** executable from the [WASI lab setup](wasi-edge.md) or the matching [official release](https://github.com/bytecodealliance/wasmtime/releases/tag/v49.0.1). From this repository's root, set its absolute path:

```sh
wasm_runtime="/absolute/path/to/wasmtime"
"$wasm_runtime" --version
```

## Read the edge of a memory

Run:

```sh
"$wasm_runtime" run -S cli=n --invoke read docs/examples/isolation/memory.wat 0
"$wasm_runtime" run -S cli=n --invoke read docs/examples/isolation/memory.wat 65535
"$wasm_runtime" run -S cli=n --invoke read docs/examples/isolation/memory.wat 65536
```

The first two return `42` and `0`. The last exits with an out-of-bounds trap: this memory starts with 65,536 bytes, so offset 65,536 is already outside it. Wasmtime may also print an invocation warning; read the result and exit status separately.

Now run:

```sh
"$wasm_runtime" run -S cli=n --invoke overwrite-neighbour docs/examples/isolation/memory.wat
```

It returns `99`. Open [the module](../examples/isolation/memory.wat) and find the store to offset `1`. That overwrite is inside the memory and is permitted. The runtime has not enforced a separate boundary for each conceptual object stored there.

## Compare two instances

Run this command:

```sh
"$wasm_runtime" run -S cli=n \
  --preload left=docs/examples/isolation/memory.wat \
  --preload right=docs/examples/isolation/memory.wat \
  --invoke observe docs/examples/isolation/instances.wat
```

The results are `77` and `42`. The observer changed the left instance; the right retained its initial byte even though both instances came from the same file. Open [the observer](../examples/isolation/instances.wat) and follow its imported function calls.

## Run all boundary checks

```sh
python3 scripts/check-isolation.py --wasmtime "$wasm_runtime"
```

Expect `"passed": true` and 11 cases. Inspect `test-results/isolation.json`: an infinite loop exhausts its fuel, a host memory cap rejects growth, a missing import prevents linking, and the wrong function type is rejected. A compatible provider makes the quote function return 250.

These are small controlled observations. They do not test arbitrary malicious guests, side channels or a provider's tenant isolation. The [lab reference](../reference/isolation-lab.md) records exact cases and scope; [pointer semantics](../explanation/component-memory.md) and [isolation guarantees](../explanation/isolation-guarantees.md) explain the consequences.
