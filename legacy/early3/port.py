"""Minimal backport of browser constraints to pre-upstream-Wasm CPython.

Build the static interpreter from release-generated sources; this deliberately
does not claim support for extension compilation, sockets, processes or threads.
"""
import re
from pathlib import Path

root = Path('/build/source')
sub = root / 'config.sub'
if sub.exists():
    text = sub.read_text()
    lines = text.splitlines(True)
    lines.insert(1, 'case "$1" in wasm32-unknown-emscripten) echo "$1"; exit 0;; esac\n')
    sub.write_text(''.join(lines))
configure = root / 'configure'
text = configure.read_text()
text = text.replace('*-*-linux*)', '*-*-emscripten | *-*-linux*)')
# Python 3.0 has three unconditionally fatal cross-build runtime probes.
# chflags/lchflags are unavailable; musl supports the standard %zd format.
fatal = re.compile(r'if test "\$cross_compiling" = yes; then\n  \{ \{ echo[^\n]*error: cannot run test program while cross compiling.*?\{ \(exit 1\); exit 1; \}; \}', re.S)
matches = list(fatal.finditer(text))
if matches:
    assert len(matches) == 3, 'Review the cross-build runtime probes for this release'
    count = [0]
    def replace(match):
        count[0] += 1
        if count[0] < 3:
            return 'if test "$cross_compiling" = yes; then\n  : # chflags/lchflags are not available in the browser'
        return 'if test "$cross_compiling" = yes; then\n  echo \'#define PY_FORMAT_SIZE_T "z"\' >> confdefs.h'
    text = fatal.sub(replace, text)
# Python 3.1's newer Autoconf syntax has sem_getvalue and %zd runtime probes.
fatal31 = re.compile(r'if test "\$cross_compiling" = yes; then :\n  \{ \{ \$as_echo[^\n]*error: in.*?as_fn_error \$\? "cannot run test program while cross compiling.*?" "\$LINENO" 5; \}', re.S)
matches31 = list(fatal31.finditer(text))
if matches31:
    assert len(matches31) == 2, 'Review the newer cross-build runtime probes'
    answers = iter(('HAVE_BROKEN_SEM_GETVALUE 1', 'PY_FORMAT_SIZE_T "z"'))
    text = fatal31.sub(lambda match: 'if test "$cross_compiling" = yes; then :\n  echo \'#define ' + next(answers) + '\' >> confdefs.h', text)
configure.write_text(text)
# Old POSIX code declares popen even without configure detecting it.
posix = root / 'Modules/posixmodule.c'
text = posix.read_text().replace('#define HAVE_POPEN      1', '#ifndef __EMSCRIPTEN__\n#define HAVE_POPEN      1\n#endif')
posix.write_text(text)
fileutils = root / 'Python/fileutils.c'
if fileutils.exists():
    text = fileutils.read_text()
    text = re.sub(r'(set_inheritable\(int fd, int inheritable, int raise, int \*atomic_flag_works\)\s*\{)', r'\1\n#ifdef __EMSCRIPTEN__\n    return 0; /* No subprocesses or inherited FDs in this browser build. */\n#endif', text)
    fileutils.write_text(text)
