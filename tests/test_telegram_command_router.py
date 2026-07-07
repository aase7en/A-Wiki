"""
Tests for scripts/hermes/telegram-command-router.py — the slash-command router.

Closes the C4 gap (docs/architecture/hermes-cross-agent-handoff.md §"C4 RESULTS"):
``/spec /plan /build /review /ship /search /wiki`` returned ``Unknown command`` on
the live Pi5 Telegram bot because the A-Wiki lifecycle skills existed on-device
but had NO Telegram command trigger. This router maps each ``/<cmd> <args>``
message to a backing script (``search-wiki.py`` or ``persona-orchestrator.py``).

Tests cover the PURE logic only: no subprocess, no real Hermes/search-wiki call
(Iron Law #1 — failing-first, CI-safe). Mirrors the import + stub-runner pattern
of tests/test_persona_orchestrator.py.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# scripts/hermes/ has no __init__.py (it is not an importable package), and the
# active interpreter's venv may shadow a same-named module. Load the file by
# absolute path via importlib so the test is hermetic to the environment.
import importlib.util as _ilu  # noqa: E402

_TCR_PATH = REPO_ROOT / "scripts" / "hermes" / "telegram-command-router.py"
_spec = _ilu.spec_from_file_location("telegram_command_router", _TCR_PATH)
assert _spec is not None and _spec.loader is not None, f"cannot load {_TCR_PATH}"
tcr = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(tcr)  # type: ignore[union-attr]

COMMAND_MAP = REPO_ROOT / "scripts" / "hermes" / "telegram-commands.json"
SEARCH_COMMANDS = ["wiki", "search"]
LIFECYCLE_COMMANDS = ["review", "spec", "plan", "build", "ship"]


# ---------------------------------------------------------------------------
# resolve_command — parse a Telegram message into (command, args)
# ---------------------------------------------------------------------------

class TestResolveCommand:
    """resolve_command(text) splits '/cmd rest' into (command, args)."""

    def test_simple_command_with_args(self) -> None:
        assert tcr.resolve_command("/wiki mqtt broker") == ("wiki", "mqtt broker")

    def test_command_with_no_args(self) -> None:
        assert tcr.resolve_command("/status") == ("status", "")

    def test_multi_word_args_preserved(self) -> None:
        assert tcr.resolve_command("/review review the auth refactor") == (
            "review", "review the auth refactor",
        )

    def test_plain_message_without_slash_returns_empty_command(self) -> None:
        # A plain (non-slash) message is not a command: command == "", args == whole text.
        cmd, args = tcr.resolve_command("สวัสดี hello there")
        assert cmd == ""
        assert args == "สวัสดี hello there"

    def test_leading_whitespace_before_slash_is_tolerated(self) -> None:
        assert tcr.resolve_command("  /wiki mqtt") == ("wiki", "mqtt")

    def test_trailing_whitespace_in_args_is_stripped(self) -> None:
        assert tcr.resolve_command("/wiki mqtt   ") == ("wiki", "mqtt")

    def test_only_command_word_returns_empty_args(self) -> None:
        assert tcr.resolve_command("/ship") == ("ship", "")


# ---------------------------------------------------------------------------
# build_route — pure argv construction (the heart of the unit test)
# ---------------------------------------------------------------------------

class TestBuildRoute:
    """build_route(command, args) maps a command to a target script + argv WITHOUT running anything."""

    def test_search_command_targets_search_wiki_script(self) -> None:
        route = tcr.build_route("wiki", "mqtt broker")
        assert route["command"] == "wiki"
        assert route["target_script"] == "scripts/wiki/search-wiki.py"
        assert route["kind"] == "search"
        assert route["task_or_query"] == "mqtt broker"

    def test_search_argv_includes_query_and_json_and_limit(self) -> None:
        route = tcr.build_route("wiki", "mqtt broker", limit=5)
        argv = route["argv"]
        # The query must be a single argv element (not shell-split).
        assert "mqtt broker" in argv
        assert "--json" in argv
        assert "--limit" in argv
        # Limit value must follow the flag.
        limit_idx = argv.index("--limit")
        assert argv[limit_idx + 1] == "5"

    def test_orchestrate_command_targets_persona_orchestrator(self) -> None:
        route = tcr.build_route("review", "review PR #42")
        assert route["command"] == "review"
        assert route["target_script"] == "scripts/hermes/persona-orchestrator.py"
        assert route["kind"] == "orchestrate"
        assert route["phase"] == "review"
        assert route["task_or_query"] == "review PR #42"

    def test_orchestrate_argv_includes_task_flag(self) -> None:
        route = tcr.build_route("plan", "break down the API work")
        argv = route["argv"]
        assert "--task" in argv
        task_idx = argv.index("--task")
        # Task must be a single argv element (preserves spaces).
        assert argv[task_idx + 1] == "break down the API work"

    def test_phase_is_none_for_search_commands(self) -> None:
        for cmd in SEARCH_COMMANDS:
            route = tcr.build_route(cmd, "query")
            assert route["phase"] is None, f"{cmd} must have no lifecycle phase"

    def test_phase_set_for_each_lifecycle_command(self) -> None:
        for cmd in LIFECYCLE_COMMANDS:
            route = tcr.build_route(cmd, "task")
            assert route["phase"] == cmd, f"{cmd} phase must equal command name"

    def test_route_is_serializable_json(self) -> None:
        # --dry-run prints the route as JSON; it must round-trip.
        route = tcr.build_route("wiki", "mqtt broker")
        json.dumps(route)  # raises if not serializable


# ---------------------------------------------------------------------------
# load_command_map — read the route map from telegram-commands.json
# ---------------------------------------------------------------------------

class TestLoadCommandMap:
    """load_command_map(path) reads the slash-command → script map."""

    def test_loads_all_seven_commands_from_real_config(self) -> None:
        cmd_map = tcr.load_command_map(COMMAND_MAP)
        for cmd in SEARCH_COMMANDS + LIFECYCLE_COMMANDS:
            assert cmd in cmd_map, f"{cmd} must be in the command map"
            entry = cmd_map[cmd]
            assert "script" in entry, f"{cmd} entry must have a 'script' field"
            assert "kind" in entry, f"{cmd} entry must have a 'kind' field"

    def test_lifecycle_entries_carry_phase(self) -> None:
        cmd_map = tcr.load_command_map(COMMAND_MAP)
        for cmd in LIFECYCLE_COMMANDS:
            assert cmd_map[cmd].get("phase") == cmd, (
                f"{cmd} entry must carry phase='{cmd}'"
            )

    def test_returns_empty_dict_when_config_missing(self, tmp_path: Path) -> None:
        missing = tmp_path / "does-not-exist.json"
        assert tcr.load_command_map(missing) == {}

    def test_returns_empty_dict_when_config_unreadable(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text("{ this is not valid json")
        assert tcr.load_command_map(bad) == {}


# ---------------------------------------------------------------------------
# execute — invoke the backing script via an injectable runner
# ---------------------------------------------------------------------------

class TestExecute:
    """execute(route) runs the target script via a runner callable; tests inject a stub."""

    def test_calls_runner_with_route_argv(self) -> None:
        route = tcr.build_route("wiki", "mqtt broker", limit=5)
        calls_seen: list[list[str]] = []

        def fake_runner(argv: list[str]) -> str:
            calls_seen.append(argv)
            return "1\twiki/entities/iot/mqtt-protocol.md\tMQTT\t…"

        out = tcr.execute(route, runner=fake_runner)
        assert len(calls_seen) == 1
        assert calls_seen[0] == route["argv"]
        assert "MQTT" in out

    def test_returns_runner_output_verbatim_on_success(self) -> None:
        route = tcr.build_route("review", "task")

        def fake_runner(argv: list[str]) -> str:
            return "## CRITICAL (1)\n- [code-reviewer] bug"

        out = tcr.execute(route, runner=fake_runner)
        assert out == "## CRITICAL (1)\n- [code-reviewer] bug"

    def test_unknown_command_route_returns_error_marker(self) -> None:
        # build_route raises on unknown command; execute is given a route that
        # already resolved. The "unknown" path is exercised by main(), not here.
        # But if a caller hands execute an empty route, it must fail soft.
        empty_route = {"argv": [], "command": "", "target_script": "", "kind": "unknown"}

        def should_not_be_called(argv: list[str]) -> str:
            raise AssertionError("runner must not be called for an empty/unknown route")

        out = tcr.execute(empty_route, runner=should_not_be_called)
        assert "error" in out.lower() or "unknown" in out.lower(), (
            "empty route must return an error string, not crash"
        )

    def test_nonzero_exit_returns_error_string_not_exception(self) -> None:
        # Mirror persona-orchestrator's fail-soft contract: a failing target
        # script surfaces as a formatted error, never raises.
        route = tcr.build_route("wiki", "query")

        def failing_runner(argv: list[str]) -> str:
            # Simulate what _default_runner returns on subprocess nonzero exit.
            return "[error: exited 2] FTS5 query error: malformed"

        out = tcr.execute(route, runner=failing_runner)
        assert out.startswith("[error:")
        assert "2" in out
