"""Regression tests for the self_audit ship gate's visibility.

Phase 6 routes registered hooks through the canonical runner.  self_audit is a
soft Stop advisor, so its user-facing stdout must remain visible through the
registry's ``allow_context_stdout`` policy instead of bypassing the runner.

These tests pin down both requirements:
  1. Stop wiring uses the canonical runner in Claude and Codex;
  2. registry policy explicitly allows self_audit contextual stdout.
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
    @pytest.mark.parametrize(
        "cfg_path,provider",
        [(".claude/settings.json", "claude"), (".codex/hooks.json", "codex")],
    )
    def test_wired_on_stop_through_canonical_runner_with_context(self, cfg_path, provider):
        cfg = json.loads((REPO_ROOT / cfg_path).read_text(encoding="utf-8"))
        cmds = [
            h.get("command", "")
            for grp in cfg["hooks"].get("Stop", [])
            for h in grp.get("hooks", [])
        ]
        expected = f"hooks_runner.py --provider {provider} --event Stop"
        assert any(expected in c for c in cmds), (
            f"{cfg_path}: Stop must dispatch through the canonical provider event sweep"
        )
        sys.path.insert(0, str(REPO_ROOT / "scripts" / "hooks"))
        import registry
        entry = registry.HOOK_REGISTRY["self_audit"]
        assert "Stop" in entry["events"]
        assert entry["allow_context_stdout"] is True


class TestOutputChannel:
    def test_user_facing_messages_go_to_stdout(self):
        """Runner context forwarding preserves the hook's user-facing stdout."""
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

    def test_runtime_state_has_explicit_isolation_seams(self):
        """P6-R06: self-audit tests must not borrow live repo state."""
        assert "AWIKI_BLACKBOARD_PATH" in SOURCE
        assert "AWIKI_MEMORY_LEDGER_PATH" in SOURCE


class TestBehaviour:
    """End-to-end against a seeded blackboard under pytest tmp_path only."""

    @pytest.fixture
    def seeded_blackboard(self, tmp_path):
        import time
        bb = tmp_path / "blackboard.jsonl"
        led = tmp_path / "memory-ledger.jsonl"
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
        return {
            "AWIKI_BLACKBOARD_PATH": str(bb),
            "AWIKI_MEMORY_LEDGER_PATH": str(led),
        }

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
        r = self._run(seeded_blackboard)
        assert r.returncode == 0, "the gate must never hard-kill a session"
        assert "BLOCK SHIP" in r.stdout
        assert "critical" in r.stdout

    def test_survives_a_cp874_console(self, seeded_blackboard):
        r = self._run({**seeded_blackboard, "PYTHONIOENCODING": "cp874"})
        assert r.returncode == 0
        assert "[self-audit] error:" not in r.stdout, "emoji crash swallowed again"
        assert "BLOCK SHIP" in r.stdout

    def test_hook_skip_silences_it(self, seeded_blackboard):
        r = self._run({**seeded_blackboard, "HOOK_SKIP": "self_audit,check_apikey"})
        assert r.returncode == 0
        assert r.stdout.strip() == ""
