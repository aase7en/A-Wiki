from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SESSION_START = REPO_ROOT / "scripts" / "hooks" / "session_start.py"


spec = importlib.util.spec_from_file_location("session_start", SESSION_START)
assert spec and spec.loader
session_start = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = session_start
spec.loader.exec_module(session_start)


def test_session_start_exposes_model_intel_hook():
    assert hasattr(session_start, "maybe_update_model_intel")


def test_session_start_todos_only_reads_active_unchecked_block(tmp_path, capsys):
    session_dir = tmp_path / "wiki" / "context"
    session_dir.mkdir(parents=True)
    (session_dir / "session-memory.md").write_text(
        "## 🔥 Active TODOs (cross-session)\n\n"
        "- [ ] **[keep]** active item\n"
        "- [x] **[done]** checked item\n"
        "\n## Recent\n\n"
        "- [ ] **[old]** old item\n",
        encoding="utf-8",
    )

    session_start.show_todos(str(tmp_path))

    captured = capsys.readouterr()
    assert "[keep]" in captured.err
    assert "[done]" not in captured.err
    assert "[old]" not in captured.err


def test_update_model_intel_script_is_drive_safe_and_grounded():
    script = REPO_ROOT / "scripts" / "update-ai-model-intel.sh"
    text = script.read_text(encoding="utf-8")

    assert "AWIKI_MODEL_INTEL_ON_START" in text
    assert ".tmp/model-intel" in text
    assert "google_search" in text
    assert "wiki/context/model-intel" not in text


def test_model_roster_refresh_script_is_ci_safe():
    script = REPO_ROOT / "scripts" / "update-model-roster.sh"
    text = script.read_text(encoding="utf-8")

    assert "--ci-ok" in text
    assert "--report PATH" in text
    assert "write_report" in text
    assert "OPENROUTER_API_KEY not set. Skipped live model roster query." in text
    assert "model-roster.conf.bak" in text


def test_model_roster_refresh_workflow_reports_without_auto_commit():
    workflow = REPO_ROOT / ".github" / "workflows" / "model-roster-refresh.yml"
    text = workflow.read_text(encoding="utf-8")

    assert "schedule:" in text
    assert "OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}" in text
    assert "--ci-ok" in text
    assert "actions/upload-artifact@v4" in text
    assert "gh issue create" in text
    assert "git commit" not in text
    assert "git push" not in text


def test_skillopt_refresh_keeps_upstream_snapshot_lightweight():
    script = REPO_ROOT / "scripts" / "refresh-skillopt.sh"
    text = script.read_text(encoding="utf-8")

    assert "https://github.com/microsoft/SkillOpt.git" in text
    assert "agent-skills/_upstream/skillopt" in text
    assert "SKILLOPT_FULL_SNAPSHOT" in text
    assert "skillopt_webui" in text
    assert "skillopt-assets" in text


def test_skillopt_installer_uses_ignored_local_targets():
    script = REPO_ROOT / "scripts" / "install-skillopt-local.sh"
    text = script.read_text(encoding="utf-8")

    assert ".tmp/skillopt-src" in text
    assert ".venv-skillopt" in text
    assert "pip install -e" in text
