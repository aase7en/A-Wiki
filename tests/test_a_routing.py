"""Tests for scripts/skills_registry/routing.py — A-Suite intent routing.

The routing table is the one piece of data all three auto-pick substrates share
(the Claude UserPromptSubmit hook, the MCP skill_route tool, and the generated
wiki/A-ROUTER.md that hookless agents read). It therefore has exactly one
implementation and one set of tests.

The central correctness concern is Thai: Python's ``\\b`` is Unicode-aware, but
Thai has no inter-word spaces, so a word-boundary regex silently never matches
a Thai trigger. These tests pin that behaviour down.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from skills_registry import routing  # noqa: E402


# ---------------------------------------------------------------------------
# Phase spine
# ---------------------------------------------------------------------------

class TestPhaseSpine:
    def test_chain_is_the_seven_requested_phases_in_order(self):
        assert routing.A_PHASE_CHAIN == (
            "ask", "design", "plan", "implement", "review", "debug", "test",
        )

    def test_every_phase_maps_to_real_lifecycle_phases(self):
        from skills_registry import VALID_LIFECYCLE_PHASES

        for phase in routing.A_PHASE_CHAIN:
            mapped = routing.A_PHASE_TO_LIFECYCLE[phase]
            assert mapped, f"{phase} maps to nothing"
            unknown = set(mapped) - set(VALID_LIFECYCLE_PHASES)
            assert not unknown, f"{phase} maps to non-existent lifecycle phase(s) {unknown}"

    def test_next_phase_walks_the_chain_and_stops_at_the_end(self):
        assert routing.next_phase("ask") == "design"
        assert routing.next_phase("debug") == "test"
        assert routing.next_phase("test") is None

    def test_next_phase_rejects_unknown_phase(self):
        with pytest.raises(ValueError):
            routing.next_phase("deploy")


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------

class TestThaiMatching:
    """Thai must match as a substring — a word-boundary regex never fires."""

    def test_thai_trigger_matches_inside_an_unspaced_sentence(self):
        # "ช่วยแก้บั๊กหน่อย" — no spaces around the trigger.
        assert routing.match_score(["แก้บั๊ก"], "ช่วยแก้บั๊กหน่อย") > 0

    def test_thai_trigger_matches_at_string_start(self):
        assert routing.match_score(["ออกแบบ"], "ออกแบบ schema ใหม่") > 0

    def test_thai_non_match_scores_zero(self):
        assert routing.match_score(["แก้บั๊ก"], "สวัสดีครับ") == 0


class TestAsciiMatching:
    def test_ascii_trigger_matches_whole_word(self):
        assert routing.match_score(["error"], "there was an error here") > 0

    def test_ascii_trigger_matches_common_suffixes(self):
        # English morphology: plural / -ing / -ed must still hit.
        assert routing.match_score(["error"], "getting errors") > 0
        assert routing.match_score(["crash"], "it crashed again") > 0
        assert routing.match_score(["fail"], "the build is failing") > 0

    def test_ascii_trigger_does_not_match_mid_word(self):
        # The whole point of the prefix boundary: 'error' must not fire on 'terror'.
        assert routing.match_score(["error"], "a terror movie") == 0
        assert routing.match_score(["test"], "the latest build") == 0

    def test_matching_is_case_insensitive(self):
        assert routing.match_score(["error"], "ERROR in prod") > 0

    def test_longer_triggers_score_higher(self):
        long_hit = routing.match_score(["database schema"], "fix the database schema")
        short_hit = routing.match_score(["api"], "fix the api")
        assert long_hit > short_hit


class TestRoute:
    @pytest.fixture
    def reg(self):
        from skills_registry import Registry

        return Registry({
            "schema_version": routing_schema_version(),
            "generated_at": "test",
            "skills": [
                _skill("a-debug", ["แก้บั๊ก", "error", "crash"]),
                _skill("a-plan", ["ออกแบบ", "design", "architecture"]),
                _skill("a-doc", ["เอกสาร", "docx"]),
                _skill("no-triggers", None),
            ],
        })

    def test_routes_thai_prompt_to_the_right_skill(self, reg):
        hits = routing.route(reg, "ช่วยแก้บั๊กหน่อย")
        assert hits, "expected at least one hit"
        assert hits[0][0] == "a-debug"

    def test_routes_english_prompt_to_the_right_skill(self, reg):
        hits = routing.route(reg, "help me design the architecture")
        assert hits[0][0] == "a-plan"

    def test_unrelated_prompt_returns_empty_not_a_false_positive(self, reg):
        assert routing.route(reg, "สวัสดี") == []

    def test_skill_without_triggers_is_never_returned(self, reg):
        for text in ("แก้บั๊ก", "design", "docx", "anything at all"):
            assert all(name != "no-triggers" for name, _ in routing.route(reg, text))

    def test_respects_limit(self, reg):
        hits = routing.route(reg, "error crash design architecture docx", limit=2)
        assert len(hits) <= 2

    def test_results_are_sorted_by_score_descending(self, reg):
        hits = routing.route(reg, "error crash design")
        scores = [s for _, s in hits]
        assert scores == sorted(scores, reverse=True)

    def test_single_distinctive_short_trigger_routes_on_its_own(self, reg):
        """A 4-char domain term like 'docx' is a strong signal by itself.

        Weighting purely by length would leave it below threshold and silently
        fail to route — the exact false negative that makes auto-pick feel broken.
        """
        hits = routing.route(reg, "แปลงไฟล์เป็น docx ให้หน่อย")
        assert hits and hits[0][0] == "a-doc"

    def test_a_three_char_trigger_alone_is_not_enough(self, reg):
        """Symmetric guard: very short triggers need corroboration."""
        from skills_registry import Registry

        tiny = Registry({
            "schema_version": routing_schema_version(),
            "generated_at": "test",
            "skills": [_skill("a-tiny", ["seo"])],
        })
        assert routing.route(tiny, "seo") == []


# ---------------------------------------------------------------------------
# Trigger validation (guards what may enter the registry)
# ---------------------------------------------------------------------------

class TestValidateTriggers:
    def test_accepts_a_normal_mixed_list(self):
        assert routing.validate_triggers(["แก้บั๊ก", "error", "crash"], "ctx") == []

    def test_rejects_more_than_max(self):
        errs = routing.validate_triggers([f"trigger{i}" for i in range(routing.MAX_TRIGGERS + 1)], "ctx")
        assert errs and "at most" in errs[0]

    def test_accepts_exactly_max(self):
        assert routing.validate_triggers([f"trig{i}" for i in range(routing.MAX_TRIGGERS)], "ctx") == []

    def test_rejects_short_ascii_trigger(self):
        # 2-char ASCII would fire on almost anything.
        errs = routing.validate_triggers(["ab"], "ctx")
        assert errs and "too short" in errs[0].lower()

    def test_accepts_two_char_thai_trigger(self):
        # Thai is information-dense; 2 chars is a real word.
        assert routing.validate_triggers(["ยา"], "ctx") == []

    def test_rejects_stop_list_words(self):
        for word in ("fix", "make", "ทำ"):
            errs = routing.validate_triggers([word], "ctx")
            assert errs, f"{word!r} should be rejected as too generic"

    def test_rejects_non_list(self):
        assert routing.validate_triggers("error", "ctx")

    def test_rejects_non_string_member(self):
        assert routing.validate_triggers(["error", 42], "ctx")

    def test_rejects_uppercase_so_storage_stays_normalised(self):
        errs = routing.validate_triggers(["ERROR"], "ctx")
        assert errs and "lowercase" in errs[0].lower()

    def test_rejects_duplicates(self):
        errs = routing.validate_triggers(["error", "error"], "ctx")
        assert errs and "duplicate" in errs[0].lower()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def routing_schema_version() -> int:
    from skills_registry import SCHEMA_VERSION

    return SCHEMA_VERSION


def _skill(name: str, triggers: list[str] | None) -> dict:
    entry = {
        "name": name,
        "aliases": [],
        "domain": ["engineering"],
        "lifecycle_phase": "meta",
        "category": "pipeline",
        "source": "repo",
        "path": f"skills/awiki/{name}/SKILL.md",
        "agents": ["all"],
        "status": "canonical",
        "description": name,
    }
    if triggers is not None:
        entry["triggers"] = triggers
    return entry
