from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "verify-model-routing.sh"


def test_verify_model_routing_mock_mode_writes_report(tmp_path):
    report = tmp_path / "model-routing-report.md"

    result = subprocess.run(
        ["bash", str(SCRIPT), "--mock", "--out", str(report)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    text = report.read_text(encoding="utf-8")
    assert "Model Routing Verification" in text
    assert "claude" in text
    assert "codex" in text
    assert "gemini" in text
    assert "PASS count: 2/3" in text
    assert "threshold: PASS" in text


def test_model_switching_protocol_has_manual_verification_matrix():
    text = (REPO_ROOT / "docs" / "protocols" / "model-switching.md").read_text(encoding="utf-8")

    required = [
        "Verification Matrix",
        "Claude Desktop",
        "Cursor",
        "Windsurf",
        "scripts/verify-model-routing.sh",
        "PASS/FAIL",
    ]
    for phrase in required:
        assert phrase in text
