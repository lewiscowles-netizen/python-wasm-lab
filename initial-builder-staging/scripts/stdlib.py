"""Package source, not host bytecode, into a deterministic uncompressed stdlib zip."""
import pathlib
import sys
import zipfile

source, dest, series = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3]
dest.mkdir(parents=True, exist_ok=True)
(dest / ("python" + series) / "lib-dynload").mkdir(parents=True, exist_ok=True)
(dest / ("python" + series) / "os.py").write_text("# Standard library path marker\n")
excluded = {"test", "tests", "__pycache__", "idlelib", "tkinter", "turtledemo", "ensurepip", "venv"}
with zipfile.ZipFile(dest / ("python" + series.replace(".", "") + ".zip"), "w") as archive:
    for path in sorted(source.rglob("*.py")):
        relative = path.relative_to(source)
        if excluded.intersection(relative.parts):
            continue
        info = zipfile.ZipInfo(relative.as_posix(), date_time=(2000, 1, 1, 0, 0, 0))
        info.external_attr = 0o644 << 16
        archive.writestr(info, path.read_bytes())
