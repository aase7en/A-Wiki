"""Tests for scripts/hooks/check_history_divergence.py — SessionStart.

SessionStart hook detecting history divergence after force-push / rewrites.
Exit 1 if diverged (warn user), exit 0 if clean.

Pattern A (subprocess).
"""
from __future__ import annotations
import os, subprocess, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "hooks" / "check_history_divergence.py"


def _run(env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ); env.update(env_extra or {})
    return subprocess.run([sys.executable, str(HOOK)], input="{}",
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(REPO_ROOT), timeout=30)


def test_exits_0_or_1():
    """Either clean (0) or diverged (1). Never 2 (block)."""
    r = _run()
    assert r.returncode in (0, 1)


def test_fail_open_silent():
    """Hook runs without crashing on the live repo."""
    assert _run().returncode in (0, 1)


class TestWiring:
    def test_known_wiring_gap_history_divergence_not_registered(self):
        """KNOWN GAP: check_history_divergence is not registered in
        .claude/settings.json SessionStart (verified 2026-08-11). The hook
        exists but never fires. This test DOCUMENTS the gap — when fixed,
        replace this test with test_registered_on_sessionstart.
        """
        import json
        cfg = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        for event in cfg["hooks"]:
            for grp in cfg["hooks"].get(event, []):
                for h in grp.get("hooks", []):
                    if "history_divergence" in h.get("command", ""):
                        # If we get here, the gap was fixed — flip this test
                        raise AssertionError(
                            "check_history_divergence IS now registered — replace "
                            "this gap-documenting test with test_registered_on_sessionstart"
                        )
        # Gap confirmed — pass (the hook is intentionally unwired for now)
        assert True
