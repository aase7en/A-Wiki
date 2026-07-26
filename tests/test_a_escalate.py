"""Tests for scripts/a_escalate.py (A-Suite C8)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

_spec = importlib.util.spec_from_file_location(
    "a_escalate", REPO_ROOT / "scripts" / "a_escalate.py"
)
esc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(esc)


def args(**over):
    import argparse
    base = dict(goal="make it fast", question="why slow?", constraint=None,
                tried=None, file=None, done=None, no_ledger=True,
                stdout=True, slug=None)
    base.update(over)
    return argparse.Namespace(**base)


class TestRender:
    def test_includes_goal_and_question(self):
        out = esc.render(args())
        assert "make it fast" in out and "why slow?" in out

    def test_states_the_receiver_has_no_session_context(self):
        """The whole point: implicit context is lost, so say so up front."""
        assert "no other context" in esc.render(args())

    def test_constraints_and_done_criteria_are_rendered(self):
        out = esc.render(args(constraint=["no schema change"], done=["p95 < 2s"]))
        assert "no schema change" in out and "p95 < 2s" in out

    def test_tried_items_are_labelled_do_not_re_suggest(self):
        out = esc.render(args(tried=["added an index"]))
        assert "added an index" in out
        assert "do not re-suggest" in out.lower()

    def test_thai_content_survives_rendering(self):
        out = esc.render(args(goal="ทำให้ dashboard เร็วขึ้น", question="ทำไมช้า?"))
        assert "ทำให้ dashboard เร็วขึ้น" in out and "ทำไมช้า?" in out

    def test_file_excerpt_is_embedded(self):
        out = esc.render(args(file=["scripts/skills_registry/routing.py"]))
        assert "routing.py" in out and "A_PHASE_CHAIN" in out

    def test_missing_file_degrades_instead_of_crashing(self):
        out = esc.render(args(file=["does/not/exist.py"]))
        assert "could not read" in out

    def test_no_ledger_omits_the_tried_section_entirely(self):
        assert "Already tried" not in esc.render(args(no_ledger=True))

    def test_asks_for_root_cause_and_disagreement(self):
        """A weak ask gets a weak answer — the pack must invite pushback."""
        out = esc.render(args())
        assert "root cause" in out.lower()
        assert "wrong" in out.lower() or "would NOT do" in out


class TestCleanSummary:
    def test_keeps_a_normal_one_liner(self):
        assert esc._clean_summary("index did not help") == "index did not help"

    def test_takes_only_the_first_line(self):
        assert esc._clean_summary("first line\nsecond line") == "first line"

    def test_drops_shell_and_commit_noise(self):
        for noise in ("$(cat <<'EOF'", "git commit -m foo", "x <<'EOF'"):
            assert esc._clean_summary(noise) == ""

    def test_truncates_very_long_summaries(self):
        out = esc._clean_summary("y" * 400)
        assert len(out) <= 160 and out.endswith("...")

    def test_blank_stays_blank(self):
        assert esc._clean_summary("   ") == ""


class TestSlugify:
    def test_ascii_goal_becomes_a_readable_stem(self):
        assert esc.slugify("Make Dashboard Fast!") == "make-dashboard-fast"

    def test_pure_thai_goal_falls_back_to_a_timestamp(self):
        """Thai has no ASCII to slug, so the stem must not come out empty."""
        out = esc.slugify("ทำให้เร็วขึ้น")
        assert out and "/" not in out and "\\" not in out

    def test_result_is_always_filename_safe(self):
        for bad in ("../../etc/passwd", "a/b\\c", "  "):
            out = esc.slugify(bad)
            assert "/" not in out and "\\" not in out and ".." not in out


class TestCli:
    def test_writes_a_pack_and_creates_the_gitignore(self, tmp_path, monkeypatch):
        monkeypatch.setattr(esc, "OUT_DIR", tmp_path / "escalate")
        monkeypatch.setattr(esc, "REPO_ROOT", tmp_path)
        rc = esc.main(["--goal", "g", "--question", "q", "--no-ledger", "--slug", "pack"])
        assert rc == 0
        out = tmp_path / "escalate" / "pack.md"
        assert out.exists()
        gi = (tmp_path / "escalate" / ".gitignore").read_text(encoding="utf-8")
        assert "*" in gi and "!.gitignore" in gi

    def test_requires_goal_and_question(self):
        with pytest.raises(SystemExit):
            esc.main(["--goal", "only goal"])
