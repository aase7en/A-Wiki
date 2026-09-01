"""zcode_hook_loader.py — machine-local dispatcher for the ZCode user-level
hook config (~/.zcode/cli/config.json). Canonical copy lives here; installed
to ~/.zcode/hooks/awiki_hook_loader.py by scripts/setup-zcode-hooks.py.

Why this exists (verified 2026-09-01, zcode.z.ai/en/docs/hooks): ZCode runs
user-level and plugin hooks but IGNORES workspace .zcode/config.json hooks —
so A-Wiki's repo-level hook wiring never fires on ZCode. The canonical hook
scripts stay in each repo; this loader is referenced by the user-level config
and:

  - no-ops (exit 0, silent) when the target script does not exist —
    non-A-Wiki projects stay completely unaffected;
  - forwards stdin bytes, stdout, and exit codes 0/2 to/from the target
    (2 = deny/ask/continue-one-round semantics per event);
  - normalizes any other child exit code to 0 so a buggy hook script can
    never spray error noise into every ZCode session on the machine.

Contract: python awiki_hook_loader.py <target-script.py> [target args...]
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass


def run(target, extra_args, stdin_bytes: bytes = b"") -> int:
    """Run target script if it exists; return normalized child exit code."""
    target = Path(target)
    if not target.is_file():
        return 0
    try:
        proc = subprocess.run(
            [sys.executable, str(target), *[str(a) for a in extra_args]],
            input=stdin_bytes, capture_output=True)
    except OSError:
        return 0
    if proc.stdout:
        try:
            sys.stdout.write(proc.stdout.decode("utf-8", errors="replace"))
            sys.stdout.flush()
        except (OSError, ValueError):
            pass
    return 2 if proc.returncode == 2 else 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        return 0
    try:
        stdin_bytes = b"" if sys.stdin.isatty() else sys.stdin.buffer.read()
    except (OSError, ValueError, AttributeError):
        stdin_bytes = b""
    return run(argv[0], argv[1:], stdin_bytes)


if __name__ == "__main__":
    sys.exit(main())
