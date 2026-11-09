"""WO-AWIKI-76-01: compact, canonical, read-only skill discovery."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from skills_registry import Registry  # noqa: E402
from skills_registry.skill_cards import build_cards  # noqa: E402


@pytest.fixture
def registry():
    return Registry({
        "skills": [
            {"name": "debugger", "status": "canonical", "description": "Investigate failures from evidence",
             "path": "skills/debugger/SKILL.md", "invocation": "auto", "triggers": ["crash", "error"]},
            {"name": "interview", "status": "canonical", "description": "Interview users about decisions",
             "path": "skills/interview/SKILL.md", "invocation": "manual", "triggers": []},
            {"name": "legacy", "status": "deprecated", "description": "Old crash routine",
             "path": "skills/legacy/SKILL.md", "triggers": ["crash"]},
        ]})
def test_query_uses_existing_router_and_excludes_deprecated(registry):
    out = build_cards(registry, query="fix crash immediately", limit=3)
    assert [x["name"] for x in out["cards"]] == ["debugger"]
    assert out["cards"][0]["match"] == "EXPLICIT_TRIGGER"
    assert out["cards"][0]["auto_load_candidate"] is True
    assert out["full_skill_bodies_loaded"] == 0
    assert "crash" in out["cards"][0]["use_when"]


def test_missed_query_is_not_auto_execute(registry):
    out = build_cards(registry, query="hello")
    assert out["cards"] == []
    assert out["decision"] == "NO_AUTO_SELECT"


def test_core_cards_capped_and_not_auto_selected(registry):
    out = build_cards(registry, query=None, core_names=("debugger", "legacy", "interview"), limit=2)
    assert [x["name"] for x in out["cards"]] == ["debugger", "interview"]
    assert out["decision"] == "DISCOVER_ONLY"
    assert all(x["auto_load_candidate"] is False for x in out["cards"])


def test_long_description_is_bounded():
    reg = Registry({"skills": [{"name": "big", "status": "canonical", "description": "word " * 300,
       "path": "skills/big/SKILL.md", "triggers": ["overflow"]}]})
    out = build_cards(reg, query="overflow", limit=1)
    assert len(out["cards"][0]["purpose"]) <= 220
    assert out["cards"][0]["purpose"].endswith("…")
def test_no_invented_negative_policy(registry):
    out = build_cards(registry, query="crash")
    card = out["cards"][0]
    assert card["do_not_use_when"] == "NOT_SPECIFIED_IN_REGISTRY"
    assert card["risk_policy"] == "NOT_VERIFIED"
    assert card["body_pointer"] == "skills/debugger/SKILL.md"


def test_description_fallback_is_suggestion_only(registry):
    out = build_cards(registry, query="interview users about decisions", limit=3)
    if out["cards"]:
        assert all(not card["auto_load_candidate"] for card in out["cards"])


@pytest.mark.parametrize("prompt", [
    "crash", "fix error", "Error in build", "crashes on launch",
    "hello", "thanks", "good morning", "how are you",
    "debug crash on Windows", "investigate runtime error",
    "restart server", "error regression", "write proposal",
    "create UI design", "plan dashboard", "research market",
    "verify build", "test deployment", "make architecture",
    "compare two systems"
])
def test_20_english_prompts_are_bounded_and_nonexecuting(registry, prompt):
    out = build_cards(registry, query=prompt, limit=3)
    assert len(out["cards"]) <= 3
    assert all(c["status"] == "canonical" and "body" not in c for c in out["cards"])
    assert out["full_skill_bodies_loaded"] == 0
def test_real_registry_and_cli_json_without_full_skill_reads():
    registry = Registry.load(ROOT / "skills-registry.json")
    out = build_cards(registry, query="fix error", limit=3)
    assert out["cards"]
    assert len(out["cards"]) <= 3
    assert all(c["status"] == "canonical" for c in out["cards"])
    cmd = [sys.executable, str(ROOT / "scripts" / "skill-cards.py"), "--query",
           "fix error", "--json"]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    assert p.returncode == 0, p.stderr
    data = json.loads(p.stdout)
    assert len(data["cards"]) <= 3
    assert data["full_skill_bodies_loaded"] == 0


@pytest.mark.parametrize("prompt", [
    "ช่วยแก้บั๊กหน้าเว็บ", "หาสาเหตุระบบไม่ทำงาน", "ทดสอบระบบ",
    "สรุปรายงานสั้นๆ", "ออกแบบระบบใหม่", "วางแผนงาน",
])
def test_thai_queries_fail_closed_without_body_reads(prompt):
    registry = Registry.load(ROOT / "skills-registry.json")
    out = build_cards(registry, query=prompt)
    assert len(out["cards"]) <= 3
    assert out["full_skill_bodies_loaded"] == 0
    assert all(c["status"] == "canonical" for c in out["cards"])


def test_default_catalog_is_small_and_read_only():
    cmd = [sys.executable, str(ROOT / "scripts" / "skill-cards.py"), "--json"]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    assert p.returncode == 0, p.stderr
    out = json.loads(p.stdout)
    assert out["decision"] == "DISCOVER_ONLY"
    assert len(out["cards"]) <= 8
    assert all(not c["auto_load_candidate"] for c in out["cards"])
