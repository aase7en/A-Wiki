from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SETTINGS = REPO_ROOT / ".gemini" / "settings.json"


def test_gemini_settings_use_current_hook_schema_and_no_stale_model():
    data = json.loads(SETTINGS.read_text(encoding="utf-8"))

    assert "gemini-2.5-pro-exp-03-25" not in SETTINGS.read_text(encoding="utf-8")
    assert isinstance(data.get("hooks"), dict)
    assert "enabled" not in data["hooks"]
    assert "runner" not in data["hooks"]

    session_start = data["hooks"]["SessionStart"][0]["hooks"][0]
    before_tool = data["hooks"]["BeforeTool"][0]["hooks"][0]

    assert session_start["type"] == "command"
    assert "scripts/hooks/session_start.py" in session_start["command"]
    assert before_tool["type"] == "command"
    assert "scripts/hooks_runner.py" in before_tool["command"]
