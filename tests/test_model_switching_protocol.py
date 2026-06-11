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


def test_platform_instruction_files_require_dynamic_cost_scouting():
    required = [
        "scout current model/pricing",
        "free-current",
        "cheap-capable",
        "platform-low-scout",
        "platform-primary",
        "scripts/model-scout-current.py",
        "dated examples only",
    ]

    for path in ("AGENTS.md", "CLAUDE.md"):
        text = read_doc(path)
        for phrase in required:
            assert phrase in text, f"{path} missing {phrase!r}"


def test_cost_first_tables_do_not_bind_vendor_models_as_routes():
    forbidden_bindings = [
        "Cheap paid (DeepSeek, Qwen)",
        "Free API (OpenRouter free / Gemini Flash)",
        "Subagent (Claude Haiku / Explore)",
        "Subagent (Haiku-class / Explore)",
        "Claude Sonnet (current)",
        "Sonnet-class default",
    ]

    for path in ("AGENTS.md", "CLAUDE.md", "docs/protocols/model-switching.md"):
        text = read_doc(path)
        for phrase in forbidden_bindings:
            assert phrase not in text, f"{path} still binds route to {phrase!r}"


def test_model_switching_protocol_documents_dynamic_scout_gate():
    text = read_doc("docs/protocols/model-switching.md")
    required = [
        "Dynamic Scout Gate",
        "scout current model/pricing",
        "free-current",
        "cheap-capable",
        "platform-low-scout",
        "platform-primary",
        "DeepSeek pricing",
        "OpenRouter Models API",
        "model examples are dated examples only",
    ]
    for phrase in required:
        assert phrase in text
