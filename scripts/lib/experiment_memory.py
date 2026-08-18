"""A-Wiki Memory Plane — L5 Experiment Memory (Phase 5).

Minimum contract (work order §4 L5):

    <data-root>/projects/<project-id>/experiments/<experiment-id>/
    ├── baseline.json      — immutable after initialization
    ├── iterations.jsonl   — append-only
    ├── winner.json        — must reference a recorded iteration
    └── report.md          — human-readable output

R-P5-003: project identity is ADAPTER-AUTHORITATIVE. The store is bound to
a project ROOT whose Phase-4 adapter (.awiki/project.yaml) must validate;
the project id is derived from that adapter, and any caller-supplied id
that disagrees is rejected BEFORE any storage is touched. An explicit id
parameter may only ever re-state the adapter's own id.

R-P5-002: every path below the data root is component-wise
symlink/reparse-checked and resolved-containment-checked before any read
or write (shared helper ``project_memory.safe_join_under_root``).

Malformed ids/records fail loudly. No A-Loop runtime here.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "project"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from project_memory import (       # noqa: E402 -- one shared contract
    AdapterInvalid, ScopeDenied, StorageUnsafe, safe_join_under_root,
    _check_data_root, default_data_root, resolve_data_root_readonly,
)

_EXP_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_PROJ_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


class BaselineImmutable(Exception):
    pass


class AppendOnly(Exception):
    pass


class WinnerValidationError(Exception):
    pass


class MalformedRecord(Exception):
    pass


class ProjectIsolationError(Exception):
    pass


def _validate_adapter(project_root: Path) -> dict:
    import validate as project_validate
    result = project_validate.validate(project_root)
    if result.exit_code() != 0:
        raise AdapterInvalid(
            "project adapter invalid (fail closed): " + "; ".join(result.errors[:3]))
    import yaml
    data = yaml.safe_load(
        (project_root / ".awiki" / "project.yaml").read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AdapterInvalid("project.yaml is not a mapping (fail closed)")
    return data


class ExperimentStore:
    """L5 experiments for exactly ONE attached project (adapter-bound)."""

    def __init__(self, project_root: Path, data_root: Path | None = None,
                 *, project_id: str | None = None, read_only: bool = False):
        project_root = Path(project_root).resolve()
        data = _validate_adapter(project_root)          # fail closed first
        pid = data.get("id")
        if not isinstance(pid, str) or not _PROJ_ID_RE.match(pid):
            raise AdapterInvalid(f"project id not slug-safe: {pid!r}")
        # R-P5-003: a caller-supplied id may only re-state the adapter's own
        # id — anything else is a cross-project access attempt, rejected
        # BEFORE any storage path is touched.
        if project_id is not None and project_id != pid:
            raise ProjectIsolationError(
                f"refused: adapter project is {pid!r}, caller asserted {project_id!r} "
                f"— L5 identity comes from the Phase-4 adapter, not the caller")
        scopes = (data.get("memory") or {}).get("scopes") or {}
        if scopes.get("project") is not True:
            raise ScopeDenied("memory.scopes.project is not enabled for this project")

        if data_root is not None:
            root = _check_data_root(data_root)
        elif read_only:
            root = _check_data_root(resolve_data_root_readonly())
        else:
            root = _check_data_root(default_data_root())
        self.project_id = pid
        self._root = root

    # ── paths (containment-checked; R-P5-002) ──
    def _exp_dir(self, exp_id: str) -> Path:
        if not _EXP_ID_RE.match(exp_id or ""):
            raise MalformedRecord(f"experiment id malformed: {exp_id!r}")
        return safe_join_under_root(
            self._root, "projects", self.project_id, "experiments", exp_id)

    def _file(self, exp_id: str, name: str) -> Path:
        if not _EXP_ID_RE.match(exp_id or ""):
            raise MalformedRecord(f"experiment id malformed: {exp_id!r}")
        return safe_join_under_root(
            self._root, "projects", self.project_id, "experiments", exp_id, name)

    def _baseline(self, exp_id: str) -> Path:
        return self._file(exp_id, "baseline.json")

    def _iterations(self, exp_id: str) -> Path:
        return self._file(exp_id, "iterations.jsonl")

    def _winner(self, exp_id: str) -> Path:
        return self._file(exp_id, "winner.json")

    def _report(self, exp_id: str) -> Path:
        return self._file(exp_id, "report.md")

    def _guard_project_dir(self, exp_id: str) -> Path:
        """Containment check first (raises StorageUnsafe), then ownership."""
        d = self._exp_dir(exp_id)
        marker = d / ".project"
        if marker.exists() and not marker.is_symlink():
            owner = marker.read_text(encoding="utf-8").strip()
            if owner != self.project_id:
                raise ProjectIsolationError(
                    f"experiment {exp_id} belongs to project {owner!r}, not {self.project_id!r}")
        return d

    # ── lifecycle ──
    def initialize(self, exp_id: str, baseline: dict) -> Path:
        if not isinstance(baseline, dict) or not baseline:
            raise MalformedRecord("baseline must be a non-empty mapping")
        d = self._guard_project_dir(exp_id)
        if self._baseline(exp_id).is_file():
            raise BaselineImmutable(f"baseline for {exp_id} already exists — immutable")
        d.mkdir(parents=True, exist_ok=True)
        safe_join_under_root(
            self._root, "projects", self.project_id, "experiments", exp_id)
        marker = self._file(exp_id, ".project")
        marker.write_text(self.project_id, encoding="utf-8")
        payload = {"experiment_id": exp_id, "project": self.project_id,
                   "initialized_at": datetime.now(timezone.utc).isoformat(),
                   "baseline": baseline}
        self._baseline(exp_id).write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        self._iterations(exp_id).write_text("", encoding="utf-8")
        return self._baseline(exp_id)

    def append_iteration(self, exp_id: str, record: dict) -> int:
        if not isinstance(record, dict) or not record:
            raise MalformedRecord("iteration must be a non-empty mapping")
        d = self._guard_project_dir(exp_id)
        if not self._baseline(exp_id).is_file():
            raise MalformedRecord(f"experiment {exp_id} not initialized")
        d.mkdir(parents=True, exist_ok=True)
        with self._iterations(exp_id).open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return len(self.read_iterations(exp_id))

    def overwrite_iteration(self, exp_id: str, index: int, record: dict):
        raise AppendOnly("iterations.jsonl is append-only — rewriting is forbidden")

    def read_iterations(self, exp_id: str) -> list[dict]:
        self._guard_project_dir(exp_id)
        p = self._iterations(exp_id)
        if not p.is_file():
            return []
        out = []
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise MalformedRecord(f"corrupt iteration line: {e}") from e
        return out

    def set_winner(self, exp_id: str, iteration_index: int) -> Path:
        iters = self.read_iterations(exp_id)
        if not (0 <= iteration_index < len(iters)):
            raise WinnerValidationError(
                f"winner must reference a recorded iteration (index {iteration_index} "
                f"out of range for {len(iters)} iteration(s))")
        payload = {"experiment_id": exp_id, "project": self.project_id,
                   "iteration_index": iteration_index,
                   "winning_record": iters[iteration_index]}
        self._winner(exp_id).write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return self._winner(exp_id)

    def read_winner(self, exp_id: str) -> dict:
        p = self._winner(exp_id)
        if not p.is_file():
            raise WinnerValidationError(f"no winner recorded for {exp_id}")
        return json.loads(p.read_text(encoding="utf-8"))

    def write_report(self, exp_id: str, markdown: str) -> Path:
        self._guard_project_dir(exp_id)
        p = self._report(exp_id)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(markdown, encoding="utf-8")
        return p
