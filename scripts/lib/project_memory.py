"""A-Wiki Memory Plane — project-aware storage resolver (Phase 5).

L2 Project Memory: durable memory belonging to exactly ONE attached project.
Identity + policy come from the Phase-4 adapter (.awiki/project.yaml) —
this module invents no second policy. Storage layout under the A-Wiki data
root (env AWIKI_DATA_DIR, else scripts/drive_path.get_drive_root()):

    <data-root>/projects/<project-id>/memory/entries.jsonl

Isolation + safety:
  - fail closed when the Phase-4 adapter is invalid (reuse scripts/project/validate)
  - memory.scopes.project=false denies L2 writes/reads
  - project-id is validated against the adapter AND the layer slug pattern
  - data root must be absolute and containment-checked; traversal rejected
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "project"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import validate as project_validate  # noqa: E402 -- Phase-4 adapter validator
import memory_layers as ml           # noqa: E402 -- layer semantics

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


class AdapterInvalid(Exception):
    """Phase-4 project adapter missing/invalid — memory operations fail closed."""


class ScopeDenied(Exception):
    """The project's memory policy denies this operation."""


def default_data_root() -> Path:
    env = os.environ.get("AWIKI_DATA_DIR")
    if env:
        return Path(env)
    from drive_path import get_drive_root  # noqa: E402 -- existing data-root helper
    return get_drive_root()


def _check_data_root(data_root: Path) -> Path:
    root = Path(data_root)
    if not root.is_absolute():
        raise ValueError(f"data root must be absolute (got {root})")
    if root.is_symlink():
        raise ValueError("data root must not be a symlink")
    return root


class ProjectMemoryStore:
    """L2 memory for one attached project (JSONL entries, ledger-compatible)."""

    def __init__(self, project_root: Path, data_root: Path | None = None):
        project_root = Path(project_root).resolve()
        result = project_validate.validate(project_root)
        if result.exit_code() != 0:
            raise AdapterInvalid(
                "project adapter invalid (fail closed): " + "; ".join(result.errors[:3]))

        import yaml
        data = yaml.safe_load(
            (project_root / ".awiki" / "project.yaml").read_text(encoding="utf-8"))
        pid = data.get("id")
        if not isinstance(pid, str) or not _SLUG_RE.match(pid):
            raise AdapterInvalid(f"project id not slug-safe: {pid!r}")

        scopes = (data.get("memory") or {}).get("scopes") or {}
        self.project_id = pid
        self.scopes = scopes
        self.privacy = data.get("privacy") or {}
        self.trust = data.get("trust") or {}
        self._root = _check_data_root(data_root) if data_root else _check_data_root(default_data_root())

    # ── paths ──
    @property
    def memory_dir(self) -> Path:
        return self._root / "projects" / self.project_id / "memory"

    def _entries_path(self) -> Path:
        return self.memory_dir / "entries.jsonl"

    def _require_scope(self, key: str):
        if self.scopes.get(key) is not True:
            raise ScopeDenied(f"memory.scopes.{key} is not enabled for this project")

    # ── L2 entry API ──
    def append_entry(self, text: str, meta: dict | None = None) -> int:
        self._require_scope("project")
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        entry = {"text": text, "meta": meta or {}, "project": self.project_id}
        with self._entries_path().open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return 1

    def read_entries(self, query: str, limit: int = 20) -> list[dict]:
        """Simple containment-scoped scan; only THIS project's entries."""
        self._require_scope("project")
        p = self._entries_path()
        if not p.is_file():
            return []
        q = query.lower()
        hits = []
        for line in reversed(p.read_text(encoding="utf-8").splitlines()):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("project") != self.project_id:
                continue  # isolation guard even inside a shared file
            if q in str(entry.get("text", "")).lower():
                hits.append(entry)
                if len(hits) >= limit:
                    break
        return hits

    # ── layer gate for generic writes (L4/L3 protection) ──
    def write_layer(self, layer: str, text: str):
        pol = ml.LAYER_POLICY.get(layer)
        if pol is None or not pol["writable_via_memory_api"]:
            raise ml.LayerViolation(
                f"layer {layer} is not writable via the memory API "
                f"(L4 raw is immutable; L3 requires the promotion pipeline)")
        if layer == "L2":
            return self.append_entry(text)
        raise ml.LayerViolation(f"layer {layer} write not implemented in Phase 5 scope")
