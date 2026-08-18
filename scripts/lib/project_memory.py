"""A-Wiki Memory Plane — project-aware storage resolver (Phase 5).

L2 Project Memory: durable memory belonging to exactly ONE attached project.
Identity + policy come from the Phase-4 adapter (.awiki/project.yaml) —
this module invents no second policy. Storage layout under the A-Wiki data
root (env AWIKI_DATA_DIR, else scripts/drive_path.get_drive_root()):

    <data-root>/projects/<project-id>/memory/entries.jsonl

R-P5-006: the entries file IS a MemoryLedger JSONL — appends route through
``memory_ledger.MemoryLedger`` (secret redaction + atomic_json concurrency)
with the authoritative ``project`` tag carried via the ledger's ``extra``
seam. There is no parallel append/search engine here.

Isolation + safety:
  - fail closed when the Phase-4 adapter is invalid (reuse scripts/project/validate)
  - memory.scopes.project=false denies L2 writes/reads
  - project-id is validated against the adapter AND the layer slug pattern
  - data root must be absolute; R-P5-002: every path below the root is
    component-wise symlink/reparse-checked and resolved-containment-checked
    before ANY read or write — nested escapes cannot follow links out
  - R-P5-005: read-only resolution never creates ~/.a-wiki-data
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "project"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import validate as project_validate  # noqa: E402 -- Phase-4 adapter validator
import memory_layers as ml           # noqa: E402 -- layer semantics
import memory_ledger                 # noqa: E402 -- L1 primitive reused for L2 (R-P5-006)
from drive_path import is_reparse_point  # noqa: E402 -- junction-safe link check

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


class AdapterInvalid(Exception):
    """Phase-4 project adapter missing/invalid — memory operations fail closed."""


class ScopeDenied(Exception):
    """The project's memory policy denies this operation."""


class StorageUnsafe(Exception):
    """A path below the data root is a symlink/reparse point or resolves
    outside the root (R-P5-002) — the operation is refused, nothing read."""


class DataRootUnavailable(Exception):
    """Read-only resolution found no configured data root and must not
    create one (R-P5-005)."""


def default_data_root() -> Path:
    """Writable resolution (may create the ~/.a-wiki-data fallback) — for
    writers only."""
    env = os.environ.get("AWIKI_DATA_DIR")
    if env:
        return Path(env)
    from drive_path import get_drive_root  # noqa: E402 -- existing helper
    return get_drive_root()


def resolve_data_root_readonly() -> Path:
    """R-P5-005: resolve the data root WITHOUT creating anything.

    Mirrors drive_path.get_drive_root()'s chain but replaces the
    mkdir-creating ~/.a-wiki-data fallback with DataRootUnavailable.
    Read-only commands (status) must never mutate the filesystem.
    """
    env = os.environ.get("AWIKI_DATA_DIR")
    if env:
        return Path(env)
    from drive_path import (  # noqa: E402
        REPO_ROOT as _DRIVE_REPO_ROOT, resolve_link_target, path_exists)
    link = _DRIVE_REPO_ROOT / "drive"
    if link.is_symlink() or is_reparse_point(link):
        target = resolve_link_target(link)
        if path_exists(target):
            return target
    try:
        is_dir = link.is_dir()
    except OSError:
        is_dir = False
    if is_dir and path_exists(link):
        return link
    cfg = _DRIVE_REPO_ROOT / ".drive-path"
    if path_exists(cfg):
        p = Path(cfg.read_text(encoding="utf-8").strip())
        if path_exists(p):
            return p
    raise DataRootUnavailable(
        "no data root configured (AWIKI_DATA_DIR / drive link / .drive-path) "
        "— read-only resolution refuses to create one")


def _check_data_root(data_root: Path) -> Path:
    root = Path(data_root)
    if not root.is_absolute():
        raise ValueError(f"data root must be absolute (got {root})")
    if root.is_symlink() or is_reparse_point(root):
        raise ValueError("data root must not be a symlink/junction")
    return root


