"""Tests for scripts/hooks/check_harness_routing.py — universal routing gate.

Blocks Write/Edit on wiki/sources/<slug>.md if frontmatter lacks
`routed_via: harness@v\d+`. Enforces cost-aware harness routing.

Pattern A (subprocess) via hooks_runner (hook doesn't self-check HOOK_SKIP).
"""
from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNNER = REPO_ROOT / "scripts" / "hooks_runner.py"


def _run(payload: dict, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ); env.update(env_extra or {})
    return subprocess.run([sys.executable, str(RUNNER), "check-harness-routing"],
        input=json.dumps(payload), capture_output=True, text=True,
        encoding="utf-8", errors="replace", env=env, cwd=str(REPO_ROOT), timeout=30)


def test_passes_for_non_edit_tool():
    assert _run({"tool_name": "Bash", "tool_input": {}}).returncode == 0


def test_passes_for_non_wiki_sources_file():
    payload = {"tool_name": "Write",
               "tool_input": {"file_path": "scripts/foo.py", "content": "x"}}
    assert _run(payload).returncode == 0


def test_fail_open_on_non_json():
    r = subprocess.run([sys.executable, str(RUNNER), "check-harness-routing"], input="{{{",
        capture_output=True, text=True, env=os.environ, cwd=str(REPO_ROOT), timeout=30)
    assert r.returncode == 0


class TestWiring:
    def test_registered_in_pretooluse_edit_matcher(self):
        cfg = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        for grp in cfg["hooks"].get("PreToolUse", []):
            if "Edit" in grp.get("matcher", ""):
                for h in grp.get("hooks", []):
                    if "harness-routing" in h.get("command", "") or "harness_routing" in h.get("command", ""):
                        return
        raise AssertionError("check_harness_routing must be on Edit PreToolUse matcher")
