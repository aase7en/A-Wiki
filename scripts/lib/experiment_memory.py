"""A-Wiki Memory Plane — L5 Experiment Memory (Phase 5).

Minimum contract (work order §4 L5):

    <data-root>/projects/<project-id>/experiments/<experiment-id>/
    ├── baseline.json      — immutable after initialization
    ├── iterations.jsonl   — append-only
    ├── winner.json        — must reference a recorded iteration
    └── report.md          — human-readable output

Project-isolated: an ExperimentStore bound to project B cannot touch
project A's experiments. Malformed ids/records fail loudly. Storage lives
under the same containment-checked data root as L2. No A-Loop runtime here.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

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


class ExperimentStore:
    def __init__(self, data_root: Path, project_id: str):
        if not _PROJ_ID_RE.match(project_id or ""):
            raise MalformedRecord(f"project id not slug-safe: {project_id!r}")
        root = Path(data_root)
        if not root.is_absolute() or root.is_symlink():
            raise MalformedRecord("data root must be absolute and not a symlink")
        self.project_id = project_id
        self._root = root / "projects" / project_id / "experiments"

    # ── paths ──
    def _exp_dir(self, exp_id: str) -> Path:
        if not _EXP_ID_RE.match(exp_id or ""):
            raise MalformedRecord(f"experiment id malformed: {exp_id!r}")
        return self._root / exp_id

    def _baseline(self, exp_id: str) -> Path:
        return self._exp_dir(exp_id) / "baseline.json"

    def _iterations(self, exp_id: str) -> Path:
        return self._exp_dir(exp_id) / "iterations.jsonl"

    def _winner(self, exp_id: str) -> Path:
        return self._exp_dir(exp_id) / "winner.json"

    def _report(self, exp_id: str) -> Path:
        return self._exp_dir(exp_id) / "report.md"

    def _guard_project_dir(self, exp_id: str) -> Path:
        d = self._exp_dir(exp_id)
        marker = d / ".project"
        if d.exists() and marker.is_file():
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
        (d / ".project").write_text(self.project_id, encoding="utf-8")
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
        d = self._exp_dir(exp_id)
        if d.exists() and (d / ".project").is_file():
            owner = (d / ".project").read_text(encoding="utf-8").strip()
            if owner != self.project_id:
                raise ProjectIsolationError(
                    f"experiment {exp_id} belongs to project {owner!r}, "
                    f"not {self.project_id!r}")
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
