"""
test_skill_learning.py — tests for scripts/lib/skill_learning.py

Self-learning skill loop: on SessionStart, detect recurring work patterns
across sessions (private journal log.md + hook telemetry
.tmp/live-events.jsonl) and, when a pattern recurs in >= N distinct
sessions with no existing skill covering it, print a short suggestion
notice pointing the human to `scripts/new-skill.py`. Human approval stays
manual — this module only proposes, never scaffolds anything itself.

Any failure (missing files, corrupt JSON, unwritable cache) must degrade to
returning [] from check_skill_patterns() — never raise.

Iron Law #1: these tests are written before scripts/lib/skill_learning.py
exists / before its logic is correct.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import skill_learning as sl  # noqa: E402


def _session(date: str, topic: str, body: str = "") -> "sl.LogSession":
    return sl.LogSession(date=date, topic=topic, body=body)


def _repeating_log(terms: list[str], n_sessions: int = 3) -> str:
    """Build a minimal log.md-shaped text where every session's body
    contains all of `terms`, across `n_sessions` distinct session headers."""
    lines = []
    for i in range(1, n_sessions + 1):
        lines.append(f"## [2026-01-0{i}] session | Session {i}")
        lines.append(" ".join(terms))
        lines.append("")
    return "\n".join(lines)


# ── parse_log_sessions ──────────────────────────────────────────────────

class TestParseLogSessions:
    def test_header_variant_pipe_with_session_label(self):
        text = (
            "## [2026-07-12] session | token-save: compaction-suggest hook "
            "+ lean SessionStart (Work PC, Claude Code Fable 5)\n"
            "body text here\n"
        )
        sessions = sl.parse_log_sessions(text)
        assert len(sessions) == 1
        assert sessions[0].date == "2026-07-12"
        assert sessions[0].topic == (
            "token-save: compaction-suggest hook + lean SessionStart "
            "(Work PC, Claude Code Fable 5)"
        )

    def test_header_variant_session_dash_2(self):
        text = (
            "## [2026-07-11] session-2 | Hygiene + sister-repo check "
            "+ EN-name purge (ภาคเย็น)\n"
            "body\n"
        )
        sessions = sl.parse_log_sessions(text)
        assert len(sessions) == 1
        assert sessions[0].date == "2026-07-11"
        assert sessions[0].topic.startswith("Hygiene + sister-repo check")

    def test_header_variant_time_and_emdash_no_pipe(self):
        text = "## [2026-07-11 10:30] — some-title\nbody\n"
        sessions = sl.parse_log_sessions(text)
        assert len(sessions) == 1
        assert sessions[0].date == "2026-07-11 10:30"
        assert "some-title" in sessions[0].topic

    def test_topic_without_pipe_uses_remainder_after_bracket(self):
        text = "## [2026-01-01] Just a title, no pipe\nbody\n"
        sessions = sl.parse_log_sessions(text)
        assert len(sessions) == 1
        assert sessions[0].topic == "Just a title, no pipe"

    def test_body_captured_until_next_header(self):
        text = (
            "## [2026-01-01] session | Alpha\n"
            "line one\n"
            "line two\n"
            "\n"
            "## [2026-01-02] session | Beta\n"
            "line three\n"
        )
        sessions = sl.parse_log_sessions(text)
        assert len(sessions) == 2
        assert sessions[0].topic == "Alpha"
        assert "line one" in sessions[0].body
        assert "line two" in sessions[0].body
        assert "line three" not in sessions[0].body
        assert sessions[1].topic == "Beta"
        assert "line three" in sessions[1].body

    def test_preamble_before_first_header_ignored(self):
        text = (
            "drive/personal/journal/log.md — symlink-target preamble line\n"
            "some random preamble text, not a header\n"
            "## [2026-01-01] session | Alpha\n"
            "real body line\n"
        )
        sessions = sl.parse_log_sessions(text)
        assert len(sessions) == 1
        assert sessions[0].topic == "Alpha"
        assert "preamble" not in sessions[0].body
        assert "drive/personal" not in sessions[0].body

    def test_empty_text_returns_empty_list(self):
        assert sl.parse_log_sessions("") == []

    def test_no_headers_at_all_returns_empty_list(self):
        assert sl.parse_log_sessions("just some text\nwith no headers\n") == []


# ── extract_terms ────────────────────────────────────────────────────────

class TestExtractTerms:
    def test_kebab_compound_found_in_topic_and_body(self):
        session = _session(
            "2026-01-01", "token-save improvements", "added compaction-suggest support"
        )
        terms = sl.extract_terms(session)
        assert "token-save" in terms
        assert "compaction-suggest" in terms

    def test_single_generic_words_ignored(self):
        session = _session("2026-01-01", "hook lean SessionStart", "added support for things")
        assert sl.extract_terms(session) == set()

    def test_thai_text_ignored_without_crash(self):
        session = _session(
            "2026-01-01",
            "เพิ่มฟีเจอร์ใหม่",
            "ทดสอบระบบภาษาไทย",
        )
        assert sl.extract_terms(session) == set()

    def test_stopwords_filtered(self):
        session = _session(
            "2026-01-01", "session-memory update", "also touched cost-tier logic"
        )
        terms = sl.extract_terms(session)
        assert "session-memory" not in terms
        assert "cost-tier" in terms

    def test_case_folding(self):
        session = _session("2026-01-01", "COST-TIER declaration", "")
        terms = sl.extract_terms(session)
        assert "cost-tier" in terms

    def test_single_char_kebab_part_not_matched(self):
        session = _session("2026-01-01", "x-ray scan result", "")
        assert "x-ray" not in sl.extract_terms(session)

    def test_all_default_stopwords_are_actually_filtered(self):
        body = " ".join(sl.STOPWORDS)
        session = _session("2026-01-01", "misc", body)
        assert sl.extract_terms(session) == set()


# ── suggest_from_log ────────────────────────────────────────────────────

class TestSuggestFromLog:
    def test_term_repeated_in_same_session_counts_once(self):
        sessions = [
            _session("2026-01-01", "A", "cost-tier cost-tier cost-tier"),
            _session("2026-01-02", "B", "cost-tier"),
            _session("2026-01-03", "C", "cost-tier"),
        ]
        result = sl.suggest_from_log(sessions, {"skills": []}, min_sessions=3)
        assert len(result) == 1
        assert result[0].count == 3
        assert result[0].pattern == "cost-tier"

    def test_threshold_boundary_n_minus_1_no_n_yes(self):
        two = [
            _session("2026-01-01", "A", "cost-tier"),
            _session("2026-01-02", "B", "cost-tier"),
        ]
        assert sl.suggest_from_log(two, {"skills": []}, min_sessions=3) == []

        three = two + [_session("2026-01-03", "C", "cost-tier")]
        result = sl.suggest_from_log(three, {"skills": []}, min_sessions=3)
        assert len(result) == 1

    def test_registry_coverage_by_name(self):
        sessions = [
            _session(f"2026-01-0{i}", f"S{i}", "cost-tier") for i in range(1, 4)
        ]
        registry = {"skills": [{"name": "cost-tier", "aliases": [], "description": ""}]}
        assert sl.suggest_from_log(sessions, registry, min_sessions=3) == []

    def test_registry_coverage_by_alias(self):
        sessions = [
            _session(f"2026-01-0{i}", f"S{i}", "cost-tier") for i in range(1, 4)
        ]
        registry = {
            "skills": [{"name": "cost-gate", "aliases": ["cost-tier"], "description": ""}]
        }
        assert sl.suggest_from_log(sessions, registry, min_sessions=3) == []

    def test_registry_coverage_by_description_substring(self):
        sessions = [
            _session(f"2026-01-0{i}", f"S{i}", "cost-tier") for i in range(1, 4)
        ]
        registry = {
            "skills": [
                {"name": "cost-gate", "aliases": [], "description": "handles cost-tier declarations"}
            ]
        }
        assert sl.suggest_from_log(sessions, registry, min_sessions=3) == []

    def test_short_name_substring_does_not_cover_non_segment(self):
        # Real registry has short skill names (ck, pdf, seo, tdd, run...).
        # "ck" is a substring of "check-privacy" but NOT a hyphen-segment —
        # it must not silently swallow the suggestion.
        registry = {"skills": [{"name": "ck", "aliases": [], "description": ""}]}
        assert sl.registry_covered("check-privacy", registry) is False

    def test_short_name_covers_when_full_segment(self):
        # "tdd" IS a full segment of "tdd-workflow" → correct suppression.
        registry = {"skills": [{"name": "tdd", "aliases": [], "description": ""}]}
        assert sl.registry_covered("tdd-workflow", registry) is True

    def test_segment_run_covers_both_directions(self):
        # needle's segments appear as a contiguous run inside the name…
        registry = {"skills": [{"name": "cost-tier-analysis", "aliases": [], "description": ""}]}
        assert sl.registry_covered("cost-tier", registry) is True
        # …and the name's segments appear as a contiguous run inside the needle.
        registry2 = {"skills": [{"name": "cost-tier", "aliases": [], "description": ""}]}
        assert sl.registry_covered("cost-tier-gate", registry2) is True

    def test_non_contiguous_segments_do_not_cover(self):
        # {cost, gate} is not a contiguous run of {cost, tier, gate}.
        registry = {"skills": [{"name": "cost-gate", "aliases": [], "description": ""}]}
        assert sl.registry_covered("cost-tier-gate", registry) is False

    def test_uncovered_term_still_suggested_alongside_covered(self):
        sessions = [
            _session(f"2026-01-0{i}", f"S{i}", "cost-tier fizz-buzz") for i in range(1, 4)
        ]
        registry = {"skills": [{"name": "cost-tier", "aliases": [], "description": ""}]}
        result = sl.suggest_from_log(sessions, registry, min_sessions=3)
        patterns = {s.pattern for s in result}
        assert "fizz-buzz" in patterns
        assert "cost-tier" not in patterns

    def test_hint_format_points_at_new_skill_script(self):
        sessions = [
            _session(f"2026-01-0{i}", f"S{i}", "cost-tier") for i in range(1, 4)
        ]
        result = sl.suggest_from_log(sessions, {"skills": []}, min_sessions=3)
        assert "scripts/new-skill.py cost-tier" in result[0].hint
        assert result[0].kind == "log-pattern"

    def test_sorted_by_count_desc_then_name(self):
        sessions = []
        for i in range(1, 5):
            sessions.append(_session(f"2026-01-0{i}", f"S{i}", "alpha-term bravo-term"))
        sessions.append(_session("2026-02-01", "S5", "alpha-term"))
        result = sl.suggest_from_log(sessions, {"skills": []}, min_sessions=3)
        assert [s.pattern for s in result] == ["alpha-term", "bravo-term"]
        assert result[0].count == 5
        assert result[1].count == 4


# ── suggest_from_events ─────────────────────────────────────────────────

class TestSuggestFromEvents:
    def _write(self, tmp_path: Path, lines: list[str]) -> Path:
        path = tmp_path / "live-events.jsonl"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def test_threshold_reached_produces_suggestion(self, tmp_path):
        lines = [
            json.dumps({"type": "hook_check", "hook": "check_cost_tier", "result": "block"})
            for _ in range(5)
        ]
        path = self._write(tmp_path, lines)
        result = sl.suggest_from_events(path, threshold=5)
        assert len(result) == 1
        assert result[0].pattern == "check_cost_tier"
        assert result[0].kind == "hook-friction"
        assert result[0].count == 5

    def test_all_pass_no_suggestion(self, tmp_path):
        lines = [
            json.dumps({"type": "hook_check", "hook": "check_cost_tier", "result": "pass"})
            for _ in range(10)
        ]
        path = self._write(tmp_path, lines)
        assert sl.suggest_from_events(path, threshold=5) == []

    def test_malformed_lines_tolerated(self, tmp_path):
        good = [
            json.dumps({"type": "hook_check", "hook": "check_cost_tier", "result": "block"})
            for _ in range(5)
        ]
        lines = ["{not valid json", ""] + good + ["also not json{{", "null", "42"]
        path = self._write(tmp_path, lines)
        result = sl.suggest_from_events(path, threshold=5)
        assert len(result) == 1
        assert result[0].count == 5

    def test_missing_file_returns_empty(self, tmp_path):
        path = tmp_path / "does-not-exist.jsonl"
        assert sl.suggest_from_events(path, threshold=5) == []

    def test_below_threshold_no_suggestion(self, tmp_path):
        lines = [
            json.dumps({"type": "hook_check", "hook": "check_cost_tier", "result": "block"})
            for _ in range(4)
        ]
        path = self._write(tmp_path, lines)
        assert sl.suggest_from_events(path, threshold=5) == []


# ── check_skill_patterns ────────────────────────────────────────────────

class TestCheckSkillPatterns:
    def _paths(self, tmp_path: Path) -> dict:
        return {
            "log_path": tmp_path / "log.md",
            "registry_path": tmp_path / "skills-registry.json",
            "events_path": tmp_path / "live-events.jsonl",
            "cache_path": tmp_path / "skill-learning-cache.json",
            "suggestions_path": tmp_path / "skill-suggestions.json",
        }

    def test_fresh_cache_returns_empty_and_does_not_rewrite_suggestions(self, tmp_path):
        paths = self._paths(tmp_path)
        paths["log_path"].write_text(_repeating_log(["cost-tier"]), encoding="utf-8")
        paths["registry_path"].write_text(json.dumps({"skills": []}), encoding="utf-8")
        now = datetime(2026, 1, 10, tzinfo=timezone.utc)
        fresh = (now - timedelta(days=1)).isoformat()
        paths["cache_path"].write_text(json.dumps({"last_checked": fresh}), encoding="utf-8")
        sentinel = "SENTINEL-UNCHANGED"
        paths["suggestions_path"].write_text(sentinel, encoding="utf-8")

        notices = sl.check_skill_patterns(now=now, env={}, **paths)
        assert notices == []
        assert paths["suggestions_path"].read_text(encoding="utf-8") == sentinel

    def test_stale_cache_runs_and_writes_suggestions_schema(self, tmp_path):
        paths = self._paths(tmp_path)
        paths["log_path"].write_text(_repeating_log(["cost-tier"]), encoding="utf-8")
        paths["registry_path"].write_text(json.dumps({"skills": []}), encoding="utf-8")
        now = datetime(2026, 1, 10, tzinfo=timezone.utc)
        stale = (now - timedelta(days=10)).isoformat()
        paths["cache_path"].write_text(json.dumps({"last_checked": stale}), encoding="utf-8")

        notices = sl.check_skill_patterns(now=now, env={}, **paths)
        assert len(notices) == 1
        data = json.loads(paths["suggestions_path"].read_text(encoding="utf-8"))
        assert "generated_at" in data
        assert "suggestions" in data
        assert data["suggestions"][0]["pattern"] == "cost-tier"
        cache = json.loads(paths["cache_path"].read_text(encoding="utf-8"))
        assert cache["last_checked"] == now.isoformat()

    def test_missing_cache_treated_as_stale_and_runs(self, tmp_path):
        paths = self._paths(tmp_path)
        paths["log_path"].write_text(_repeating_log(["cost-tier"]), encoding="utf-8")
        paths["registry_path"].write_text(json.dumps({"skills": []}), encoding="utf-8")
        now = datetime(2026, 1, 10, tzinfo=timezone.utc)

        notices = sl.check_skill_patterns(now=now, env={}, **paths)
        assert len(notices) == 1
        assert paths["cache_path"].exists()

    def test_notices_capped_at_three(self, tmp_path):
        paths = self._paths(tmp_path)
        terms = ["alpha-term", "bravo-term", "charlie-term", "delta-term"]
        paths["log_path"].write_text(_repeating_log(terms), encoding="utf-8")
        paths["registry_path"].write_text(json.dumps({"skills": []}), encoding="utf-8")
        now = datetime(2026, 1, 10, tzinfo=timezone.utc)

        notices = sl.check_skill_patterns(now=now, env={}, **paths)
        assert len(notices) == 3
        data = json.loads(paths["suggestions_path"].read_text(encoding="utf-8"))
        assert len(data["suggestions"]) == 4

    def test_disabled_via_env(self, tmp_path):
        paths = self._paths(tmp_path)
        paths["log_path"].write_text(_repeating_log(["cost-tier"]), encoding="utf-8")
        now = datetime(2026, 1, 10, tzinfo=timezone.utc)

        notices = sl.check_skill_patterns(now=now, env={"AWIKI_SKILL_LOOP": "0"}, **paths)
        assert notices == []
        assert not paths["cache_path"].exists()

    def test_missing_log_md_no_raise(self, tmp_path):
        paths = self._paths(tmp_path)
        paths["registry_path"].write_text(json.dumps({"skills": []}), encoding="utf-8")
        now = datetime(2026, 1, 10, tzinfo=timezone.utc)

        notices = sl.check_skill_patterns(now=now, env={}, **paths)
        assert notices == []

    def test_corrupt_registry_json_no_raise(self, tmp_path):
        paths = self._paths(tmp_path)
        paths["log_path"].write_text(_repeating_log(["cost-tier"]), encoding="utf-8")
        paths["registry_path"].write_text("{not valid json", encoding="utf-8")
        now = datetime(2026, 1, 10, tzinfo=timezone.utc)

        notices = sl.check_skill_patterns(now=now, env={}, **paths)
        assert len(notices) == 1  # corrupt registry -> treated as empty, nothing covered

    def test_corrupt_cache_json_still_runs(self, tmp_path):
        paths = self._paths(tmp_path)
        paths["log_path"].write_text(_repeating_log(["cost-tier"]), encoding="utf-8")
        paths["registry_path"].write_text(json.dumps({"skills": []}), encoding="utf-8")
        paths["cache_path"].write_text("{not valid json", encoding="utf-8")
        now = datetime(2026, 1, 10, tzinfo=timezone.utc)

        notices = sl.check_skill_patterns(now=now, env={}, **paths)
        assert len(notices) == 1
        cache = json.loads(paths["cache_path"].read_text(encoding="utf-8"))
        assert "last_checked" in cache

    def test_unwritable_suggestions_path_does_not_raise(self, tmp_path):
        paths = self._paths(tmp_path)
        paths["log_path"].write_text(_repeating_log(["cost-tier"]), encoding="utf-8")
        paths["registry_path"].write_text(json.dumps({"skills": []}), encoding="utf-8")
        blocker = tmp_path / "blocker"
        blocker.write_text("x", encoding="utf-8")
        paths["suggestions_path"] = blocker / "skill-suggestions.json"
        now = datetime(2026, 1, 10, tzinfo=timezone.utc)

        # Write target is unwritable (parent is a file, not a dir) -> must not
        # raise, and the in-memory notice list is still returned correctly.
        notices = sl.check_skill_patterns(now=now, env={}, **paths)
        assert len(notices) == 1

    def test_notice_message_format_log_pattern(self, tmp_path):
        paths = self._paths(tmp_path)
        paths["log_path"].write_text(_repeating_log(["cost-tier"]), encoding="utf-8")
        paths["registry_path"].write_text(json.dumps({"skills": []}), encoding="utf-8")
        now = datetime(2026, 1, 10, tzinfo=timezone.utc)

        notices = sl.check_skill_patterns(now=now, env={}, **paths)
        assert notices[0].startswith("\U0001f9e0 Skill loop: 'cost-tier' ซ้ำ 3 sessions")
        assert ".tmp/skill-suggestions.json" in notices[0]

    def test_notice_message_format_hook_friction(self, tmp_path):
        paths = self._paths(tmp_path)
        paths["log_path"].write_text("", encoding="utf-8")
        paths["registry_path"].write_text(json.dumps({"skills": []}), encoding="utf-8")
        block_lines = [
            json.dumps({"type": "hook_check", "hook": "check_cost_tier", "result": "block"})
            for _ in range(5)
        ]
        paths["events_path"].write_text("\n".join(block_lines) + "\n", encoding="utf-8")
        now = datetime(2026, 1, 10, tzinfo=timezone.utc)

        notices = sl.check_skill_patterns(now=now, env={}, **paths)
        assert notices[0].startswith("\U0001f9e0 Skill loop: hook 'check_cost_tier' block 5 ครั้ง")
        assert ".tmp/skill-suggestions.json" in notices[0]

    def test_default_min_sessions_threshold_not_met(self, tmp_path):
        paths = self._paths(tmp_path)
        paths["log_path"].write_text(_repeating_log(["cost-tier"], n_sessions=2), encoding="utf-8")
        paths["registry_path"].write_text(json.dumps({"skills": []}), encoding="utf-8")
        now = datetime(2026, 1, 10, tzinfo=timezone.utc)

        # default MIN_SESSIONS=3 must not trigger with only 2 distinct sessions
        notices_default = sl.check_skill_patterns(now=now, env={}, **paths)
        assert notices_default == []

    def test_explicit_min_sessions_kwarg_overrides_default(self, tmp_path):
        paths = self._paths(tmp_path)
        paths["log_path"].write_text(_repeating_log(["cost-tier"], n_sessions=2), encoding="utf-8")
        paths["registry_path"].write_text(json.dumps({"skills": []}), encoding="utf-8")
        now = datetime(2026, 1, 10, tzinfo=timezone.utc)

        notices = sl.check_skill_patterns(now=now, env={}, min_sessions=2, **paths)
        assert len(notices) == 1

    def test_min_sessions_env_override(self, tmp_path):
        paths = self._paths(tmp_path)
        paths["log_path"].write_text(_repeating_log(["cost-tier"], n_sessions=2), encoding="utf-8")
        paths["registry_path"].write_text(json.dumps({"skills": []}), encoding="utf-8")
        now = datetime(2026, 1, 10, tzinfo=timezone.utc)

        notices = sl.check_skill_patterns(
            now=now, env={"AWIKI_SKILL_LOOP_MIN_SESSIONS": "2"}, **paths
        )
        assert len(notices) == 1


# ── CLI ──────────────────────────────────────────────────────────────────

class TestCLI:
    SCRIPT = str(REPO_ROOT / "scripts" / "lib" / "skill_learning.py")

    def test_report_exits_zero_no_traceback(self):
        result = subprocess.run(
            [sys.executable, self.SCRIPT, "--report"],
            capture_output=True, text=True,
            cwd=str(REPO_ROOT), timeout=30,
        )
        assert result.returncode == 0
        assert "Traceback" not in result.stderr

    def test_report_does_not_touch_cache(self):
        cache_path = REPO_ROOT / ".tmp" / "skill-learning-cache.json"
        before = cache_path.read_text(encoding="utf-8") if cache_path.exists() else None
        subprocess.run(
            [sys.executable, self.SCRIPT, "--report"],
            capture_output=True, text=True,
            cwd=str(REPO_ROOT), timeout=30,
        )
        after = cache_path.read_text(encoding="utf-8") if cache_path.exists() else None
        assert before == after


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
