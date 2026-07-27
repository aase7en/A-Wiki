"""Regression tests for the self_audit ship gate's visibility.

self_audit.py landed as a Stop hook that always exits 0 and wrote to stderr,
wired through hooks_runner.py. hooks_runner.run_hook uses
subprocess.run(capture_output=True) and re-emits stderr ONLY when the child
exits 2 — so every warning the ship gate ever produced was discarded. The gate
existed, ran on every session, and had never once spoken to anyone.

These tests pin down the two properties that fix required:
  1. it is wired DIRECTLY on Stop, not through the runner
  2. it writes to stdout, which is the channel a direct-wired hook reaches the
     user on
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "hooks" / "self_audit.py"
SOURCE = HOOK.read_text(encoding="utf-8")


class TestWiring:
    @pytest.mark.parametrize("cfg_path", [".claude/settings.json", ".codex/hooks.json"])
    def test_wired_direct_on_stop_not_through_the_runner(self, cfg_path):
        cfg = json.loads((REPO_ROOT / cfg_path).read_text(encoding="utf-8"))
        cmds = [
            h.get("command", "")
            for grp in cfg["hooks"].get("Stop", [])
            for h in grp.get("hooks", [])
        ]
        mine = [c for c in cmds if "self_audit" in c or "self-audit" in c]
        assert mine, f"{cfg_path}: self_audit not wired on Stop"
        for c in mine:
            assert "hooks_runner" not in c, (
                f"{cfg_path}: self_audit routed through hooks_runner, which "
                f"swallows the stdout of an exit-0 hook — its warnings would be "
                f"invisible again"
            )


class TestOutputChannel:
    def test_user_facing_messages_go_to_stdout(self):
        """A direct-wired Stop hook reaches the user on stdout."""
        _, _, main_body = SOURCE.partition("def main() -> int:")
        assert "sys.stderr.write(" not in main_body, (
            "main() still writes user-facing output to stderr"
        )
        assert "_emit(" in main_body

    def test_has_a_utf8_preamble(self):
        """It prints ⛔ / ⚠️ / ✅ — without this it dies on a cp874 console."""
        assert "reconfigure" in SOURCE and "utf-8" in SOURCE

    def test_hook_skip_uses_substring_match_like_every_other_hook(self):
        """Exact equality meant HOOK_SKIP='self_audit,other' failed to skip it."""
        assert 'os.environ.get("HOOK_SKIP") == "self_audit"' not in SOURCE
        assert '"self_audit" in os.environ.get("HOOK_SKIP"' in SOURCE


class TestBehaviour:
    """End-to-end against a seeded blackboard, restoring the real one after."""

    @pytest.fixture
    def seeded_blackboard(self, monkeypatch):
        import shutil, time
        bb = REPO_ROOT / ".tmp" / "blackboard.jsonl"
        bak = REPO_ROOT / ".tmp" / "blackboard.jsonl.pytest-bak"
        bb.parent.mkdir(exist_ok=True)
        had = bb.exists()
        if had:
            shutil.copy2(bb, bak)
        now = time.time()
        rows = [
            {"ts": now, "thread_id": "PYTEST", "frm": "claude", "to": "*",
             "type": "proposal", "tags": ["council"], "topic": "pytest gate",
             "body": "review"},
            {"ts": now + 1, "thread_id": "PYTEST", "frm": "security-auditor",
             "to": "*", "type": "answer", "tags": ["council"],
             "persona": "security-auditor", "severity": "critical",
             "finding": "pytest fixture finding", "body": "pytest fixture finding"},
        ]
        bb.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
        yield bb
        if had:
            shutil.move(str(bak), str(bb))
        else:
            bb.unlink(missing_ok=True)
        # drop the ledger rows this fixture caused
        led = REPO_ROOT / ".tmp" / "memory-ledger.jsonl"
        if led.exists():
            keep = [
                l for l in led.read_text(encoding="utf-8").splitlines()
                if l.strip() and "pytest fixture finding" not in l
            ]
            led.write_text("\n".join(keep) + ("\n" if keep else ""), encoding="utf-8")

    def _run(self, env_extra=None):
        env = dict(os.environ)
        env.pop("HOOK_SKIP", None)
        env.update(env_extra or {})
        return subprocess.run(
            [sys.executable, str(HOOK)], input="{}", capture_output=True,
            text=True, encoding="utf-8", errors="replace",
            env=env, cwd=str(REPO_ROOT), timeout=30,
        )

    def test_critical_finding_reaches_stdout(self, seeded_blackboard):
        r = self._run()
        assert r.returncode == 0, "the gate must never hard-kill a session"
        assert "BLOCK SHIP" in r.stdout
        assert "critical" in r.stdout

    def test_survives_a_cp874_console(self, seeded_blackboard):
        r = self._run({"PYTHONIOENCODING": "cp874"})
        assert r.returncode == 0
        assert "[self-audit] error:" not in r.stdout, "emoji crash swallowed again"
        assert "BLOCK SHIP" in r.stdout

    def test_hook_skip_silences_it(self, seeded_blackboard):
        r = self._run({"HOOK_SKIP": "self_audit,check_apikey"})
        assert r.returncode == 0
        assert r.stdout.strip() == ""
