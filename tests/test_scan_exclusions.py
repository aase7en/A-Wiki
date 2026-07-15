"""Tests for skills_registry/scan.py path-exclusion rules (Iron Law #1 — failing first).

I1: docs/protocols/skill-frontmatter-schema.md (D2) documents that ``examples/``
and ``references/`` subdirs "do not affect registry", but ``scan.py`` did not
enforce this — a stray ``SKILL.md`` in ``examples/`` would be silently picked
up (and then swallowed by name-dedup). These tests pin the enforcement.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from skills_registry.scan import find_skill_files  # noqa: E402


# Minimal valid SKILL.md frontmatter for the fixtures below.
_SKILL_MD = """---
name: {name}
description: fixture skill
domain: general
lifecycle_phase: build
status: active
---

# {name}
"""


def _make_skill(parent: Path, name: str) -> Path:
    """Create a minimal SKILL.md under parent/<name>/ and return its path."""
    d = parent / name
    d.mkdir(parents=True, exist_ok=True)
    skill_md = d / "SKILL.md"
    skill_md.write_text(_SKILL_MD.format(name=name), encoding="utf-8")
    return skill_md


@pytest.fixture
def isolated_repo(tmp_path: Path, monkeypatch) -> Path:
    """A fake repo root with skills/ + agent-skills/ and an empty fake home.

    Isolates find_skill_files() from the real machine's ~/.claude/skills etc.
    so the test only sees what we explicitly create under tmp_path.
    """
    (tmp_path / "skills").mkdir()
    (tmp_path / "agent-skills").mkdir()
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    # Neutralise the external-surface scan (Path.home() at scan.py:212).
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    return tmp_path


class TestScanSubdirExclusions:
    """I1: examples/references/ subdirs must not be scanned as skills."""

    def test_examples_subdir_skill_not_discovered(self, isolated_repo: Path) -> None:
        """A SKILL.md placed under examples/ must be skipped by the scanner."""
        repo = isolated_repo
        # Legitimate top-level skill — should be discovered.
        _make_skill(repo / "skills", "my-real-skill")
        # Stray SKILL.md inside examples/ — must NOT be discovered.
        _make_skill(repo / "skills" / "my-real-skill" / "examples", "stray-example")

        found = find_skill_files(repo)
        names = {item["name"] for item in found}

        assert "my-real-skill" in names, "real skill should be discovered"
        assert "stray-example" not in names, (
            "SKILL.md under examples/ must be excluded (I1) — found: " + ", ".join(sorted(names))
        )

    def test_references_subdir_skill_not_discovered(self, isolated_repo: Path) -> None:
        """A SKILL.md placed under references/ must be skipped by the scanner."""
        repo = isolated_repo
        _make_skill(repo / "skills", "alpha")
        _make_skill(repo / "skills" / "alpha" / "references", "stray-ref")

        found = find_skill_files(repo)
        names = {item["name"] for item in found}

        assert "alpha" in names
        assert "stray-ref" not in names, (
            "SKILL.md under references/ must be excluded (I1) — found: " + ", ".join(sorted(names))
        )

    def test_upstream_and_deprecated_still_excluded(self, isolated_repo: Path) -> None:
        """Regression guard: the pre-existing _upstream/ and deprecated/ exclusions
        must still work after adding examples/references/ to the same filter."""
        repo = isolated_repo
        _make_skill(repo / "skills", "kept")
        _make_skill(repo / "skills" / "_upstream" / "vendored", "vendored-skill")
        _make_skill(repo / "skills" / "deprecated" / "old", "old-skill")

        found = find_skill_files(repo)
        names = {item["name"] for item in found}

        assert "kept" in names
        assert "vendored-skill" not in names
        assert "old-skill" not in names
