from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / "agent-skills" / "swarm-intelligence" / "model-cost-switching"
SKILL_FILE = SKILL_DIR / "SKILL.md"


def test_model_cost_switching_skill_is_depth_two_and_named_consistently():
    assert SKILL_FILE.exists()
    assert SKILL_DIR.parent.name == "swarm-intelligence"
    assert SKILL_DIR.parent.parent.name == "agent-skills"

    text = SKILL_FILE.read_text(encoding="utf-8")

    assert "name: model-cost-switching" in text
    assert "description:" in text
    assert "docs/protocols/model-switching.md" in text
    assert "claude-model-cost-switching-strategy-2026-06.md" in text
    assert "/Users/" not in text


def test_model_cost_switching_skill_has_operational_decision_rules():
    text = SKILL_FILE.read_text(encoding="utf-8")

    required_phrases = [
        "Triggers",
        "Non-Triggers",
        "Decision Algorithm",
        "Escalate",
        "De-escalate",
        "4a",
        "4b",
        "4c",
        "low",
        "medium",
        "high",
        "xhigh",
        "max",
        "สถาปนิก",
        "ทีมช่าง",
        "ผู้ช่วย",
        "Level -1",
        "Level 3",
    ]

    for phrase in required_phrases:
        assert phrase in text

    assert "Claude Code only" not in text
