"""Tests for scripts/live-dashboard/suite_editor.py — eval suite generator (X3).

Iron Law #1: failing tests written FIRST.

X3 สร้าง/แก้ eval suite จาก dashboard form → validate + atomic write.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "live-dashboard"))

import suite_editor  # noqa: E402  -- module under test (created by X3)


# ---------------------------------------------------------------------------
# 1. validate_suite_name — kebab-case only
# ---------------------------------------------------------------------------
def test_validate_suite_name_accepts_kebab_case():
    assert suite_editor.validate_suite_name("medical") is True
    assert suite_editor.validate_suite_name("ai-ops") is True
    assert suite_editor.validate_suite_name("thought-partner") is True


def test_validate_suite_name_rejects_uppercase():
    assert suite_editor.validate_suite_name("Medical") is False
    assert suite_editor.validate_suite_name("AI-Ops") is False


def test_validate_suite_name_rejects_spaces():
    assert suite_editor.validate_suite_name("med ical") is False
    assert suite_editor.validate_suite_name("med ical") is False


def test_validate_suite_name_rejects_path_traversal():
    assert suite_editor.validate_suite_name("../etc/passwd") is False
    assert suite_editor.validate_suite_name("foo/bar") is False
    assert suite_editor.validate_suite_name("..") is False


def test_validate_suite_name_rejects_empty():
    assert suite_editor.validate_suite_name("") is False
    assert suite_editor.validate_suite_name("   ") is False


# ---------------------------------------------------------------------------
# 2. validate_suite — reject stages key (pipeline suite — กันทับ DAG)
# ---------------------------------------------------------------------------
def test_validate_suite_rejects_stages_key():
    """Suite ที่มี 'stages' key = pipeline (DAG) — ห้าม save ทับ."""
    suite = {"suite": "x", "stages": [...], "cases": []}
    errors = suite_editor.validate_suite(suite)
    assert any("stages" in e.lower() or "pipeline" in e.lower() for e in errors)


def test_validate_suite_accepts_normal_suite():
    """Suite ปกติ (cases only) → no errors."""
    suite = {
        "suite": "test-suite",
        "description": "A test",
        "cases": [{"id": "c1", "subagent": "x", "prompt": "do", "required": ["a"], "forbidden": []}],
    }
    errors = suite_editor.validate_suite(suite)
    assert errors == []


# ---------------------------------------------------------------------------
# 3. validate_case — required fields
# ---------------------------------------------------------------------------
def test_validate_case_requires_id_subagent_prompt():
    """Case ต้องมี id + subagent + prompt."""
    # missing id
    errors = suite_editor.validate_case({"subagent": "x", "prompt": "y"})
    assert any("id" in e for e in errors)
    # missing subagent
    errors = suite_editor.validate_case({"id": "c1", "prompt": "y"})
    assert any("subagent" in e for e in errors)
    # missing prompt
    errors = suite_editor.validate_case({"id": "c1", "subagent": "x"})
    assert any("prompt" in e for e in errors)


def test_validate_case_complete_no_errors():
    case = {"id": "c1", "subagent": "x", "prompt": "do something", "required": ["a"], "forbidden": ["b"]}
    assert suite_editor.validate_case(case) == []


# ---------------------------------------------------------------------------
# 4. write_suite — atomic roundtrip
# ---------------------------------------------------------------------------
def test_write_suite_atomic_roundtrip(tmp_path):
    """write → read → match."""
    suite = {
        "suite": "roundtrip-test",
        "description": "Test",
        "cases": [{"id": "c1", "subagent": "x", "prompt": "hello", "required": ["h"], "forbidden": []}],
    }
    suite_editor.write_suite(suite, suites_dir=tmp_path)
    # file exists
    assert (tmp_path / "roundtrip-test.json").is_file()
    # read back
    loaded = json.loads((tmp_path / "roundtrip-test.json").read_text(encoding="utf-8"))
    assert loaded["suite"] == "roundtrip-test"
    assert loaded["cases"][0]["prompt"] == "hello"


def test_write_suite_rejects_invalid_name(tmp_path):
    """Invalid name → raise ValueError, no file written."""
    suite = {"suite": "../bad", "description": "", "cases": []}
    with pytest.raises(ValueError):
        suite_editor.write_suite(suite, suites_dir=tmp_path)
    assert not (tmp_path / "../bad.json").exists()


# ---------------------------------------------------------------------------
# 5. parse comma-separated required/forbidden
# ---------------------------------------------------------------------------
def test_parse_comma_separated():
    """'a, b, c' → ['a', 'b', 'c'] (trim whitespace, drop empty)."""
    assert suite_editor.parse_comma_list("a, b, c") == ["a", "b", "c"]
    assert suite_editor.parse_comma_list("single") == ["single"]
    assert suite_editor.parse_comma_list("") == []
    assert suite_editor.parse_comma_list("a,,b,") == ["a", "b"]  # drop empties


# ---------------------------------------------------------------------------
# 6. load_suite_by_name — read existing
# ---------------------------------------------------------------------------
def test_load_suite_by_name(tmp_path):
    """Load a suite file by name → parsed dict."""
    (tmp_path / "my-suite.json").write_text(
        json.dumps({"suite": "my-suite", "cases": []}), encoding="utf-8")
    loaded = suite_editor.load_suite_by_name("my-suite", suites_dir=tmp_path)
    assert loaded is not None
    assert loaded["suite"] == "my-suite"


def test_load_suite_not_found(tmp_path):
    """Missing suite → None."""
    assert suite_editor.load_suite_by_name("nonexistent", suites_dir=tmp_path) is None


# ---------------------------------------------------------------------------
# 7. list_subagents — from agents/subagents/*.md
# ---------------------------------------------------------------------------
def test_list_subagents_returns_list(tmp_path):
    """list_subagents() ต้อง return list of names (without .md)."""
    # Create fake agents dir
    agents_dir = tmp_path / "subagents"
    agents_dir.mkdir()
    (agents_dir / "agent-a.md").write_text("---\nname: a\n---\n", encoding="utf-8")
    (agents_dir / "agent-b.md").write_text("---\nname: b\n---\n", encoding="utf-8")
    (agents_dir / "README.md").write_text("readme", encoding="utf-8")
    names = suite_editor.list_subagents(agents_dir=agents_dir)
    assert "agent-a" in names
    assert "agent-b" in names
    assert "README" not in names  # exclude README
