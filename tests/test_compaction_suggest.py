"""
Tests for check_compaction_suggest.py — strategic /compact suggester (hook #16).

The hook reads the Claude Code transcript (JSONL) on UserPromptSubmit,
estimates current context size from the latest assistant `usage` entry,
and prints a Thai /compact suggestion to stdout when usage crosses a
threshold percentage of the context window. Always exits 0 (never blocks).

State file lives in AWIKI_COMPACT_SUGGEST_TMP_DIR (tests) or .tmp/ (prod)
so the same level is suggested only once, re-suggested every +STEP pp,
and reset after a compaction shrinks the context.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = str(REPO_ROOT / "scripts" / "hooks" / "check_compaction_suggest.py")

# Default window 200_000 / threshold 75% / step 10pp
WINDOW = 200_000


def _usage_line(input_tokens: int, cache_read: int = 0, cache_creation: int = 0) -> str:
    return json.dumps({
        "type": "assistant",
        "message": {
            "role": "assistant",
            "usage": {
                "input_tokens": input_tokens,
                "cache_read_input_tokens": cache_read,
                "cache_creation_input_tokens": cache_creation,
            },
        },
    })


def _write_transcript(path: Path, *lines: str) -> Path:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _run_hook(payload: dict, tmp_dir: Path, extra_env: dict | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, "AWIKI_COMPACT_SUGGEST_TMP_DIR": str(tmp_dir)}
    env.pop("HOOK_SKIP", None)
    env.pop("AWIKI_COMPACT_SUGGEST", None)
    env.pop("AWIKI_COMPACT_SUGGEST_PCT", None)
    env.pop("AWIKI_COMPACT_SUGGEST_STEP", None)
    env.pop("AWIKI_CONTEXT_WINDOW", None)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, HOOK_PATH],
        input=json.dumps(payload),
        capture_output=True, text=True,
        encoding="utf-8", errors="replace",
        env=env,
        cwd=str(REPO_ROOT),
    )


def _payload(transcript: Path | None, session_id: str = "sess-test") -> dict:
    data = {"session_id": session_id, "hook_event_name": "UserPromptSubmit"}
    if transcript is not None:
        data["transcript_path"] = str(transcript)
    return data


class TestFailSoft:
    """Hook must never break the prompt flow — exit 0 + silence on any problem."""

    def test_no_transcript_path_silent(self, tmp_path):
        proc = _run_hook(_payload(None), tmp_path)
        assert proc.returncode == 0, proc.stderr
        assert proc.stdout.strip() == ""

    def test_missing_transcript_file_silent(self, tmp_path):
        proc = _run_hook(_payload(tmp_path / "nope.jsonl"), tmp_path)
        assert proc.returncode == 0, proc.stderr
        assert proc.stdout.strip() == ""

    def test_malformed_transcript_silent(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", "not json at all", "{broken", "")
        proc = _run_hook(_payload(t), tmp_path)
        assert proc.returncode == 0, proc.stderr
        assert proc.stdout.strip() == ""

    def test_empty_stdin_silent(self, tmp_path):
        env = {**os.environ, "AWIKI_COMPACT_SUGGEST_TMP_DIR": str(tmp_path)}
        proc = subprocess.run(
            [sys.executable, HOOK_PATH],
            input="", capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            env=env, cwd=str(REPO_ROOT),
        )
        assert proc.returncode == 0, proc.stderr
        assert proc.stdout.strip() == ""


class TestThreshold:
    def test_below_threshold_silent(self, tmp_path):
        # 50% of 200k = well below default 75%
        t = _write_transcript(tmp_path / "t.jsonl", _usage_line(100_000))
        proc = _run_hook(_payload(t), tmp_path)
        assert proc.returncode == 0, proc.stderr
        assert proc.stdout.strip() == ""

    def test_above_threshold_warns(self, tmp_path):
        # 80% of 200k
        t = _write_transcript(tmp_path / "t.jsonl", _usage_line(160_000))
        proc = _run_hook(_payload(t), tmp_path)
        assert proc.returncode == 0, proc.stderr
        assert "/compact" in proc.stdout

    def test_cache_tokens_counted_in_context(self, tmp_path):
        # input 1k + cache_read 150k + cache_creation 10k = 161k = 80.5%
        t = _write_transcript(tmp_path / "t.jsonl", _usage_line(1_000, cache_read=150_000, cache_creation=10_000))
        proc = _run_hook(_payload(t), tmp_path)
        assert "/compact" in proc.stdout

    def test_uses_latest_usage_line(self, tmp_path):
        # earlier line low, latest line high → must warn
        t = _write_transcript(
            tmp_path / "t.jsonl",
            _usage_line(60_000),
            json.dumps({"type": "user", "message": {"role": "user", "content": "hi"}}),
            _usage_line(170_000),
        )
        proc = _run_hook(_payload(t), tmp_path)
        assert "/compact" in proc.stdout

    def test_custom_threshold_env(self, tmp_path):
        # 60% with threshold lowered to 50 → warns
        t = _write_transcript(tmp_path / "t.jsonl", _usage_line(120_000))
        proc = _run_hook(_payload(t), tmp_path, {"AWIKI_COMPACT_SUGGEST_PCT": "50"})
        assert "/compact" in proc.stdout

    def test_custom_window_env(self, tmp_path):
        # 120k of a 130k window = 92% → warns even though below default 200k threshold
        t = _write_transcript(tmp_path / "t.jsonl", _usage_line(120_000))
        proc = _run_hook(_payload(t), tmp_path, {"AWIKI_CONTEXT_WINDOW": "130000"})
        assert "/compact" in proc.stdout


class TestStateMachine:
    """Warn once per level; re-warn per +step; reset after compaction."""

    def test_same_level_not_repeated(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", _usage_line(160_000))
        first = _run_hook(_payload(t), tmp_path)
        second = _run_hook(_payload(t), tmp_path)
        assert "/compact" in first.stdout
        assert second.stdout.strip() == ""

    def test_regrow_past_step_warns_again(self, tmp_path):
        t1 = _write_transcript(tmp_path / "t.jsonl", _usage_line(152_000))   # 76%
        first = _run_hook(_payload(t1), tmp_path)
        t2 = _write_transcript(tmp_path / "t.jsonl", _usage_line(176_000))   # 88% >= 76+10
        second = _run_hook(_payload(t2), tmp_path)
        assert "/compact" in first.stdout
        assert "/compact" in second.stdout

    def test_reset_after_compaction(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", _usage_line(160_000))    # 80% → warn
        _run_hook(_payload(t), tmp_path)
        t = _write_transcript(tmp_path / "t.jsonl", _usage_line(60_000))     # 30% → compacted, reset
        mid = _run_hook(_payload(t), tmp_path)
        t = _write_transcript(tmp_path / "t.jsonl", _usage_line(160_000))    # 80% again → warn again
        again = _run_hook(_payload(t), tmp_path)
        assert mid.stdout.strip() == ""
        assert "/compact" in again.stdout

    def test_state_isolated_per_session(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", _usage_line(160_000))
        first = _run_hook(_payload(t, session_id="sess-a"), tmp_path)
        other = _run_hook(_payload(t, session_id="sess-b"), tmp_path)
        assert "/compact" in first.stdout
        assert "/compact" in other.stdout


class TestOptOut:
    def test_disabled_by_env(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", _usage_line(180_000))
        proc = _run_hook(_payload(t), tmp_path, {"AWIKI_COMPACT_SUGGEST": "0"})
        assert proc.returncode == 0
        assert proc.stdout.strip() == ""

    def test_hook_skip_respected(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", _usage_line(180_000))
        proc = _run_hook(_payload(t), tmp_path, {"HOOK_SKIP": "check_compaction_suggest"})
        assert proc.returncode == 0
        assert proc.stdout.strip() == ""


class TestWiring:
    def test_settings_json_wires_user_prompt_submit(self):
        settings = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        blocks = settings.get("hooks", {}).get("UserPromptSubmit", [])
        commands = [
            h.get("command", "")
            for block in blocks
            for h in block.get("hooks", [])
        ]
        assert any("check_compaction_suggest" in c for c in commands), (
            "check_compaction_suggest.py must be wired directly (not via hooks_runner, "
            "which swallows stdout) under hooks.UserPromptSubmit"
        )
