"""Kilo runtime surface — keeps .kilo/kilo.jsonc skills.paths registry-owned.

WO-AWIKI-KILOSURF-08. The generated/kilo.skills-paths.json snippet was
correct but nothing merged it into the runtime file Kilo actually reads,
so .kilo/kilo.jsonc carried a stale hand-frozen list (Iron Law #10 drift).
This generator renders the runtime file by loading its current content
(pure JSON — no comments, verified) and replacing ONLY ``skills.paths``
with the registry-derived category dirs. Operator-owned config (model,
permission, indexing, agents, …) is preserved byte-for-byte in structure.

Fails loud when the runtime file is missing: it is a tracked repo file, so
absence means a broken checkout, not a bootstrap case.
"""
from __future__ import annotations

import json
from pathlib import Path

from .. import Registry
from .gen_kilo import _category_dirs

REPO_ROOT = Path(__file__).resolve().parents[3]
filename = ".kilo/kilo.jsonc"  # repo-root-relative (ROOT_SURFACES)


def render(registry: Registry) -> str:
    runtime_path = REPO_ROOT / filename
    if not runtime_path.exists():
        raise RuntimeError(
            f"{filename} missing — tracked runtime config expected in every "
            "checkout; refusing to invent one from scratch")
    data = json.loads(runtime_path.read_text(encoding="utf-8"))
    data.setdefault("skills", {})["paths"] = _category_dirs(registry)
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"
