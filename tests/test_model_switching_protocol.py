from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read_doc(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_model_switching_protocol_has_required_structure_and_links():
    text = read_doc("docs/protocols/model-switching.md")

    required_phrases = [
        "id=\"tier-4a\"",
        "id=\"tier-4b\"",
        "id=\"tier-4c\"",
        "low",
        "medium",
        "high",
        "xhigh",
        "max",
        "Phase A",
        "Phase B",
        "Phase C",
        "Phase D",
        "delegation.md",
        "context-compaction.md",
        "bot-trading-iron-law.md",
        "claude-model-cost-switching-strategy-2026-06.md",
        "wiki/context/wiki-overview.md",
        "2048 tokens",
        "1.25x",
        "2x",
    ]

    for phrase in required_phrases:
        assert phrase in text

    assert "/Users/" not in text


def test_quick_commands_points_to_model_switching_protocol():
    text = read_doc("docs/protocols/quick-commands.md")

    assert "/model-tier" in text
    assert "docs/protocols/model-switching.md" in text


def test_platform_instruction_files_have_behavioral_model_switching_pointer():
    required = [
        "docs/protocols/model-switching.md",
        "model-cost-switching",
        "classify task",
        "tier 4a/4b/4c",
        "effort",
        "ไม่ต้องรอ user สั่ง",
    ]

    for path in ("AGENTS.md", "CLAUDE.md"):
        text = read_doc(path)
        for phrase in required:
            assert phrase in text, f"{path} missing {phrase!r}"
