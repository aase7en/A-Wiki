"""Tests for scripts/hooks/check_a_route.py — Claude auto-suggest (A-Suite C7).

Wiring contract this pins down: the hook is wired DIRECT on UserPromptSubmit,
emits on stdout with a bare print(), and always exits 0.

hooks_runner.py uses subprocess.run(capture_output=True) and re-emits only
stderr, and only when the child exits 2. Routing this hook through the runner
would silently discard every suggestion it ever makes.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "hooks" / "check_a_route.py"


def run(prompt: str, session: str = "routetest", env_extra=None, state_dir: Path | None = None):
    env = dict(os.environ)
    env.pop("HOOK_SKIP", None)
    env.pop("AWIKI_A_ROUTE", None)
    if state_dir is not None:
        env["AWIKI_ROUTE_STATE_DIR"] = str(state_dir)
    env.update(env_extra or {})
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({"prompt": prompt, "session_id": session}),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(REPO_ROOT), timeout=30,
    )


class TestSuggestion:
    def test_thai_bug_prompt_suggests_a_debug(self, tmp_path):
        r = run("ช่วยแก้บั๊ก dashboard หน่อย", state_dir=tmp_path)
        assert r.returncode == 0
        assert "A-Debug" in r.stdout

    def test_english_design_prompt_suggests_a_plan(self, tmp_path):
        r = run("help me design the architecture", state_dir=tmp_path)
        assert r.returncode == 0
        assert "A-Plan" in r.stdout

    def test_unrelated_prompt_stays_silent(self, tmp_path):
        r = run("สวัสดีครับ", state_dir=tmp_path)
        assert r.returncode == 0
        assert r.stdout.strip() == "", "must not guess when nothing matches"

    def test_greeting_in_english_stays_silent(self, tmp_path):
        r = run("what is the weather today", state_dir=tmp_path)
        assert r.stdout.strip() == ""

    def test_suggestion_goes_to_stdout_not_stderr(self, tmp_path):
        """Direct-wired hooks reach the model via stdout only."""
        r = run("ช่วยแก้บั๊กหน่อย", state_dir=tmp_path)
        assert r.stdout.strip()
        assert "A-Debug" not in r.stderr


class TestAntiSpam:
    def test_same_suggestion_is_not_repeated_back_to_back(self, tmp_path):
        first = run("ช่วยแก้บั๊กหน่อย", state_dir=tmp_path)
        second = run("แก้บั๊กต่อ", state_dir=tmp_path)
        assert first.stdout.strip()
        assert second.stdout.strip() == "", "should not nag with the same skill twice"

    def test_a_different_skill_is_still_suggested(self, tmp_path):
        run("ช่วยแก้บั๊กหน่อย", state_dir=tmp_path)
        r = run("ออกแบบ schema ใหม่", state_dir=tmp_path)
        assert "A-Plan" in r.stdout

    def test_sessions_do_not_share_anti_spam_state(self, tmp_path):
        run("ช่วยแก้บั๊กหน่อย", session="s1", state_dir=tmp_path)
        r = run("ช่วยแก้บั๊กหน่อย", session="s2", state_dir=tmp_path)
        assert "A-Debug" in r.stdout

    def test_session_id_with_path_characters_is_sanitised(self, tmp_path):
        r = run("ช่วยแก้บั๊กหน่อย", session="../../evil id", state_dir=tmp_path)
        assert r.returncode == 0
        for p in tmp_path.iterdir():
            assert ".." not in p.name


class TestFailOpen:
    def test_opt_out_env_silences_the_hook(self, tmp_path):
        r = run("ช่วยแก้บั๊กหน่อย", env_extra={"AWIKI_A_ROUTE": "0"}, state_dir=tmp_path)
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_hook_skip_silences_the_hook(self, tmp_path):
        r = run("ช่วยแก้บั๊กหน่อย", env_extra={"HOOK_SKIP": "check_a_route"}, state_dir=tmp_path)
        assert r.stdout.strip() == ""

    def test_malformed_stdin_exits_zero(self):
        r = subprocess.run([sys.executable, str(HOOK)], input="not json",
                           capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=30)
        assert r.returncode == 0

    def test_empty_prompt_exits_zero_quietly(self, tmp_path):
        r = run("", state_dir=tmp_path)
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_thai_output_survives_cp874_console(self, tmp_path):
        r = run("ช่วยแก้บั๊กหน่อย", env_extra={"PYTHONIOENCODING": "cp874"}, state_dir=tmp_path)
        assert r.returncode == 0
        assert "Traceback" not in r.stderr

    def test_thai_prompt_arrives_intact_from_raw_utf8_bytes(self, tmp_path):
        """Regression: stdin must be decoded as UTF-8, not the ambient codepage.

        The original hook reconfigured stdout/stderr but not stdin. On this
        Windows box the default is cp874, so a Thai prompt piped in as raw UTF-8
        bytes decoded to mojibake ('ช่วยแก้บั๊ก' -> '\\udc8a\\udc88วย...'), matched no
        trigger, and the hook went silently dead in the language it matters most
        for. The other tests missed it because subprocess.run(encoding="utf-8")
        papers over the difference — so this one writes BYTES deliberately.
        """
        payload = json.dumps(
            {"prompt": "ช่วยแก้บั๊ก dashboard หน่อย", "session_id": "bytes"},
            ensure_ascii=False,
        ).encode("utf-8")
        env = dict(os.environ)
        env.pop("HOOK_SKIP", None)
        env.pop("AWIKI_A_ROUTE", None)
        env.pop("PYTHONIOENCODING", None)      # do not let the shim hide the bug
        env["AWIKI_ROUTE_STATE_DIR"] = str(tmp_path)
        r = subprocess.run([sys.executable, str(HOOK)], input=payload,
                           capture_output=True, env=env, cwd=str(REPO_ROOT), timeout=30)
        assert r.returncode == 0
        assert "A-Debug" in r.stdout.decode("utf-8", "replace")

    def test_runs_well_within_the_hook_timeout(self, tmp_path):
        import time
        t0 = time.time()
        run("ช่วยแก้บั๊กหน่อย", state_dir=tmp_path)
        assert time.time() - t0 < 5.0, "must fit the 5s hook budget"


class TestWiring:
    def test_wired_direct_on_userpromptsubmit_not_via_runner(self):
        cfg = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        cmds = [
            h.get("command", "")
            for grp in cfg["hooks"].get("UserPromptSubmit", [])
            for h in grp.get("hooks", [])
        ]
        mine = [c for c in cmds if "check_a_route.py" in c]
        assert mine, "check_a_route.py not wired on UserPromptSubmit"
        for c in mine:
            assert "hooks_runner" not in c, (
                "must be direct — hooks_runner captures stdout, so suggestions "
                "would never reach the model"
            )
