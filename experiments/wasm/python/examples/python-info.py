from __future__ import print_function
import os
import struct
import sys


def field(name, value):
    print(name + ": " + str(value))


def unavailable(error):
    return "unavailable (" + type(error).__name__ + ": " + str(error) + ")"


print("=== Interpreter ===")
field("Version", sys.version.replace("\n", " "))
field("Platform", sys.platform)
implementation = getattr(sys, "implementation", None)
if implementation is not None:
    field("Implementation", implementation.name)
else:
    try:
        import platform
        field("Implementation", platform.python_implementation())
    except Exception as error:
        field("Implementation", unavailable(error))
field("Pointer width (bits)", struct.calcsize("P") * 8)
field("Byte order", sys.byteorder)
field("Maximum Unicode code point", hex(sys.maxunicode))
field("Length of one astral character", len(b"\\U0001f600".decode("unicode_escape")))

print("\n=== Encodings ===")
field("Default encoding", sys.getdefaultencoding())
field("Filesystem encoding", sys.getfilesystemencoding())
field("Standard output encoding", getattr(sys.stdout, "encoding", None))
field("Standard error encoding", getattr(sys.stderr, "encoding", None))

print("\n=== Paths ===")
field("Executable", sys.executable)
for name in ("prefix", "exec_prefix", "base_prefix", "base_exec_prefix"):
    field(name, getattr(sys, name, "unavailable"))
field("Current directory", os.getcwd())
field("Import paths", repr(sys.path))

print("\n=== Modules ===")
field("Built-in modules", ", ".join(sorted(sys.builtin_module_names)))
for name in ("sqlite3", "zlib", "bz2", "decimal", "ssl", "ctypes",
             "pip", "micropip", "js"):
    try:
        module = __import__(name)
        detail = None
        if name == "sqlite3":
            detail = "SQLite " + module.sqlite_version
        field(name, "import available" + (" (" + str(detail) + ")" if detail else ""))
    except Exception as error:
        field(name, unavailable(error))
print("An import alone does not prove that every module operation works.")

print("\n=== Build configuration ===")
try:
    import sysconfig
except Exception as error:
    field("sysconfig module", unavailable(error))
    field("Target build metadata", "unavailable (sysconfig module is missing)")
else:
    field("sysconfig module", "available")
    try:
        field("sysconfig platform", sysconfig.get_platform())
    except Exception as error:
        field("sysconfig platform", unavailable(error))
    try:
        configuration = sysconfig.get_config_vars()
    except Exception as error:
        field("Target build metadata", unavailable(error))
    else:
        field("Target build metadata", "available")
        for name in ("SOABI", "EXT_SUFFIX", "MULTIARCH", "HOST_GNU_TYPE",
                     "BUILD_GNU_TYPE", "SIZEOF_VOID_P", "Py_ENABLE_SHARED",
                     "Py_DEBUG", "Py_GIL_DISABLED", "WITH_PYMALLOC"):
            field(name, configuration.get(name, "unavailable"))

print("\nDiagnostics complete.")
