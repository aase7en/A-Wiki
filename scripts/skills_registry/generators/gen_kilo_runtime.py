"""Kilo runtime surface — keeps .kilo/kilo.jsonc skills.paths registry-owned.

WO-AWIKI-KILOSURF-08. The generated/kilo.skills-paths.json snippet was
correct but nothing merged it into the runtime file Kilo actually reads,
so .kilo/kilo.jsonc carried a stale hand-frozen list (Iron Law #10 drift).

Design (terra r1):
- ``render`` is PURE (safe for --check): it performs a SURGICAL string
  replacement of the ``paths`` array inside the ``skills`` block only.
  Everything else — bytes, formatting, ordering, any future comments
  outside that array — is preserved verbatim, so --check can never report
  drift for reasons unrelated to paths.
- ``write_atomic`` is the regen-side writer: re-reads the file, verifies it
  was not concurrently modified since render (mtime+size), writes to a
  temp file and os.replace()s it into place, so a crash can never truncate
  the runtime config (fail-loud on every anomaly).

Fails loud when the runtime file is missing or its skills/paths shape is
unexpected: it is a tracked repo file, so absence means a broken checkout.
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

_PATHS_RE = re.compile(
    r'(?P<block>"skills"\s*:\s*\{\s*"paths"\s*:\s*\[)(?P<items>[^\]]*)'
    r'(?P<end>\])',
    re.S,
)


def _render_paths_json(paths: list[str]) -> str:
    inner = ",\n".join(json.dumps(p) for p in paths)
    indented = "\n".join(
        ("      " + line if line else line) for line in inner.splitlines()
    )
    return f'\n{indented}\n    '


def render(registry: Registry) -> str:
    """Pure render: current file content with ONLY the skills.paths array
    replaced by the registry-derived list. Raises RuntimeError on any
    structural surprise — never guesses."""
    runtime_path = REPO_ROOT / filename
    if not runtime_path.exists():
        raise RuntimeError(
            f"{filename} missing — tracked runtime config expected in every "
            "checkout; refusing to invent one from scratch")
    text = runtime_path.read_text(encoding="utf-8")
    new_paths = _render_paths_json(_category_dirs(registry))
    out, n = _PATHS_RE.subn(
        lambda m: m.group("block") + new_paths + m.group("end"), text, count=1)
    if n != 1:
        raise RuntimeError(
            f"{filename}: could not locate the skills.paths array — "
            "refusing blind rewrite")
    # sanity: the replacement must parse and carry exactly the derived paths
    parsed = json.loads(out)
    if parsed["skills"]["paths"] != _category_dirs(registry):
        raise RuntimeError(f"{filename}: surgical replace produced wrong paths")
    return out


def write_atomic(registry: Registry, out_path: Path) -> None:
    """Regen-side writer with concurrent-modification guard and atomic
    replace. regen-skill-surfaces.py prefers this over plain write_text
    when a generator defines it."""
    runtime_path = REPO_ROOT / filename
    stat_before = runtime_path.stat()  # BEFORE render reads the file
    expected = render(registry)
    # TOCTOU guard: if the file changed while rendering, fail loud
    # instead of silently clobbering someone's concurrent edit.
    current = runtime_path.read_text(encoding="utf-8")
    stat_now = runtime_path.stat()
    if (stat_now.st_mtime_ns, stat_now.st_size) != (
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
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            tmp.write(expected)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(tmp_name, out_path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
