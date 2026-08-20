"""Deterministic objective → work-order decomposition (no LLM guessing).

Splitting rules (stable, testable):
  - text after a ':' is the task list body (before ':' is context/prefix)
  - body splits on ',' and the word 'and'
  - no ':' → the whole text is the body
Each task becomes a work-order dict + optional WO file (docs/work-orders/).
"""
from __future__ import annotations

import re
from pathlib import Path

LANE_RULES = [
    (r"scripts/hooks|hooks_runner|registry\.py", "hook-engine"),
    (r"\.github/workflows|scripts/security|scripts/health", "infra-CI"),
    (r"COLLAB|docs/protocols|AGENTS\.md|continuity", "governance"),
    (r"wiki/|gen-index", "wiki-knowledge"),
    (r"scripts/lib/(memory|project|experiment|promotion)", "memory-plane"),
]
DEFAULT_LANE = "migration"

VERIFY_DEFAULT = ("python scripts/security/scan_repo.py --ci --baseline "
                  "scripts/security/baseline.txt && "
                  "python -m pytest tests/ -q")


def _slug(text: str, maxlen: int = 32) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:maxlen] or "task"


def _lane_for(task: str) -> str:
    for pattern, lane in LANE_RULES:
        if re.search(pattern, task, re.I):
            return lane
    return DEFAULT_LANE


def split_objective(objective: str) -> list[str]:
    body = objective.split(":", 1)[1] if ":" in objective else objective
    parts = re.split(r",|\band\b", body)
    return [p.strip(" .;") for p in parts if len(p.strip(" .;")) >= 2]


def plan_objective(objective: str, repo_root: Path | None = None,
                   write: bool = False) -> list[dict]:
    root = Path(repo_root) if repo_root else Path.cwd()
    base = _slug(objective)[:24] or "objective"
    wos: list[dict] = []
    for i, task in enumerate(split_objective(objective), 1):
        wos.append({
            "id": f"WO-{base}-{i:02d}",
            "goal": task,
            "lane": _lane_for(task),
            "verify": VERIFY_DEFAULT,
            "status": "NOT_STARTED",
        })
    if write and wos:
        wo_dir = root / "docs" / "work-orders"
        wo_dir.mkdir(parents=True, exist_ok=True)
        for wo in wos:
            (wo_dir / f"{wo['id']}.md").write_text(
                f"# {wo['id']} — {wo['goal']}\n\n"
                f"- **Lane:** {wo['lane']}\n"
                f"- **Status:** {wo['status']}\n"
                f"- **Verify:** `{wo['verify']}`\n"
                f"- **Checkpoint log:**\n", encoding="utf-8")
    return wos
