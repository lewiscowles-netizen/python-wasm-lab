#!/usr/bin/env python3
"""Replay the core Wasm isolation tutorial using a supplied Wasmtime 49.0.1 binary."""
import argparse
import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "docs/examples/isolation"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wasmtime", required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "test-results/isolation.json")
    args = parser.parse_args()
    binary = Path(args.wasmtime).resolve()
    version = subprocess.check_output([str(binary), "--version"], text=True).strip()
    if not version.startswith("wasmtime 49.0.1 "):
        parser.error("This recorded fixture requires Wasmtime 49.0.1")
    sources = [Path(__file__).resolve(), *sorted(EXAMPLES.glob("*.wat"))]
    evidence = {
        "schemaVersion": 1,
        "checkedAt": datetime.now(timezone.utc).isoformat(),
        "scope": "Core module semantics in a native CLI; not a WASI, hostile-tenant, side-channel or cloud certification.",
        "host": platform.platform(),
        "runtime": {"version": version, "binarySHA256": hashlib.sha256(binary.read_bytes()).hexdigest()},
        "sources": [{"path": str(p.relative_to(ROOT)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in sources],
        "cases": [],
    }
    cases = [
        ("in-bounds read", [], "read", "memory.wat", ["0"], "42", None),
        ("last valid byte", [], "read", "memory.wat", ["65535"], "0", None),
        ("out-of-bounds read", [], "read", "memory.wat", ["65536"], None, "out of bounds memory access"),
        ("in-bounds neighbour overwrite", [], "overwrite-neighbour", "memory.wat", [], "99", None),
        ("growth without host cap", [], "grow", "memory.wat", [], "1", None),
        ("growth denied by host cap", ["-W", "max-memory-size=65536"], "grow", "memory.wat", [], "-1", None),
        ("fuel ends infinite loop", ["-W", "fuel=1000"], "spin", "memory.wat", [], None, "all fuel consumed"),
        ("missing capability import", [], "quote", "consumer.wat", ["2"], None, "unknown import"),
        ("linked capability", ["--preload", "catalog=catalog.wat"], "quote", "consumer.wat", ["2"], "250", None),
        ("wrong import signature", ["--preload", "catalog=wrong-catalog.wat"], "quote", "consumer.wat", ["2"], None, "incompatible import type"),
        ("two independent memories", ["--preload", "left=memory.wat", "--preload", "right=memory.wat"], "observe", "instances.wat", [], "77\n42", None),
    ]
    try:
        for name, options, function, filename, arguments, stdout, error in cases:
            command = ["run", "-S", "cli=n", *options, "--invoke", function, filename, *arguments]
            result = subprocess.run([str(binary), *command], cwd=EXAMPLES, text=True, capture_output=True, timeout=10)
            observed = {"name": name, "arguments": command, "exitCode": result.returncode, "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}
            evidence["cases"].append(observed)
            if error is None:
                if result.returncode != 0 or result.stdout.strip() != stdout:
                    raise AssertionError(observed)
            else:
                if result.returncode == 0 or error not in result.stderr:
                    raise AssertionError(observed)
            observed["passed"] = True
        evidence["passed"] = True
    except Exception as error:
        evidence["passed"] = False
        evidence["failure"] = str(error)
        raise
    finally:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(evidence, indent=2) + "\n")
        print(json.dumps({"passed": evidence["passed"], "cases": len(evidence["cases"]), "output": str(args.output)}))


if __name__ == "__main__":
    main()
