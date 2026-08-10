"""Tests for scripts/hooks/release_agent_claims.py — Stop hook.

Stop hook: hand back this session's work claims so the next agent doesn't
get a collision block for work nobody is doing. Wired DIRECT on Stop
(not via hooks_runner — swallows exit-0 stdout). Always exits 0.
"""
from __future__ import annotations
import os, subprocess, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "hooks" / "release_agent_claims.py"


def _run(env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ); env.update(env_extra or {})
    return subprocess.run([sys.executable, str(HOOK)], input="{}",
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(REPO_ROOT), timeout=30)


def test_always_exits_zero():
    """Stop hook — never blocks session end."""
    assert _run().returncode == 0


def test_fail_open_silent():
    """Runs without crashing on the live repo."""
    assert _run().returncode == 0


class TestWiring:
    def test_registered_on_stop(self):
        import json
        cfg = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        for grp in cfg["hooks"].get("Stop", []):
            for h in grp.get("hooks", []):
                if "release_agent_claims" in h.get("command", ""):
                    return
        raise AssertionError("release_agent_claims must be registered on Stop")

    def test_wired_direct_not_via_hooks_runner(self):
        import json
        cfg = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        for grp in cfg["hooks"].get("Stop", []):
            for h in grp.get("hooks", []):
                c = h.get("command", "")
                if "release_agent_claims" in c:
                    assert "hooks_runner" not in c, (
                        "release_agent_claims must be wired DIRECT — runner swallows exit-0 stdout"
                    )
                    return
        raise AssertionError("release_agent_claims not found on Stop")
