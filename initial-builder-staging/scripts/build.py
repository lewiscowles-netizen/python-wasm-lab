#!/usr/bin/env python3
"""Run checksum-pinned Buildx builds; never infer success from a source pin."""
import argparse
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("series", nargs="+", help="Python minor versions, e.g. 3.14 3.15")
parser.add_argument("--jobs", type=int, default=4)
parser.add_argument("--print", action="store_true", dest="print_only")
args = parser.parse_args()
lock = json.loads((ROOT / "versions.json").read_text())
versions = {v["series"]: v for v in lock["versions"]}
targets = {}
for series in args.series:
    if series not in versions:
        parser.error("Unknown minor version " + series)
    if series not in ("3.14", "3.15"):
        parser.error("This branch currently builds 3.14 and 3.15; use the family-specific branch for " + series)
    v = versions[series]
    targets["python-" + series.replace(".", "-")] = {
        "context": str(ROOT),
        "dockerfile": "Dockerfile",
        "args": {"PYTHON_VERSION": v["version"], "PYTHON_SERIES": series,
                 "PYTHON_URL": v["url"], "PYTHON_SHA256": v["sha256"], "JOBS": str(args.jobs)},
        "output": ["type=local,dest=" + str(ROOT / "builds" / ("build-" + v["version"]))],
    }
bake = {"group": {"default": {"targets": list(targets)}}, "target": targets}
if args.print_only:
    print(json.dumps(bake, indent=2))
else:
    subprocess.run(["docker", "buildx", "bake", "--file", "-", "--progress", "plain"],
                   input=json.dumps(bake), text=True, check=True, cwd=ROOT)
