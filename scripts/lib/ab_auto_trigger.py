"""ab_auto_trigger.py — auto-propose A/B experiments from repeated task patterns.

Tier 3 #12. Bridges Neural Spine task_board with the existing ab_routing
infra (R4). When the same task type repeats ≥ N times AND no A/B experiment
covers it yet → draft a proposal (inactive by default, user must enable).

Reuse 100% of ab_routing/ab_rotator/ab_report — this module only:
  - detects patterns (classify_task_patterns)
  - checks if experiment exists (has_experiment)
  - drafts proposal (propose_experiment)
  - writes to ledger as type=idea tagged 'ab-proposal'

Activation is manual (user sets active:true + runs rotator). Auto-trigger
only drafts — never activates (safety + Iron Law #3 user-as-critic).
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import memory_ledger  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO_ROOT / "agents" / "ab-experiments.json"
DEFAULT_LEDGER = REPO_ROOT / ".tmp" / "memory-ledger.jsonl"
DEFAULT_TASKS = REPO_ROOT / ".tmp" / "task-board.json"


def _extract_keyword(goal: str) -> str:
    """Extract the action keyword from a task goal (first word, lowercased).

    'review PR #42' → 'review'
    'summarize the docs' → 'summarize'
    'fix auth bug' → 'fix'
    """
    if not goal:
        return ""
    # First alphanumeric word
    m = re.match(r"\s*([a-zA-Z]+)", goal)
    return m.group(1).lower() if m else ""


def classify_task_patterns(
    tasks_path: Path | str,
    *,
    min_count: int = 3,
) -> list[dict]:
    """Group tasks by goal keyword, return those with count >= min_count.

    Returns [{keyword, count, sample_goals}] sorted by count descending.
    """
    tasks_path = Path(tasks_path)
    if not tasks_path.is_file():
        return []
    try:
        import task_board
        board = task_board.TaskBoard(tasks_path)
        tasks = board.list()
    except Exception:
        return []
    groups: dict[str, list[str]] = {}
    for t in tasks:
        kw = _extract_keyword(t.get("goal", ""))
        if not kw:
            continue
        groups.setdefault(kw, []).append(t.get("goal", ""))
    patterns = [
        {"keyword": kw, "count": len(goals), "sample_goals": goals[:3]}
        for kw, goals in groups.items()
        if len(goals) >= min_count
    ]
    patterns.sort(key=lambda p: p["count"], reverse=True)
    return patterns


def has_experiment(keyword: str, config_path: Path | str) -> bool:
    """Check if ab-experiments.json already has an experiment matching keyword."""
    config_path = Path(config_path)
    if not config_path.is_file():
        return False
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    for exp in config.get("experiments", []):
        subagent = exp.get("subagent", "").lower()
        if keyword.lower() in subagent or subagent in keyword.lower():
            return True
    return False


def propose_experiment(
    *,
    keyword: str,
    count: int,
    sample_goals: list[str],
) -> dict[str, Any]:
    """Draft an A/B experiment proposal for a repeated task pattern.

    Returns a dict matching ab-experiments.json schema. active=False by
    default — user must explicitly enable (Iron Law #3: user is critic).
    """
    samples_str = "; ".join(sample_goals[:3])
    return {
        "subagent": keyword,
        "champion": "current-default",  # placeholder — user fills in real model
        "challenger": "candidate-model",  # placeholder
        "active": False,  # NEVER auto-activate
        "phase_size": 10,
        "total_phases": 4,
        "reason": (
            f"Auto-proposed: task pattern '{keyword}' seen {count}x "
            f"(samples: {samples_str}). Compare current vs candidate model."
        ),
    }


def write_proposal_to_ledger(
    ledger_path: Path | str,
    proposal: dict[str, Any],
) -> None:
    """Write proposal as ledger type=idea tagged 'ab-proposal'."""
    ledger = memory_ledger.MemoryLedger(ledger_path)
    summary = (
        f"A/B PROPOSAL: {proposal['subagent']} — champion={proposal['champion']} "
        f"vs challenger={proposal['challenger']} "
        f"(pattern seen {proposal['phase_size']*2}+x). "
        f"Edit agents/ab-experiments.json + set active:true to enable."
    )
    ledger.append(
        session_id="ab-auto-trigger",
        type="idea",
        summary=summary,
        tags=["ab-proposal", "a-loop", proposal["subagent"]],
    )


def scan_and_propose(
    *,
    tasks_path: Path | str = DEFAULT_TASKS,
    ledger_path: Path | str = DEFAULT_LEDGER,
    config_path: Path | str = DEFAULT_CONFIG,
    min_count: int = 3,
) -> int:
    """End-to-end: scan tasks → find patterns → propose experiments.

    Skips patterns that already have an experiment in config.
    Returns count of proposals written.
    """
    patterns = classify_task_patterns(tasks_path, min_count=min_count)
    if not patterns:
        return 0
    written = 0
    for p in patterns:
        if has_experiment(p["keyword"], config_path):
            continue
        proposal = propose_experiment(
            keyword=p["keyword"],
            count=p["count"],
            sample_goals=p["sample_goals"],
        )
        write_proposal_to_ledger(ledger_path, proposal)
        written += 1
    return written
