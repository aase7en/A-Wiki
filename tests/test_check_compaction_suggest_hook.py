"""Tests for scripts/hooks/check_compaction_suggest.py — UserPromptSubmit.

UserPromptSubmit advisory: estimates context usage from session transcript
and prints /compact suggestion when usage > 75% of context window.
Wired DIRECT (not via hooks_runner — stdout must reach the model).
"""
from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "hooks" / "check_compaction_suggest.py"


def _run(payload: dict, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ); env.update(env_extra or {})
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(REPO_ROOT), timeout=30)


def test_always_exits_zero():
    """UserPromptSubmit hooks must never block — exit 0 always."""
    r = _run({"prompt": "hello", "session_id": "test"})
    assert r.returncode == 0


def test_fail_open_silent():
    """Runs without crashing on a minimal payload."""
    r = _run({"prompt": "hello", "session_id": "test"})
    assert r.returncode == 0


class TestWiring:
    def test_registered_on_userpromptsubmit(self):
        cfg = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        for grp in cfg["hooks"].get("UserPromptSubmit", []):
            for h in grp.get("hooks", []):
                if "compaction" in h.get("command", ""):
                    return
        raise AssertionError("check_compaction_suggest must be on UserPromptSubmit")

    def test_wired_direct_not_via_hooks_runner(self):
        cfg = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        for grp in cfg["hooks"].get("UserPromptSubmit", []):
            for h in grp.get("hooks", []):
                c = h.get("command", "")
                if "compaction" in c:
                    assert "hooks_runner" not in c, (
                        "check_compaction_suggest must be wired DIRECT — stdout must reach model"
                    )
                    return
        raise AssertionError("check_compaction_suggest not found on UserPromptSubmit")
