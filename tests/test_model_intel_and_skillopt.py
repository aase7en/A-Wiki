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


def test_update_model_intel_script_is_drive_safe_and_grounded():
    script = REPO_ROOT / "scripts" / "update-ai-model-intel.sh"
    text = script.read_text(encoding="utf-8")

    assert "AWIKI_MODEL_INTEL_ON_START" in text
    assert ".tmp/model-intel" in text
    assert "google_search" in text
    assert "wiki/context/model-intel" not in text


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
