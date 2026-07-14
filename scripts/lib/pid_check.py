#!/usr/bin/env python3
"""pid_check.py — cross-platform, SAFE process-liveness probe.

Why this exists (concrete incident, this repo, 2026-07-14):
scripts/dashboard-stop.sh used MSYS `kill -0 "$pid"` to decide whether the
Live Dashboard daemon was still running before cleaning up its PID file. On
Windows the daemon's PID (.tmp/live-dashboard.pid, written by
scripts/live-dashboard/server.py::daemonize()) is a genuine native Win32 PID
(subprocess.Popen(..., creationflags=DETACHED_PROCESS).pid) — Git Bash's
`kill` only signals MSYS-space processes and reports "No such process" for
ANY native PID, dead or alive.

Empirically confirmed on this machine:
  - `kill -0 <native_pid>`      -> "No such process", even though alive.
  - `kill <native_pid>` (real)  -> ALSO "No such process" — MSYS kill cannot
    even terminate a native PID, not just probe it.
  - `taskkill //PID <pid> //F`  -> works.
That false negative made dashboard-stop.sh delete the PID file as "stale"
while the daemon kept running — silently orphaned (never actually stopped,
and no longer discoverable since the PID file was gone).

A second call site had the same POSIX-assumption problem, though narrower
than first suspected: scripts/live-dashboard/server.py::is_already_running()
called `os.kill(pid, 0)` intending the POSIX "just probe, don't kill"
existence check. CPython on Windows special-cases sig values 0 and 1 (they
equal win32's CTRL_C_EVENT/CTRL_BREAK_EVENT) to call
GenerateConsoleCtrlEvent() instead of TerminateProcess() — confirmed by
direct experiment on this machine (Python 3.11.15): os.kill(pid, 0) against
both an ordinary child and one spawned with the exact
DETACHED_PROCESS|CREATE_NEW_PROCESS_GROUP flags server.py's daemonize() uses
did NOT terminate it, while os.kill(pid, 15) reliably did (exit code 15).
So `os.kill(pid, 0)` is not the "instant kill" landmine it can appear to be
from CPython's TerminateProcess(handle, sig) pattern for other signal
values — but it is still the wrong tool here: GenerateConsoleCtrlEvent's
actual effect depends on console/process-group configuration the caller
doesn't control (it can raise OSError for a process in a different process
group, or silently do nothing, or in principle be delivered if the target
ever attaches a console) — none of that is "reliably tells you if the PID
is alive," which is the one thing this check needs.

is_pid_alive() is the one safe, well-defined way to ask "is this PID alive"
on both platforms, without depending on console-signal delivery quirks:
  - POSIX: os.kill(pid, 0) is safe and precisely-defined here — real
    signal-0 semantics (ESRCH if not found, EPERM if found-but-inaccessible).
  - Windows: OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, ...) — a
    handle-open call that can never terminate anything, plus
    GetExitCodeProcess()'s STILL_ACTIVE sentinel (see _is_alive_windows()'s
    own docstring for why the OpenProcess success check alone isn't
    sufficient either).

This module must NEVER call TerminateProcess, os.kill() relying on Windows
signal semantics, or any other API that can end the process it is checking.

No REPO_ROOT constant here (unlike scripts/lib/vendor_watch.py /
skill_learning.py) — this module touches no repo files, only the OS process
table, so a repo-root path would be dead code.
"""
from __future__ import annotations

import os
import sys

# No Thai/emoji text is emitted by this module, but keep the repo-wide
# reconfigure so the CLI's own error text never crashes a cp874 console —
# same pattern as scripts/lib/vendor_watch.py / skill_learning.py.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass


def is_pid_alive(pid: int) -> bool:
    """Return True if `pid` names a live process. NEVER signals/kills it.

    Raises TypeError for a non-int `pid` (bool included — it's a subclass
    of int but never a valid PID) and ValueError for pid <= 0 (0 and
    negative PIDs have special "process group" meaning on POSIX — refusing
    them here prevents this "just checking" function from ever accidentally
    probing/signaling a whole process group). These ARE allowed to raise —
    they are programmer errors, not "PID doesn't exist" cases.

    For any well-typed positive int that simply doesn't name a live
    process (dead, never existed, inaccessible, out of range), this
    ALWAYS returns False and NEVER raises — matches the fail-soft
    convention used across scripts/lib/*.py.
    """
    if isinstance(pid, bool) or not isinstance(pid, int):
        raise TypeError(f"pid must be a positive int, got {pid!r}")
    if pid <= 0:
        raise ValueError(f"pid must be > 0, got {pid}")

    if sys.platform == "win32":
        return _is_alive_windows(pid)
    return _is_alive_posix(pid)


def _is_alive_posix(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        # Exists but owned by someone else — still "alive" for our purposes.
        return True
    except OSError:
        return False


def _is_alive_windows(pid: int) -> bool:
    """OpenProcess succeeding is NOT sufficient on its own: a process's
    kernel object stays alive (and OpenProcess-by-PID keeps working) for as
    long as ANY handle to it remains open — including a handle our own
    caller holds (e.g. a still-referenced subprocess.Popen object, which
    keeps an internal Win32 handle open until the Popen object is garbage
    collected). Empirically confirmed on this machine: OpenProcess()
    against a process that had already exited (terminate()+wait() both
    returned) still succeeded because the calling test still held its
    Popen handle — a bare "did OpenProcess succeed" check reported the
    dead process as alive. GetExitCodeProcess()'s STILL_ACTIVE (259) sentinel
    is the standard way to distinguish "object exists" from "actually
    running" and is what this function checks.
    """
    try:
        import ctypes
        import ctypes.wintypes as wintypes

        kernel32 = ctypes.windll.kernel32
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL
        kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel32.GetExitCodeProcess.restype = wintypes.BOOL

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        STILL_ACTIVE = 259

        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return False
        try:
            exit_code = wintypes.DWORD()
            ok = kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
            if not ok:
                return False
            return exit_code.value == STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)
    except Exception:
        # Out-of-range pid, ctypes/OS failure, etc. — "not alive", never raise.
        return False


def main(argv: "list[str] | None" = None) -> int:
    """CLI: exit 0 = alive, 1 = not alive, 2 = bad arg."""
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        sys.stderr.write("usage: pid_check.py <pid>\n")
        return 2
    try:
        pid = int(argv[0])
    except ValueError:
        sys.stderr.write(f"invalid pid: {argv[0]!r}\n")
        return 2
    try:
        alive = is_pid_alive(pid)
    except (TypeError, ValueError) as e:
        sys.stderr.write(f"{e}\n")
        return 2
    return 0 if alive else 1


if __name__ == "__main__":
    raise SystemExit(main())
