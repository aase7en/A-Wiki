"""Kilo runtime surface — keeps .kilo/kilo.jsonc skills.paths registry-owned.

WO-AWIKI-KILOSURF-08. The generated/kilo.skills-paths.json snippet was
correct but nothing merged it into the runtime file Kilo actually reads,
so .kilo/kilo.jsonc carried a stale hand-frozen list (Iron Law #10 drift).

Design (terra r1+r2):
- ``render`` is PURE (safe for --check) and byte-preserving: it reads BYTES
  (no universal-newline translation — CRLF outside the array survives) and
  surgically replaces only the top-level ``skills.paths`` array, anchored
  to the file's standard two-space top-level key indentation. Any other
  shape (nested "skills" objects, missing block, exotic formatting) fails
  loud instead of guessing. ``--check`` can therefore never report drift
  for reasons unrelated to paths.
- ``write_atomic`` is the regen-side writer: stats the file BEFORE render
  reads it, re-reads and re-stats afterwards (refusing to overwrite a file
  that changed mid-render), writes to a temp file, restores the original
  file mode, fsyncs and os.replace()s into place. Concurrency note: this
  is best-effort single-writer protection — the residual stat→replace
  window is microseconds and there is no cross-process lock; the double
  guard plus content short-circuit covers the realistic regen-vs-editor
  race. A crash can never truncate the runtime config.

Fails loud when the runtime file is missing or its shape is unexpected:
it is a tracked repo file, so absence means a broken checkout.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path

from .. import Registry
from .gen_kilo import _category_dirs

REPO_ROOT = Path(__file__).resolve().parents[3]
filename = ".kilo/kilo.jsonc"  # repo-root-relative (ROOT_SURFACES)

# Top-level "skills": {"paths": [...]} — anchored to exactly two spaces of
# indentation (the file's standard top-level key depth). A nested "skills"
# object deeper inside another value will NOT match this pattern, and a
# top-level block reformatted to another depth fails loud by not matching.
_PATHS_RE = re.compile(
    rb'(?P<block>\n  "skills"\s*:\s*\{\s*"paths"\s*:\s*\[)(?P<items>[^\]]*)'
    rb'(?P<end>\])',
)


def _render_paths_json(paths: list[str]) -> bytes:
    inner = ",\n".join(json.dumps(p) for p in paths)
    indented = "\n".join(
        ("      " + line if line else line) for line in inner.splitlines()
    )
    return f'\n{indented}\n    '.encode("utf-8")


def render(registry: Registry) -> bytes:
    """Pure render: current file BYTES with ONLY the top-level
    skills.paths array replaced by the registry-derived list. Raises
    RuntimeError on any structural surprise — never guesses."""
    runtime_path = REPO_ROOT / filename
    if not runtime_path.exists():
        raise RuntimeError(
            f"{filename} missing — tracked runtime config expected in every "
            "checkout; refusing to invent one from scratch")
    raw = runtime_path.read_bytes()
    new_paths = _render_paths_json(_category_dirs(registry))
    out, n = _PATHS_RE.subn(
        lambda m: m.group("block") + new_paths + m.group("end"),
        raw, count=1)
    if n != 1:
        raise RuntimeError(
            f"{filename}: could not locate the top-level skills.paths array "
            "(standard two-space indentation expected) — refusing blind "
            "rewrite")
    # sanity: the replacement must parse and carry exactly the derived
    # paths at the TOP LEVEL (a nested "skills" elsewhere must never have
    # been the thing we replaced).
    parsed = json.loads(out.decode("utf-8"))
    if parsed.get("skills", {}).get("paths") != _category_dirs(registry):
        raise RuntimeError(
            f"{filename}: surgical replace produced wrong top-level paths")
    return out


def write_atomic(registry: Registry, out_path: Path) -> None:
    """Regen-side writer with concurrent-modification guards and atomic
    replace. regen-skill-surfaces.py prefers this over plain write_text
    when a generator defines it."""
    runtime_path = REPO_ROOT / filename
    stat_before = runtime_path.stat()  # BEFORE render reads the file
    expected = render(registry)
    # TOCTOU guard #1: refuse to clobber a file that changed mid-render.
    current = runtime_path.read_bytes()
    stat_mid = runtime_path.stat()
    if (stat_mid.st_mtime_ns, stat_mid.st_size) != (
            stat_before.st_mtime_ns, stat_before.st_size):
        raise RuntimeError(
            f"{filename} changed while rendering — refusing to overwrite; "
            "re-run regen")
    if current == expected:
        return  # already in sync; no write, no mtime churn
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=str(out_path.parent), prefix=".kilo.jsonc.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as tmp:
            tmp.write(expected)
            tmp.flush()
            os.fsync(tmp.fileno())
        # preserve the original file mode (mkstemp creates 0600; the
        # tracked config is 0644 — other readers must keep access)
        os.chmod(tmp_name, stat_before.st_mode & 0o7777)
        # TOCTOU guard #2: last check immediately before the atomic swap.
        stat_last = runtime_path.stat()
        if (stat_last.st_mtime_ns, stat_last.st_size) != (
                stat_before.st_mtime_ns, stat_before.st_size):
            raise RuntimeError(
                f"{filename} changed during write — refusing to replace; "
                "re-run regen")
        os.replace(tmp_name, out_path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
