from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
EXTRACTOR = REPO_ROOT / "scripts" / "_extract_response.py"
DELEGATE_SH = REPO_ROOT / "scripts" / "swarm" / "delegate.sh"


def test_extract_response_supports_system_python3_for_gemini():
    system_python = Path("/usr/bin/python3")
    if not system_python.exists():
        pytest.skip("/usr/bin/python3 not available on this machine")

    payload = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "GEMINI_LANE_OK"}],
                    "role": "model",
                },
                "finishReason": "STOP",
                "index": 0,
            }
        ]
    }

    proc = subprocess.run(
        [str(system_python), str(EXTRACTOR), "gemini"],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "GEMINI_LANE_OK"


def test_delegate_failure_log_guards_zero_attempts():
    text = DELEGATE_SH.read_text(encoding="utf-8")
    assert 'if [ "$count" -gt 0 ]; then' in text
    assert 'for reason in "${FAIL_REASONS[@]}"' in text
