"""Tests for scripts/skills_registry/quality_gate_thai.py.

Covers: valid input, missing keys, length bounds, Thai-ratio thresholds,
examples structure, process_steps bounds, invocation enum, secret/path leak,
and tolerance to markdown fences.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import pytest  # noqa: E402

from skills_registry.quality_gate_thai import validate  # noqa: E402


# ---------- fixtures ----------

VALID = """{
  "th_description": "สกิลนี้ช่วย debug อย่างเป็นระบบ โดยใช้แมนตรา 4 ขั้นเพื่อหา root cause ก่อนแก้ กันซ้ำซ้อนของการแก้ที่อาการไม่ใช่ที่สาเหตุ",
  "when_to_use": "เมื่อเจอ bug ที่ซับซ้อน หรือแก้แล้วเกิดใหม่",
  "examples": [
    {"scenario": "แอป crash บางครั้ง", "how": "ใช้ /debug-mantra ทำ 4 ขั้น"}
  ],
  "process_steps": ["reproduce", "trace fail path", "falsify hypothesis", "cross-reference"],
  "invocation": "manual"
}"""


# ---------- happy paths ----------

def test_valid_full_input():
    ok, reason, data = validate(VALID, "debug-mantra")
    assert ok, f"expected ok, got reason={reason}"
    assert data["invocation"] == "manual"
    assert len(data["process_steps"]) == 4
    assert len(data["examples"]) == 1


def test_valid_minimal_no_process_steps():
    body = """{
      "th_description": "สกิลนี้ช่วยค้นหาใน wiki ด้วย FTS5 แบบ local ไม่ต้องเชื่อมเน็ต เร็วและฟรี เหมาะกับการดูข้อมูลในเครื่อง",
      "when_to_use": "เมื่อต้องการค้นหาใน wiki",
      "examples": [{"scenario": "ค้น MQTT", "how": "/wiki-search-local MQTT"}]
    }"""
    ok, reason, data = validate(body)
    assert ok, reason
    assert "process_steps" not in data
    assert data["invocation"] == "manual"  # defaulted


def test_valid_with_fences():
    body = """Here you go:
    ```json
    {
      "th_description": "สกิลนี้ช่วยค้นหาใน wiki ด้วย FTS5 แบบ local ไม่ต้องเชื่อมเน็ต เร็วและฟรี เหมาะกับการดูข้อมูลในเครื่อง",
      "when_to_use": "เมื่อต้องการค้นหาใน wiki",
      "examples": [{"scenario": "ค้น MQTT", "how": "/wiki-search-local MQTT"}]
    }
    ```
    """
    ok, reason, _ = validate(body)
    assert ok, reason


def test_valid_with_preamble():
    body = """Sure, here's the JSON:
    {"th_description": "สกิลนี้ช่วยค้นหาใน wiki ด้วย FTS5 แบบ local ไม่ต้องเชื่อมเน็ต เร็วและฟรี เหมาะกับการดูข้อมูลในเครื่อง", "when_to_use": "เมื่อต้องการค้นหาใน wiki", "examples": [{"scenario": "ค้น MQTT", "how": "/wiki-search-local MQTT"}]}"""
    ok, reason, _ = validate(body)
    assert ok, reason


# ---------- structural failures ----------

def test_empty_output():
    ok, reason, _ = validate("")
    assert not ok
    assert "empty" in reason


def test_invalid_json():
    ok, reason, _ = validate("{not json")
    assert not ok
    assert "JSON parse" in reason


def test_missing_required_key():
    body = """{
      "th_description": "สกิลนี้ช่วยค้นหาใน wiki ด้วย FTS5 แบบ local ไม่ต้องเชื่อมเน็ต เร็วและฟรี เหมาะกับการดูข้อมูลในเครื่อง",
      "when_to_use": "เมื่อต้องการค้นหาใน wiki"
    }"""
    ok, reason, _ = validate(body)
    assert not ok
    assert "examples" in reason


def test_unknown_key():
    body = """{
      "th_description": "สกิลนี้ช่วยค้นหาใน wiki ด้วย FTS5 แบบ local ไม่ต้องเชื่อมเน็ต เร็วและฟรี เหมาะกับการดูข้อมูลในเครื่อง",
      "when_to_use": "เมื่อต้องการค้นหาใน wiki",
      "examples": [{"scenario": "ค้น MQTT", "how": "/wiki-search-local MQTT"}],
      "bogus_field": "no"
    }"""
    ok, reason, _ = validate(body)
    assert not ok
    assert "bogus_field" in reason


# ---------- length failures ----------

def test_th_description_too_short():
    body = """{
      "th_description": "สั้นเกินไป",
      "when_to_use": "เมื่อต้องการค้นหาใน wiki",
      "examples": [{"scenario": "ค้น MQTT", "how": "/wiki-search-local MQTT"}]
    }"""
    ok, reason, _ = validate(body)
    assert not ok
    assert "th_description length" in reason


def test_when_to_use_too_short():
    body = """{
      "th_description": "สกิลนี้ช่วยค้นหาใน wiki ด้วย FTS5 แบบ local ไม่ต้องเชื่อมเน็ต เร็วและฟรี เหมาะกับการดูข้อมูลในเครื่อง",
      "when_to_use": "สั้น",
      "examples": [{"scenario": "ค้น MQTT", "how": "/wiki-search-local MQTT"}]
    }"""
    ok, reason, _ = validate(body)
    assert not ok
    assert "when_to_use length" in reason


# ---------- Thai-ratio failures ----------

def test_th_description_too_english():
    body = """{
      "th_description": "This skill helps you debug systematically using four mantras to find root cause before fixing and avoid repeatedly fixing symptoms instead of causes.",
      "when_to_use": "เมื่อเจอ bug ที่ซับซ้อน",
      "examples": [{"scenario": "แอป crash", "how": "/debug-mantra"}]
    }"""
    ok, reason, _ = validate(body)
    assert not ok
    assert "Thai ratio" in reason


# ---------- examples structure ----------

def test_examples_not_list():
    body = """{
      "th_description": "สกิลนี้ช่วยค้นหาใน wiki ด้วย FTS5 แบบ local ไม่ต้องเชื่อมเน็ต เร็วและฟรี เหมาะกับการดูข้อมูลในเครื่อง",
      "when_to_use": "เมื่อต้องการค้นหาใน wiki",
      "examples": {"scenario": "x", "how": "y"}
    }"""
    ok, reason, _ = validate(body)
    assert not ok
    assert "examples" in reason


def test_examples_entry_missing_how():
    body = """{
      "th_description": "สกิลนี้ช่วยค้นหาใน wiki ด้วย FTS5 แบบ local ไม่ต้องเชื่อมเน็ต เร็วและฟรี เหมาะกับการดูข้อมูลในเครื่อง",
      "when_to_use": "เมื่อต้องการค้นหาใน wiki",
      "examples": [{"scenario": "x"}]
    }"""
    ok, reason, _ = validate(body)
    assert not ok
    assert "scenario+how" in reason


def test_examples_too_many():
    body = """{
      "th_description": "สกิลนี้ช่วยค้นหาใน wiki ด้วย FTS5 แบบ local ไม่ต้องเชื่อมเน็ต เร็วและฟรี เหมาะกับการดูข้อมูลในเครื่อง",
      "when_to_use": "เมื่อต้องการค้นหาใน wiki",
      "examples": [{"scenario":"a","how":"b"},{"scenario":"c","how":"d"},{"scenario":"e","how":"f"}]
    }"""
    ok, reason, _ = validate(body)
    assert not ok
    assert "1-2" in reason


# ---------- process_steps ----------

def test_process_steps_too_short():
    body = """{
      "th_description": "สกิลนี้ช่วยค้นหาใน wiki ด้วย FTS5 แบบ local ไม่ต้องเชื่อมเน็ต เร็วและฟรี เหมาะกับการดูข้อมูลในเครื่อง",
      "when_to_use": "เมื่อต้องการค้นหาใน wiki",
      "examples": [{"scenario":"a","how":"b"}],
      "process_steps": ["one", "two"]
    }"""
    ok, reason, _ = validate(body)
    assert not ok
    assert "process_steps length" in reason


def test_process_steps_too_long():
    # 60 chars is the cap (relaxed from 40 for Thai compound words).
    long_step = "x" * 61
    body = json.dumps({
        "th_description": "สกิลนี้ช่วยค้นหาใน wiki ด้วย FTS5 แบบ local ไม่ต้องเชื่อมเน็ต เร็วและฟรี เหมาะกับการดูข้อมูลในเครื่อง",
        "when_to_use": "เมื่อต้องการค้นหาใน wiki",
        "examples": [{"scenario": "a", "how": "b"}],
        "process_steps": [long_step, "y", "z"],
    })
    ok, reason, _ = validate(body)
    assert not ok
    assert "process_steps[0] length 61 > 60" in reason


def test_process_steps_at_cap_60_passes():
    at_cap = "x" * 60  # exactly the cap — should pass
    body = json.dumps({
        "th_description": "สกิลนี้ช่วยค้นหาใน wiki ด้วย FTS5 แบบ local ไม่ต้องเชื่อมเน็ต เร็วและฟรี เหมาะกับการดูข้อมูลในเครื่อง",
        "when_to_use": "เมื่อต้องการค้นหาใน wiki",
        "examples": [{"scenario": "a", "how": "b"}],
        "process_steps": [at_cap, "y", "z"],
    })
    ok, reason, data = validate(body)
    assert ok, reason
    assert len(data["process_steps"]) == 3


def test_process_steps_null_is_tolerated():
    body = """{
      "th_description": "สกิลนี้ช่วยค้นหาใน wiki ด้วย FTS5 แบบ local ไม่ต้องเชื่อมเน็ต เร็วและฟรี เหมาะกับการดูข้อมูลในเครื่อง",
      "when_to_use": "เมื่อต้องการค้นหาใน wiki",
      "examples": [{"scenario":"a","how":"b"}],
      "process_steps": null
    }"""
    ok, reason, data = validate(body)
    assert ok, reason
    assert "process_steps" not in data  # null stripped


# ---------- invocation ----------

def test_invalid_invocation():
    body = """{
      "th_description": "สกิลนี้ช่วยค้นหาใน wiki ด้วย FTS5 แบบ local ไม่ต้องเชื่อมเน็ต เร็วและฟรี เหมาะกับการดูข้อมูลในเครื่อง",
      "when_to_use": "เมื่อต้องการค้นหาใน wiki",
      "examples": [{"scenario":"a","how":"b"}],
      "invocation": "magic"
    }"""
    ok, reason, _ = validate(body)
    assert not ok
    assert "invocation" in reason


# ---------- secret/path leak ----------

def test_secret_leak_user_path():
    body = """{
      "th_description": "สกิลนี้ช่วยค้นหาไฟล์ใน /Users/john/projects แบบ local ไม่ต้องเชื่อมเน็ต เร็วและฟรี เหมาะกับการดูข้อมูลในเครื่อง",
      "when_to_use": "เมื่อต้องการค้นหาใน wiki",
      "examples": [{"scenario":"a","how":"b"}]
    }"""
    ok, reason, _ = validate(body)
    assert not ok
    assert "leaked" in reason.lower() or "Users" in reason


def test_secret_leak_api_key():
    body = """{
      "th_description": "สกิลนี้ใช้คีย์ sk-abc123def456ghi789jkl012mno345pqr ในการเรียก API แบบ local ไม่ต้องเชื่อมเน็ต เร็วและฟรี",
      "when_to_use": "เมื่อต้องการค้นหาใน wiki",
      "examples": [{"scenario":"a","how":"b"}]
    }"""
    ok, reason, _ = validate(body)
    assert not ok


def test_secret_leak_drive_path():
    body = """{
      "th_description": "สกิลนี้ช่วย sync ข้อมูลไปยัง A-Wiki-Data/Drive อย่างปลอดภัย แบบ local ไม่ต้องเชื่อมเน็ต เร็วและฟรี",
      "when_to_use": "เมื่อต้องการ sync",
      "examples": [{"scenario":"a","how":"b"}]
    }"""
    ok, reason, _ = validate(body)
    assert not ok
