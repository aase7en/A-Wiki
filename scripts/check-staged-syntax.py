#!/usr/bin/env python3
"""check-staged-syntax.py — compile every staged *.py before the commit lands.

Why this exists
---------------
Commit 307b3215 ("chunk(a-claim): Iron Law #11") wrote two f-strings in
scripts/hooks/session_start.py with a LITERAL newline where `\\n` was meant.
The pre-commit gate printed "✅ AWiki safety gate passed" and let it through.
Until it was fixed on 2026-07-27:

  * the SessionStart hook crashed every session — silently, its output simply
    never appeared;
  * `pytest tests/` aborted at COLLECTION ("Interrupted: 2 errors during
    collection") because two test modules exec_module that file at import, so
    the ENTIRE suite ran zero tests while looking like a tooling error rather
    than a failure list.

tests/test_hooks_subprocess_encoding.py already ast.parses every
scripts/hooks/*.py and WOULD have caught it — but a suite that cannot collect
cannot catch anything. So the same check has to run at a point that does not
depend on the suite being runnable: commit time.

What it checks
--------------
The STAGED blob (`git cat-file blob <index sha>`), never the working tree —
git commits the index, so the index is what has to compile. A file fixed on
disk but staged broken still blocks; mid-edit garbage on disk does not.

Usage
-----
    python scripts/check-staged-syntax.py --staged

No arguments = silent no-op (keeps the file inert if it is ever wired up or
imported somewhere that just runs it).

Exit codes
----------
    0  clean, nothing staged, not a repo, or skipped
    1  syntax error(s) found — findings on stdout as `path:line:col: message`
    2  internal error — fail-closed, because a checker that cannot run must
       not look like a pass (that failure mode is what shipped 307b3215)

Override
--------
    HOOK_SKIP=check_staged_syntax        (this step only)
    PRE_COMMIT_SKIP_AWIKI=1              (the whole Layer-2 gate)
"""
from __future__ import annotations

import os
import subprocess
import sys
import warnings

SKIP_TOKEN = "check_staged_syntax"
# Regular file blobs only. Symlinks (120000) and gitlinks (160000) have no
# Python source to compile — a symlink's "content" is its target path, which
# would be a guaranteed false positive.
BLOB_MODES = {"100644", "100755"}


def _git(args: list[str]) -> bytes:
    """Run git in the current directory and return raw stdout bytes.

    Bytes, not text: paths and source may hold any encoding, and decoding
    child output with the locale codec is its own recurring bug class here
    (see tests/test_hooks_subprocess_encoding.py).
    """
    proc = subprocess.run(["git", *args], capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args[:3])} failed (rc={proc.returncode}): "
            f"{proc.stderr.decode('utf-8', 'replace').strip()}"
        )
    return proc.stdout


def _decode_path(raw: bytes) -> str:
    return raw.decode("utf-8", "surrogateescape")


def staged_python_blobs() -> list[tuple[str, str]]:
    """[(path, index blob sha)] for staged *.py files that still exist.

    Reads `git diff --cached --raw -z`, whose records carry the destination
    mode and the index blob sha directly:
        :<srcmode> <dstmode> <srcsha> <dstsha> <status>\\0<path>\\0
    Renames/copies add a second path field; the destination is the last one.
    """
    raw = _git([
        "diff", "--cached", "--raw", "-z",
        "--diff-filter=ACMR",  # deletions have no blob left to compile
    ])
    fields = raw.split(b"\x00")
    out: list[tuple[str, str]] = []
    i = 0
    while i < len(fields):
        meta = fields[i]
        i += 1
        if not meta.startswith(b":"):
            continue  # trailing empty field
        parts = meta[1:].split(b" ")
        if len(parts) < 5:
            continue
        dst_mode, dst_sha, status = parts[1], parts[3], parts[4]
        # R/C records carry <source path>\0<destination path>\0.
        n_paths = 2 if status[:1] in (b"R", b"C") else 1
        paths = fields[i:i + n_paths]
        i += n_paths
        if not paths:
            continue
        path = _decode_path(paths[-1])
        if not path.endswith(".py"):
            continue
        if dst_mode.decode("ascii", "replace") not in BLOB_MODES:
            continue
        out.append((path, dst_sha.decode("ascii", "replace")))
    return out


def compile_blob(path: str, sha: str) -> str | None:
    """Compile one staged blob. Returns a finding line, or None if it is fine."""
    source = _git(["cat-file", "blob", sha])
    try:
        with warnings.catch_warnings():
            # SyntaxWarning (e.g. invalid escape sequence) is not a commit
            # blocker and must not pollute the gate's output.
            warnings.simplefilter("ignore")
            # bytes input: CPython honours the PEP 263 coding cookie and BOM
            # itself, so files that are not UTF-8 still compile correctly.
            compile(source, path, "exec", dont_inherit=True)
    except SyntaxError as exc:
        line = exc.lineno or 0
        col = exc.offset or 0
        finding = f"  {path}:{line}:{col}: {exc.msg}"
        text = (exc.text or "").rstrip("\n")
        if text.strip():
            finding += f"\n      | {text.strip()[:120]}"
        return finding
    except ValueError as exc:  # e.g. source contains null bytes
        return f"  {path}: {exc}"
    return None


def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:  # Thai Windows consoles default to cp874
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass

    if "--staged" not in argv:
        return 0  # inert unless explicitly asked to check the index

    if SKIP_TOKEN in os.environ.get("HOOK_SKIP", "").replace("-", "_"):
        sys.stderr.write(f"🐍 Syntax gate: BYPASSED (HOOK_SKIP={SKIP_TOKEN})\n")
        return 0

    try:
        _git(["rev-parse", "--git-dir"])
    except (RuntimeError, OSError):
        return 0  # no repo, no index, nothing to gate

    try:
        blobs = staged_python_blobs()
        findings = [f for f in (compile_blob(p, s) for p, s in blobs) if f]
    except Exception as exc:  # noqa: BLE001 — fail-closed on purpose
        sys.stderr.write(f"check-staged-syntax: internal error: {exc}\n")
        return 2

    if findings:
        print("\n".join(findings))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