def safe_join_under_root(root: Path, *parts: str) -> Path:
    """R-P5-002 containment-safe join. Refuses, before any read/write:

      - ``..`` / absolute / empty components
      - ANY intermediate or leaf component that is a symlink or Windows
        reparse point (junction), checked with lstat semantics only
      - a final path whose canonical (realpath) resolution escapes the
        canonical data root (catches junctions is_symlink() cannot see)
    """
    root = Path(root)
    cur = root
    for part in parts:
        if not isinstance(part, str) or not part or part in (".", ".."):
            raise StorageUnsafe(f"unsafe path component {part!r}")
        if os.sep in part or "/" in part or "\\" in part or ":" in part:
            raise StorageUnsafe(f"path component must be a single segment: {part!r}")
        cur = cur / part
        if cur.is_symlink() or is_reparse_point(cur):
            raise StorageUnsafe(f"path component is a symlink/reparse point: {cur.name}")
    resolved = Path(os.path.realpath(cur))
    root_resolved = Path(os.path.realpath(root))
    if resolved != root_resolved and root_resolved not in resolved.parents:
        raise StorageUnsafe("resolved path escapes the data root")
    return cur


class ProjectMemoryStore:
    """L2 memory for one attached project, routed through MemoryLedger."""

    def __init__(self, project_root: Path, data_root: Path | None = None,
                 *, read_only: bool = False):
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
        if data_root is not None:
            self._root = _check_data_root(data_root)
        elif read_only:
            self._root = _check_data_root(resolve_data_root_readonly())
        else:
            self._root = _check_data_root(default_data_root())

    # ── paths (containment-checked; R-P5-002) ──
    @property
    def memory_dir(self) -> Path:
        return safe_join_under_root(self._root, "projects", self.project_id, "memory")

    def _entries_path(self) -> Path:
        return safe_join_under_root(
            self._root, "projects", self.project_id, "memory", "entries.jsonl")

    @property
    def experiments_dir(self) -> Path:
        return safe_join_under_root(
            self._root, "projects", self.project_id, "experiments")

    def _ledger(self) -> memory_ledger.MemoryLedger:
        return memory_ledger.MemoryLedger(self._entries_path())

    def _require_scope(self, key: str):
        if self.scopes.get(key) is not True:
            raise ScopeDenied(f"memory.scopes.{key} is not enabled for this project")

    # ── L2 entry API (MemoryLedger seam — R-P5-006) ──
    def append_entry(self, text: str, meta: dict | None = None) -> float:
        """Append one L2 entry; returns the ledger entry ts (its identity).

        Storage goes through MemoryLedger.append → secret redaction
        (recursively applied to meta, R-P5-006) + atomic_json lock-protected
        append. Project tag rides the ledger's namespaced `extra` seam.
        """
        self._require_scope("project")
        meta = meta or {}
        etype = meta.get("type", "lesson")
        if etype not in memory_ledger.VALID_TYPES:
            etype = "lesson"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        # re-verify containment AFTER mkdir (parent creation may traverse)
        safe_join_under_root(self._root, "projects", self.project_id, "memory")
        return self._ledger().append(
            session_id=f"awiki-project:{self.project_id}",
            type=etype,
            summary=text,
            tags=[f"project:{self.project_id}"] + [str(t) for t in meta.get("tags", [])],
            extra={"project": self.project_id, "meta": meta},
        )

    @staticmethod
    def _entry_project(entry: dict) -> str | None:
        extra = entry.get("extra")
        return extra.get("project") if isinstance(extra, dict) else None

    def read_entries(self, query: str, limit: int = 20) -> list[dict]:
        """Ledger-seamed search; only THIS project's entries ever return."""
        self._require_scope("project")
        hits = [e for e in self._ledger().search(query, limit * 3)
                if self._entry_project(e) == self.project_id]
        return hits[:limit]

    def get_entry(self, ts: float) -> dict | None:
        """Fetch one entry by ledger ts — the L2 source identity used by
        the promotion gate (R-P5-001)."""
        self._require_scope("project")
        for e in self._ledger()._load_all():
            if e.get("ts") == ts:
                if self._entry_project(e) != self.project_id:
                    return None  # foreign entry — never a valid source
                return e
        return None

    def count_entries(self) -> int:
        self._require_scope("project")
        return len(self._ledger()._load_all())

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
