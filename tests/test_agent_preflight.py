from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "agent-preflight.py"
spec = importlib.util.spec_from_file_location("agent_preflight", SCRIPT)
assert spec and spec.loader
agent_preflight = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = agent_preflight
spec.loader.exec_module(agent_preflight)


def test_exit_code_fails_only_on_fail():
    results = [
        agent_preflight.CheckResult("OK", "one", "ok"),
        agent_preflight.CheckResult("WARN", "two", "warn"),
    ]
    assert agent_preflight.exit_code(results) == 0

    results.append(agent_preflight.CheckResult("FAIL", "three", "fail"))
    assert agent_preflight.exit_code(results) == 1


def test_session_handoff_warning_is_present():
    result = agent_preflight.check_session_handoff()

    assert result.level == "WARN"
    assert "sync.py --now" in result.detail


def test_instruction_drift_detects_missing_preflight_line(monkeypatch, tmp_path):
    (tmp_path / "AGENTS.md").write_text("no preflight here\n", encoding="utf-8")
    monkeypatch.setattr(agent_preflight, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(agent_preflight, "PREFLIGHT_DOCS", ["AGENTS.md"])

    result = agent_preflight.check_instruction_drift()

    assert result.level == "FAIL"
    assert "missing preflight line" in result.detail


def test_instruction_drift_detects_missing_brain_gate_line(monkeypatch, tmp_path):
    (tmp_path / "AGENTS.md").write_text("python scripts/agent-preflight.py\n", encoding="utf-8")
    monkeypatch.setattr(agent_preflight, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(agent_preflight, "PREFLIGHT_DOCS", ["AGENTS.md"])

    result = agent_preflight.check_instruction_drift()

    assert result.level == "FAIL"
    assert "missing brain gate line" in result.detail


def test_instruction_drift_passes_when_documented(monkeypatch, tmp_path):
    (tmp_path / "AGENTS.md").write_text(
        "python scripts/agent-preflight.py\n"
        "docs/protocols/brain-improvement-gate.md\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(agent_preflight, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(agent_preflight, "PREFLIGHT_DOCS", ["AGENTS.md"])

    result = agent_preflight.check_instruction_drift()

    assert result.level == "OK"


def test_hook_command_audit_blocks_absolute_paths(monkeypatch, tmp_path):
    config = tmp_path / ".codex" / "hooks.json"
    config.parent.mkdir()
    config.write_text(
        '{"hooks":[{"command":"bash \'A:\\\\GitHub\\\\A-Wiki\\\\.codex\\\\hooks\\\\stop-auto-commit.sh\'"}]}',
        encoding="utf-8",
    )
    monkeypatch.setattr(agent_preflight, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(agent_preflight, "HOOK_CONFIGS", [".codex/hooks.json"])

    result = agent_preflight.check_hook_config_commands()

    assert result.level == "FAIL"
    assert "non-portable absolute path" in result.detail


def test_hook_command_audit_passes_relative_existing_paths(monkeypatch, tmp_path):
    hook = tmp_path / ".codex" / "hooks" / "stop-auto-commit.sh"
    hook.parent.mkdir(parents=True)
    hook.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    config = tmp_path / ".codex" / "hooks.json"
    config.write_text('{"hooks":[{"command":"bash .codex/hooks/stop-auto-commit.sh"}]}', encoding="utf-8")
    monkeypatch.setattr(agent_preflight, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(agent_preflight, "HOOK_CONFIGS", [".codex/hooks.json"])

    result = agent_preflight.check_hook_config_commands()

    assert result.level == "OK"


def test_hook_command_audit_warns_for_missing_local_config(monkeypatch, tmp_path):
    monkeypatch.setattr(agent_preflight, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(agent_preflight, "HOOK_CONFIGS", [".codex/hooks.json"])

    result = agent_preflight.check_hook_config_commands()

    assert result.level == "WARN"
    assert "local config missing" in result.detail
