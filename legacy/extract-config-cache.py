"""Extract reusable C ABI probes from this exact, pinned Emscripten toolchain.

Do not reuse this file across SDK versions or compiler target settings. Python
specific runtime probes, threads, optimizations and configure flags are excluded.
"""
import re
import sys
from pathlib import Path

source = Path(sys.argv[1])
target = Path(sys.argv[2])
facts = re.findall(r'^ac_cv_(?:header|func|sizeof|type)_[A-Za-z0-9_]+=.*$', source.read_text(), re.M)
assert len(facts) > 100, 'Expected a completed target configure log'
target.write_text(
    '# Measured by CPython 2.7.18 configure, emsdk 2.0.2 linux/amd64 image\n'
    '# sha256:d2daf8d497c38f69e854239b06679184dcb676580fcb56146a3ad6f559b47aa6\n'
    '# Target wasm32; overrides for unsupported browser operations follow this file.\n'
    + '\n'.join(sorted(set(facts))) + '\n'
)
print('Wrote {} measured target-compiler facts to {}'.format(len(facts), target))
