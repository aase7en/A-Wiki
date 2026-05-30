from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "skillopt" / "awiki_eval.py"


def test_awiki_eval_scores_required_and_forbidden_terms(tmp_path):
    skill = tmp_path / "skill.md"
    skill.write_text(
        "# Test Skill\n\nUse local search first. Never edit raw/ files.\n",
        encoding="utf-8",
    )
    suite = tmp_path / "suite.json"
    suite.write_text(
        json.dumps(
            {
                "suite": "unit",
                "cases": [
                    {
                        "id": "local-first",
                        "skill": str(skill),
                        "required": ["local search"],
                        "forbidden": ["git reset --hard"],
                    },
                    {
                        "id": "raw-immutable",
                        "skill": str(skill),
                        "required": ["Never edit raw/"],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--suite", str(suite), "--json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["passed"] is True
    assert payload["score"] == 1.0
    assert payload["passed_cases"] == 2


def test_awiki_eval_fails_when_required_guidance_missing(tmp_path):
    skill = tmp_path / "skill.md"
    skill.write_text("# Test Skill\n\nNo relevant guidance.\n", encoding="utf-8")
    suite = tmp_path / "suite.json"
    suite.write_text(
        json.dumps(
            {
                "suite": "unit",
                "cases": [
                    {
                        "id": "missing",
                        "skill": str(skill),
                        "required": ["local search first"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--suite", str(suite), "--json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["passed"] is False
    assert payload["failed_cases"] == 1


def test_codex_hook_setup_script_uses_relative_commands():
    script = REPO_ROOT / "scripts" / "setup-codex-hooks.sh"
    text = script.read_text(encoding="utf-8")

    assert ".codex/hooks.json" in text
    assert "scripts/hooks_runner.py" in text
    assert "/Users/" not in text
    assert "A:\\\\" not in text


def test_awiki_skillopt_adapter_accepts_non_regressing_candidate(tmp_path):
    current = tmp_path / "current.md"
    current.write_text("# Current\n\nUse local search first.\n", encoding="utf-8")
    candidate = tmp_path / "candidate.md"
    candidate.write_text("# Candidate\n\nUse local search first. Never edit raw/.\n", encoding="utf-8")
    suite = tmp_path / "suite.json"
    suite.write_text(
        json.dumps(
            {
                "suite": "gate",
                "cases": [
                    {"id": "local", "required": ["local search"]},
                    {"id": "raw", "required": ["Never edit raw/"]},
                ],
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "skillopt" / "awiki_skillopt_adapter.py"),
            "--suite",
            str(suite),
            "--current-skill",
            str(current),
            "--candidate-skill",
            str(candidate),
            "--json",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["action"] == "accept"
    assert payload["candidate_score"] > payload["current_score"]


def test_awiki_skillopt_adapter_rejects_regression(tmp_path):
    current = tmp_path / "current.md"
    current.write_text("# Current\n\nUse local search first. Never edit raw/.\n", encoding="utf-8")
    candidate = tmp_path / "candidate.md"
    candidate.write_text("# Candidate\n\nUse local search first.\n", encoding="utf-8")
    suite = tmp_path / "suite.json"
    suite.write_text(
        json.dumps(
            {
                "suite": "gate",
                "cases": [
                    {"id": "local", "required": ["local search"]},
                    {"id": "raw", "required": ["Never edit raw/"]},
                ],
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "skillopt" / "awiki_skillopt_adapter.py"),
            "--suite",
            str(suite),
            "--current-skill",
            str(current),
            "--candidate-skill",
            str(candidate),
            "--json",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["action"] == "reject"
    assert payload["candidate_score"] < payload["current_score"]
