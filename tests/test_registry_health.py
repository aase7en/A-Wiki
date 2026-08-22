"""Registry health invariants — defect #3/#4 (auto-skill plan §4).

User-journey contract: registry paths must resolve on EVERY clone, not just
the machine that happened to install a skill into ~/.claude or ~/.codex.
Machine-dependent entries without a tracked in-repo copy must carry
status "deprecated" (schema has no "archived") so every generated surface skips them.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY = REPO_ROOT / "skills-registry.json"


@pytest.fixture(scope="module")
def registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def test_no_live_machine_dependent_paths(registry):
    """defect #3: live entries must not point at ~/.claude|~/.codex."""
    bad = [s["name"] for s in registry["skills"]
           if str(s.get("path", "")).startswith("~")
           and s.get("status") != "deprecated"]
    assert bad == [], f"machine-dependent paths on non-deprecated skills: {bad}"


def test_live_paths_resolve_inside_repo(registry):
    """defect #3 (strong form): every live path must exist in the repo."""
    missing = []
    for s in registry["skills"]:
        if s.get("status") == "deprecated":
            continue
        p = s.get("path", "")
        if p and not (REPO_ROOT / p).is_file():
            missing.append(f"{s['name']}: {p}")
    assert missing == [], f"live registry paths that do not exist here: {missing[:10]}"


def test_no_empty_descriptions_on_live_skills(registry):
    """defect #4: description is the tier-2 routing surface — empty = unroutable."""
    empty = [s["name"] for s in registry["skills"]
             if not str(s.get("description", "")).strip()
             and s.get("status") != "deprecated"]
    assert empty == [], f"live skills with empty descriptions: {empty}"


def test_archived_entries_documented(registry):
    """Deprecated skills must say why (grep-able history, never silent deletion)."""
    for s in registry["skills"]:
        if s.get("status") == "deprecated":
            note = str(s.get("note", s.get("archived_reason", ""))).strip()
            assert note, f"deprecated skill {s['name']} has no reason note"
