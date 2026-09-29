#!/usr/bin/env python3
"""Import the separate builder's completed, verified runtimes into this lab."""
import argparse
from pathlib import Path
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--builder", type=Path, default=root.parent / "python-wasm-builder",
                        help="Builder checkout containing scripts/export-site.py and builds/")
    args = parser.parse_args()
    builder = args.builder.resolve()
    exporter = builder / "scripts/export-site.py"
    if not exporter.is_file():
        parser.error("Builder exporter not found; supply --builder /path/to/python-wasm-builder")
    builds = sorted(path for path in (builder / "builds").glob("build-[0-9]*") if path.is_dir())
    if not builds:
        parser.error("No completed build directories found. Build interpreters in python-wasm-builder first.")
    # Validate and export runtime artifacts through the builder.
    subprocess.run([sys.executable, str(exporter), str(root), *(str(path) for path in builds)], check=True)
    print("Imported %d builds. Start the playground with: python3 serve.py" % len(builds))


if __name__ == "__main__":
    main()
