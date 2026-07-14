"""tests/test_hook_stdout_encoding.py — cp874 stdout MOJIBAKE regression guard.

Distinct from tests/test_hooks_subprocess_encoding.py (AST-lint only, for
missing `encoding=` kwargs on subprocess calls that READ another process's
output — a crash-class bug, fixed 2026-07-12). This bug does NOT crash; it
silently corrupts Thai text via a write/decode encoding mismatch: a hook
writes Thai text to stdout/stderr under the console's locale codec (cp874
on Thai Windows) with no reconfigure preamble, while hooks_runner.py
hardcodes encoding="utf-8" to DECODE the captured bytes — cp874 Thai bytes
aren't valid UTF-8, so errors="replace" silently substitutes `?` for every
corrupted character. Discovered live 2026-07-14 when check_cost_tier.py's
block message printed as mojibake instead of readable Thai.

See scripts/hooks_runner.py (central PYTHONIOENCODING=utf-8 env fix + its
own reconfigure preamble) and scripts/hooks/check_cost_tier.py (targeted
reconfigure preamble, copied from check_compaction_suggest.py:114-120) for
the 3-diff fix this file guards.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOKS_RUNNER = REPO_ROOT / "scripts" / "hooks_runner.py"
CHECK_COST_TIER = REPO_ROOT / "scripts" / "hooks" / "check_cost_tier.py"

sys.path.insert(0, str(REPO_ROOT / "scripts"))

THAI_SUBSTRING = "ยังไม่ได้ประกาศ"


def _cost_gate_block_payload() -> dict:
    """A tool_input that reaches check_cost_tier.py's block path (exit 2):
    a GATE_TOOLS member (Edit), not a .tmp/ write, no declaration on disk
    (AWIKI_COST_GATE_TMP_DIR points at an empty tmp_path per test)."""
    return {
        "tool_name": "Edit",
        "tool_input": {"file_path": "wiki/test.md", "old_string": "a", "new_string": "b"},
    }


def _cp874_env(tmp_path) -> dict:
    env = {**os.environ, "PYTHONIOENCODING": "cp874", "AWIKI_COST_GATE_TMP_DIR": str(tmp_path)}
    env.pop("CI", None)
    env.pop("HOOK_SKIP", None)
    return env


# (a) full round trip through hooks_runner.py (child write-decode AND
#     hooks_runner's own re-emit)
def test_hooks_runner_check_cost_tier_roundtrips_thai_under_cp874(tmp_path):
    proc = subprocess.run(
        [sys.executable, str(HOOKS_RUNNER), "check_cost_tier"],
        input=json.dumps(_cost_gate_block_payload()),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=_cp874_env(tmp_path), cwd=str(REPO_ROOT), timeout=30,
    )
    assert proc.returncode == 2, proc.stderr
    assert THAI_SUBSTRING in proc.stderr, f"Thai text mojibaked: {proc.stderr!r}"
    assert "�" not in proc.stderr


# (b) standalone — proves the per-file preamble works independent of the runner
def test_check_cost_tier_standalone_roundtrips_thai_under_cp874(tmp_path):
    proc = subprocess.run(
        [sys.executable, str(CHECK_COST_TIER)],
        input=json.dumps(_cost_gate_block_payload()),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=_cp874_env(tmp_path), cwd=str(REPO_ROOT), timeout=30,
    )
    assert proc.returncode == 2, proc.stderr
    assert THAI_SUBSTRING in proc.stderr, f"Thai text mojibaked: {proc.stderr!r}"
    assert "�" not in proc.stderr


# (c) functional regression guard for the central fix
def test_run_hook_sets_pythonioencoding_utf8_for_child(monkeypatch):
    import hooks_runner

    captured = {}
    real_run = hooks_runner.subprocess.run

    def spy_run(*args, **kwargs):
        captured.update(kwargs)
        return real_run(*args, **kwargs)

    monkeypatch.setattr(hooks_runner.subprocess, "run", spy_run)
    hooks_runner.run_hook(
        "check_apikey.py", {"tool_name": "Bash", "tool_input": {"command": "echo hi"}}
    )
    assert captured.get("env", {}).get("PYTHONIOENCODING") == "utf-8"


# (d) no crash under cp874 (check_cost_tier specifically — not covered by
#     tests/test_check_privacy.py, which is scoped to check-privacy.py)
def test_check_cost_tier_no_crash_under_cp874(tmp_path):
    proc = subprocess.run(
        [sys.executable, str(CHECK_COST_TIER)],
        input=json.dumps(_cost_gate_block_payload()),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=_cp874_env(tmp_path), cwd=str(REPO_ROOT), timeout=30,
    )
    assert "UnicodeEncodeError" not in proc.stderr
    assert "UnicodeDecodeError" not in proc.stderr


# (e) hooks_runner's own direct writes (e.g. the ⚠️ emoji, not representable
#     in cp874) must not crash either — run ALL hooks under cp874 so
#     hooks_runner's own sys.stderr.write() relay paths get exercised too.
def test_hooks_runner_own_writes_survive_cp874(tmp_path):
    env = _cp874_env(tmp_path)
    proc = subprocess.run(
        [sys.executable, str(HOOKS_RUNNER)],
        input=json.dumps({"tool_name": "Bash", "tool_input": {"command": "echo hi"}}),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(REPO_ROOT), timeout=30,
    )
    assert "UnicodeEncodeError" not in proc.stderr
    assert proc.returncode == 0, proc.stderr
