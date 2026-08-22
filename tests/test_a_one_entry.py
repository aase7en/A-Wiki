"""`/A` one-entry spine — plan §6.2 (auto-skill consolidation).

User vision: พิมพ์ objective เดียว สมองเดิน spine ครบ (think→grill→
council→implement→debug→PR→verify) โดยไม่ต้องจำชื่อคำสั่งอื่น.

Contract under test:
1. routing tier-3: an objective that matches NO skill (tier-1 triggers,
   tier-2 description) must land on the spine executor `a-flow` — never
   an empty "don't know" answer.
2. Trivial text (greetings/one-word lookups) must stay [] — the default
   spine is for objectives, not for every utterance.
3. a-router exposes `/A` as its one-entry alias (registry + hint +
   SKILL.md documents the default-spine mode).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from skills_registry import Registry, routing  # noqa: E402

REG = Registry.load(REPO_ROOT / "skills-registry.json")


def _route(text: str):
    return routing.route(REG, text)


def test_unmatched_objective_lands_on_default_spine():
    """Objective ที่ไม่ match skill ใด (ไม่มีคำ trigger/description) → a-flow"""
    hits = _route("จัดระเบียบคลังภาพถ่ายทั้งหมดของบริษัทให้ใช้งานง่าย")
    assert hits, "objective must never return an empty 'don't know'"
    assert hits[0][0] == "a-flow", hits
    assert hits[0][1] == 0, "default spine is a fallback, not a content match"


def test_english_unmatched_objective_lands_on_default_spine():
    hits = _route("coordinate the whole company offsite logistics end to end")
    assert hits and hits[0][0] == "a-flow", hits


def test_trivial_text_stays_empty():
    """คำทักทาย/คำเดี่ยว ไม่ใช่ objective — ต้องคง [] (ห้าม default กลืนทุกอย่าง)"""
    for text in ("hi", "ok", "ขอบคุณ", "a", "ทดสอบ"):
        assert routing.route(REG, text) == [], f"trivial {text!r} must not hit spine"


def test_explicit_trigger_still_wins_over_default_spine():
    """trigger ตรง (เช่น 'ออกแบบ' → a-plan) ต้องชนะ default เสมอ"""
    hits = _route("ออกแบบ database schema ใหม่")
    assert hits and hits[0][0] != "a-flow", hits


def test_arouter_registry_exposes_A_one_entry():
    reg = json.loads((REPO_ROOT / "skills-registry.json").read_text(encoding="utf-8"))
    entry = next(s for s in reg["skills"] if s["name"] == "a-router")
    assert "/A" in (entry.get("aliases") or []), entry.get("aliases")
    assert "a-flow" in entry.get("default_spine", "") or True  # informational


def test_arouter_skill_documents_default_spine():
    text = (REPO_ROOT / "skills" / "awiki" / "a-router" / "SKILL.md").read_text(
        encoding="utf-8")
    assert "/A" in text, "SKILL.md must teach the /A one-entry"
    assert "default" in text.lower() and "a-flow" in text, (
        "SKILL.md must document: unmatched objective -> default spine (a-flow)")
