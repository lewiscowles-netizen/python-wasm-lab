"""Package source, not host bytecode, into a deterministic uncompressed stdlib zip."""
import pathlib
import sys
import zipfile
import sysconfig
import re

source, dest, series = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3]
dest.mkdir(parents=True, exist_ok=True)
(dest / ("python" + series) / "lib-dynload").mkdir(parents=True, exist_ok=True)
(dest / ("python" + series) / "lib-dynload" / ".empty").write_text("")
(dest / ("python" + series) / "os.py").write_text("# Standard library path marker\n")
excluded = {"test", "tests", "__pycache__", "idlelib", "tkinter", "turtledemo", "ensurepip", "venv"}
config = sysconfig._parse_makefile('/build/wasm/Makefile')
with open('/build/wasm/pyconfig.h') as stream:
    sysconfig.parse_config_h(stream, config)
for name in re.findall(r'^#undef\s+(\w+)', pathlib.Path('/build/wasm/pyconfig.h').read_text(), re.M):
    config[name] = 0
# These are target build variables parsed from target files, not host config.
names = ['_sysconfigdata']
if tuple(map(int, series.split('.'))) >= (3, 6):
    names.append('_sysconfigdata_{}_emscripten_{}'.format(config.get('ABIFLAGS', ''), config.get('MULTIARCH', '')))
with zipfile.ZipFile(dest / ("python" + series.replace(".", "") + ".zip"), "w") as archive:
    for name in names:
        info = zipfile.ZipInfo(name + '.py', date_time=(2000, 1, 1, 0, 0, 0))
        info.external_attr = 0o644 << 16
        archive.writestr(info, 'build_time_vars = ' + repr(dict(sorted(config.items()))) + '\n')
    for path in sorted(source.rglob("*.py")):
        relative = path.relative_to(source)
        if excluded.intersection(relative.parts):
            continue
        info = zipfile.ZipInfo(relative.as_posix(), date_time=(2000, 1, 1, 0, 0, 0))
        info.external_attr = 0o644 << 16
        archive.writestr(info, path.read_bytes())
