from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify-awiki-ready.py"
spec = importlib.util.spec_from_file_location("verify_awiki_ready", SCRIPT)
assert spec and spec.loader
verify_awiki_ready = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = verify_awiki_ready
spec.loader.exec_module(verify_awiki_ready)


def test_exit_code_fails_only_on_fail():
    results = [
        verify_awiki_ready.ReadyCheck("OK", "one", "ok"),
        verify_awiki_ready.ReadyCheck("WARN", "two", "warn"),
    ]
    assert verify_awiki_ready.exit_code(results) == 0

    results.append(verify_awiki_ready.ReadyCheck("FAIL", "three", "fail"))
    assert verify_awiki_ready.exit_code(results) == 1


def test_heavy_path_ignore_check_requires_gitignore(monkeypatch, tmp_path):
    monkeypatch.setattr(verify_awiki_ready, "REPO_ROOT", tmp_path)
    (tmp_path / ".gitignore").write_text("raw\nraw/\ndrive\n.tmp/\n.venv-*\n", encoding="utf-8")

    result = verify_awiki_ready.check_heavy_paths_ignored()

    assert result.level == "OK"


def test_heavy_path_ignore_check_fails_when_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(verify_awiki_ready, "REPO_ROOT", tmp_path)
    (tmp_path / ".gitignore").write_text("raw\n", encoding="utf-8")

    result = verify_awiki_ready.check_heavy_paths_ignored()

    assert result.level == "FAIL"
    assert ".tmp/" in result.detail


def test_codex_hooks_relative_check_blocks_absolute_paths(monkeypatch, tmp_path):
    config = tmp_path / ".codex" / "hooks.json"
    config.parent.mkdir()
    config.write_text(
        '{"hooks":{"Stop":[{"hooks":[{"command":"bash /Users/me/A-Wiki/.codex/hooks/stop.sh"}]}]}}',
        encoding="utf-8",
    )
    monkeypatch.setattr(verify_awiki_ready, "REPO_ROOT", tmp_path)

    result = verify_awiki_ready.check_codex_hooks_relative()

    assert result.level == "FAIL"
    assert "absolute" in result.detail


def test_script_mentions_required_readiness_checks():
    text = SCRIPT.read_text(encoding="utf-8")

    assert "scripts/agent-preflight.py" in text
    assert "scripts/model-router-policy.py" in text
    assert "scripts/todo-health.py" in text
    assert "scripts/skillopt/run-awiki-evals.sh" in text
    assert "scripts/skill-quality-report.py" in text
