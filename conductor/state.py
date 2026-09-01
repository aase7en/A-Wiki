"""Unified read-only status: COLLAB claims + git branches + hard-gate count.

The conductor never mutates anything through this module — status is a
snapshot others (gate/CLI) reason over.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

SCHEMA = "awiki-conductor/v1"


def parse_claims(collab: Path) -> list[dict]:
    """Parse the in-progress claim table from COLLAB.md (tolerant, read-only)."""
    if not collab.is_file():
        return []
    claims: list[dict] = []
    in_table = False
    for line in collab.read_text(encoding="utf-8").splitlines():
        # anchor ONLY on the claims header — COLLAB has other tables (Lanes)
        if line.startswith("|") and "chunk/wo" in line.lower():
            in_table = True
            continue
        if in_table and line.startswith("|") and "chunk/wo" not in line.lower()                 and set(line.replace("|", "").replace("-", "").strip()) <= set(": "):
            continue  # separator row of the claims table
        if not in_table:
            continue
        if not line.strip():
            # Formatting-only blank lines are tolerated inside the claims
            # section; a non-table prose line still terminates the section.
            continue
        if not line.strip().startswith("|"):
            in_table = False
            continue
        if line.lower().startswith("| lane"):
            in_table = False  # a different table starts
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4 or cells[0].startswith("_"):
            continue
        claims.append({
            "chunk": cells[0],
            "agent": cells[1] if len(cells) > 1 else "",
            "claimed": cells[2] if len(cells) > 2 else "",
            "scope": cells[3] if len(cells) > 3 else "",
            "branch": cells[4] if len(cells) > 4 else "",
        })
    return claims


def list_branches(repo_root: Path) -> list[str]:
    try:
        out = subprocess.run(
            ["git", "branch", "--format=%(refname:short)"],
            capture_output=True, text=True, timeout=15, cwd=str(repo_root),
        )
    except (OSError, subprocess.SubprocessError):
        return []
    return [b for b in out.stdout.split() if b]


def count_hard_gates(repo_root: Path) -> int:
    sys_path = repo_root / "scripts" / "hooks"
    if not sys_path.is_dir():
        return 0
    import sys
    inserted = str(sys_path)
    if inserted not in sys.path:
        sys.path.insert(0, inserted)
    try:
        import registry  # type: ignore
    except Exception:
        return 0
    return sum(1 for e in registry.HOOK_REGISTRY.values()
               if e.get("classification") == "hard")


def conductor_status(repo_root: Path | None = None) -> dict:
    root = Path(repo_root) if repo_root else Path.cwd()
    return {
        "schema": SCHEMA,
        "repo": root.name,
        "claims": parse_claims(root / "COLLAB.md"),
        "branches": list_branches(root),
        "gate_tools": count_hard_gates(root),
    }
