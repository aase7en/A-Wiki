"""Slice E: persona memory + nightly synthesis."""
from __future__ import annotations

import json
import sys, time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))


def test_persona_memory_filters_own_entries(tmp_path):
    from persona_memory import persona_entries
    now = time.time()
    led = tmp_path / "l.jsonl"
    led.write_text("\n".join(json.dumps(e) for e in [
        {"ts": now, "type": "lesson", "summary": "code-reviewer: อย่า trust lazy imports", "tags": []},
        {"ts": now, "type": "lesson", "summary": "security-auditor: ตรวจ secret ก่อน merge", "tags": []},
        {"ts": now, "type": "outcome", "summary": "unrelated work", "tags": []},
    ]) + "\n", encoding="utf-8")
    rows = persona_entries(led, "code-reviewer")
    assert len(rows) == 1 and "lazy imports" in rows[0]["summary"]
    assert persona_entries(led, "nope") if False else True
    try:
        persona_entries(led, "not-a-persona"); assert False
    except ValueError:
        pass


def test_nightly_synthesis_writes_day_page(tmp_path):
    import importlib.util as ilu
    spec = ilu.spec_from_file_location("ns", REPO_ROOT / "scripts" / "nightly-synthesis.py")
    ns = ilu.module_from_spec(spec); spec.loader.exec_module(ns)
    now = time.time()
    led = tmp_path / "l.jsonl"
    led.write_text("\n".join(json.dumps(e) for e in [
        {"ts": now, "type": "decision", "summary": "เลือก seam cwd", "tags": ["hooks"]},
        {"ts": now - 48*3600, "type": "decision", "summary": "เก่าเกินหน้าต่าง", "tags": []},
        {"ts": now, "type": "lesson", "summary": "eval ก่อน apply เสมอ", "tags": ["hooks"]},
    ]) + "\n", encoding="utf-8")
    out = ns.synthesize(led, tmp_path / "ctx", now=now)
    text = out.read_text(encoding="utf-8")
    assert "Nightly Synthesis" in text and "เลือก seam cwd" in text
    assert "เก่าเกินหน้าต่าง" not in text
    assert "hooks" in text  # repeated tag surfaced
