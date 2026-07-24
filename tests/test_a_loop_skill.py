"""Tests for A-Loop skill registration + SKILL.md shape.

Iron Law #1: failing tests written FIRST.
Iron Law #9: skill registry is single source of truth.

a-loop ต้อง:
  - ลงทะเบียนใน skills-registry.json (ก่อน SKILL.md write — hook enforce)
  - SKILL.md มี frontmatter ครบ (name, description, domain, ...)
  - SKILL.md สั้น (<200 บรรทัด — A- suite convention)
  - references/ แยก phase (progressive disclosure)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_PATH = REPO_ROOT / "skills" / "awiki" / "a-loop" / "SKILL.md"
REGISTRY_PATH = REPO_ROOT / "skills-registry.json"


def _load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _find_skill_entry(name: str) -> dict | None:
    reg = _load_registry()
    for e in reg.get("skills", []):
        if e.get("name") == name:
            return e
    return None


# ---------------------------------------------------------------------------
# 1. registry — a-loop must be registered
# ---------------------------------------------------------------------------
def test_a_loop_registered_in_registry():
    """Iron Law #9: skill must be in skills-registry.json."""
    entry = _find_skill_entry("a-loop")
    assert entry is not None, (
        "a-loop not in skills-registry.json — run new-skill.py or add entry. "
        "check_skill_registry.py hook will block SKILL.md write without this."
    )


def test_a_loop_entry_has_required_fields():
    """Registry entry must have the schema fields other A- skills have."""
    entry = _find_skill_entry("a-loop")
    if entry is None:
        pytest.skip("a-loop not registered yet")
    required = {"name", "domain", "lifecycle_phase", "category", "agents",
                "invocation", "status", "path", "source"}
    missing = required - set(entry.keys())
    assert not missing, f"a-loop registry entry missing fields: {missing}"


def test_a_loop_entry_uses_a_suite_conventions():
    """Match A- suite: domain=engineering, lifecycle_phase=meta, category=pipeline."""
    entry = _find_skill_entry("a-loop")
    if entry is None:
        pytest.skip("a-loop not registered yet")
    assert entry["lifecycle_phase"] == "meta", "A- skills are meta (orchestrators)"
    assert entry["category"] == "pipeline", "A- skills are pipeline aggregators"
    assert "all" in entry.get("agents", []), "A- skills target all agents"


# ---------------------------------------------------------------------------
# 2. SKILL.md — exists, valid frontmatter, under 200 lines
# ---------------------------------------------------------------------------
def test_skill_md_exists():
    assert SKILL_PATH.is_file(), f"SKILL.md missing at {SKILL_PATH}"


def test_skill_md_has_frontmatter():
    if not SKILL_PATH.is_file():
        pytest.skip("SKILL.md not created yet")
    content = SKILL_PATH.read_text(encoding="utf-8")
    assert content.startswith("---"), "SKILL.md must start with frontmatter"
    # frontmatter closes with second ---
    parts = content.split("---", 2)
    assert len(parts) >= 3, "SKILL.md frontmatter not properly closed"


def test_skill_md_under_200_lines():
    """A- suite convention: keep SKILL.md thin (<200 lines).

    Long content goes in references/ (progressive disclosure).
    """
    if not SKILL_PATH.is_file():
        pytest.skip("SKILL.md not created yet")
    lines = SKILL_PATH.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 200, (
        f"SKILL.md is {len(lines)} lines — A- suite caps at 200. "
        f"Move detail to references/*.md."
    )


# ---------------------------------------------------------------------------
# 3. references/ — progressive disclosure phases
# ---------------------------------------------------------------------------
def test_references_dir_exists():
    ref_dir = SKILL_PATH.parent / "references"
    assert ref_dir.is_dir(), "references/ dir missing"


def test_phase_decompose_reference_exists():
    ref = SKILL_PATH.parent / "references" / "phase-decompose.md"
    assert ref.is_file(), "phase-decompose.md missing"


# ---------------------------------------------------------------------------
# 4. surfaces — regen produces 0 drift after registration
# ---------------------------------------------------------------------------
def test_no_surface_drift():
    """regen-skill-surfaces.py --check must pass after adding a-loop."""
    import subprocess
    r = subprocess.run(
        ["python3", "scripts/regen-skill-surfaces.py", "--check"],
        cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 0, (
        f"surface drift detected:\n{r.stdout}\n{r.stderr}\n"
        f"run: python scripts/regen-skill-surfaces.py"
    )
