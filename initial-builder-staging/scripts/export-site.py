#!/usr/bin/env python3
"""Copy verified builds into the existing GitHub Pages playground."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument("site", type=Path, help="Path to the lewiscowles1986.github.io checkout")
parser.add_argument("builds", nargs="+", type=Path, help="Artifact directories")
args = parser.parse_args()
playground = args.site.resolve() / "experiments/wasm/python"
catalog_path = playground / "runtimes.json"
if not catalog_path.is_file():
    parser.error("Site does not contain the Python playground registry")
catalog = json.loads(catalog_path.read_text())
entries = {item["id"]: item for item in catalog["runtimes"]}
validated = []
for directory in args.builds:
    manifest = json.loads((directory / "manifest.json").read_text())
    version = manifest["version"]
    if not version or any(c not in "0123456789.abrc" for c in version):
        parser.error("Invalid interpreter version in manifest")
    for filename in ("python.mjs", "python.wasm", "python.data"):
        actual = hashlib.sha256((directory / filename).read_bytes()).hexdigest()
        recorded = manifest["files"][filename]["sha256"]
        if actual != recorded:
            parser.error("Artifact hash mismatch: " + str(directory / filename))
    if (directory / "python.wasm").read_bytes()[:4] != b"\x00asm":
        parser.error("Artifact is not WebAssembly")
    smoke = json.loads((directory / "smoke.json").read_text())
    if not smoke["version"].startswith(version + " "):
        parser.error("Smoke result does not match interpreter version")
    validated.append((directory, version))
for directory, version in validated:
    destination = playground / "builds" / ("build-" + version)
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".python-build-", dir=destination.parent))
    try:
        for filename in ("python.mjs", "python.wasm", "python.data", "manifest.json", "smoke.json", "CPYTHON-LICENSE.txt"):
            shutil.copy2(directory / filename, staging / filename)
        if destination.exists():
            shutil.rmtree(destination)
        staging.rename(destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    identity = "cpython-" + version
    relative = "./builds/build-" + version + "/"
    entries[identity] = {"id": identity, "label": "CPython " + version,
                         "version": version, "adapter": "emscripten",
                         "module": relative + "python.mjs",
                         "manifest": relative + "manifest.json", "invocation": "callMain"}
catalog["runtimes"] = list(entries.values())
temporary = catalog_path.with_suffix(".json.tmp")
temporary.write_text(json.dumps(catalog, indent=2) + "\n")
temporary.replace(catalog_path)
print("Exported: " + ", ".join(version for _, version in validated))
