"""
Tests for scripts/hermes/persona-orchestrator.py — the sequential persona fan-out.

Hermes has NO native subagent / parallel fan-out. This orchestrator realizes
"fan-out" as a sequence of ``hermes chat -q --persona <name>`` calls, then
merges the outputs into one triaged report. Tests cover the PURE logic only:
no subprocess, no real Hermes call (Iron Law #1 — failing-first, CI-safe).

Mirrors the import pattern of tests/test_render_kilo_config.py: add the
script's dir to sys.path and import directly (scripts/hermes/ has no
__init__.py, so it is not an importable package).
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

_PO_PATH = REPO_ROOT / "scripts" / "hermes" / "persona-orchestrator.py"
_spec = _ilu.spec_from_file_location("persona_orchestrator", _PO_PATH)
assert _spec is not None and _spec.loader is not None, f"cannot load {_PO_PATH}"
po = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(po)  # type: ignore[union-attr]

LIFECYCLE_CONFIG = REPO_ROOT / "scripts" / "hermes" / "lifecycle-config.json"
DEFAULT_PERSONAS = ["code-reviewer", "test-engineer", "security-auditor"]


# ---------------------------------------------------------------------------
# build_plan — pure plan construction (the heart of the unit test)
# ---------------------------------------------------------------------------

class TestBuildPlan:
    """build_plan(personas, task, sleep_s) builds argv lists WITHOUT running anything."""

    def test_three_personas_yields_three_calls(self) -> None:
        plan = po.build_plan(DEFAULT_PERSONAS, "review this PR", sleep_s=4)
        assert len(plan["calls"]) == 3
        names = [c["persona"] for c in plan["calls"]]
        assert names == DEFAULT_PERSONAS

    def test_each_call_argv_shape(self) -> None:
        plan = po.build_plan(["code-reviewer"], "fix the bug", sleep_s=4)
        call = plan["calls"][0]
        assert call["argv"] == [
            "hermes", "chat", "-q",
            "--persona", "code-reviewer",
            "fix the bug",
        ], "argv must match the documented hermes chat -q --persona <name> contract"

    def test_sleep_placed_between_calls_not_after_last(self) -> None:
        plan = po.build_plan(DEFAULT_PERSONAS, "task", sleep_s=5)
        sleeps = plan["sleeps"]
        # n personas → n-1 sleeps (no sleep after the final call).
        assert len(sleeps) == 2, "3 personas should yield 2 inter-call sleeps"
        assert all(s == 5 for s in sleeps), "each sleep must equal sleep_s"

    def test_single_persona_has_no_sleep(self) -> None:
        plan = po.build_plan(["code-reviewer"], "task", sleep_s=4)
        assert plan["sleeps"] == [], "one persona → no inter-call sleep"

    def test_empty_personas_yields_empty_plan(self) -> None:
        plan = po.build_plan([], "task", sleep_s=4)
        assert plan["calls"] == []
        assert plan["sleeps"] == []

    def test_task_arg_quoted_as_single_argv_element(self) -> None:
        # Task with spaces must be ONE argv element, not shell-split.
        plan = po.build_plan(["code-reviewer"], "review PR #42 carefully", sleep_s=4)
        assert plan["calls"][0]["argv"][-1] == "review PR #42 carefully"

    def test_plan_is_serializable_json(self) -> None:
        # --dry-run prints the plan as JSON; it must round-trip.
        plan = po.build_plan(DEFAULT_PERSONAS, "task", sleep_s=4)
        json.dumps(plan)  # raises if not serializable


# ---------------------------------------------------------------------------
# load_personas — read parallel_fan_out from lifecycle-config.json
# ---------------------------------------------------------------------------

class TestLoadPersonas:
    def test_loads_parallel_fan_out_from_config(self) -> None:
        personas = po.load_personas(LIFECYCLE_CONFIG)
        assert personas == DEFAULT_PERSONAS, (
            "must read the parallel_fan_out list from lifecycle-config.json"
        )

    def test_returns_empty_list_when_no_fan_out_key(self, tmp_path: Path) -> None:
        cfg = tmp_path / "cfg.json"
        cfg.write_text(json.dumps({"personas": {"available": ["x"]}}))
        assert po.load_personas(cfg) == []

    def test_returns_empty_list_when_fan_out_empty(self, tmp_path: Path) -> None:
        cfg = tmp_path / "cfg.json"
        cfg.write_text(json.dumps({"personas": {"parallel_fan_out": []}}))
        assert po.load_personas(cfg) == []


# ---------------------------------------------------------------------------
# run — orchestration with an injectable runner (no subprocess in tests)
# ---------------------------------------------------------------------------

class TestRun:
    """run() executes the plan via a runner callable; tests inject a stub."""

    def test_calls_runner_once_per_persona_in_order(self) -> None:
        plan = po.build_plan(DEFAULT_PERSONAS, "task", sleep_s=0)
        calls_seen: list[list[str]] = []

        def fake_runner(argv: list[str]) -> str:
            calls_seen.append(argv)
            # Echo the persona so we can verify ordering.
            return f"output from {argv[argv.index('--persona') + 1]}"

        report = po.run(plan, runner=fake_runner)
        assert len(calls_seen) == 3
        # Order preserved.
        seen_personas = [argv[argv.index("--persona") + 1] for argv in calls_seen]
        assert seen_personas == DEFAULT_PERSONAS

    def test_report_collects_per_persona_output(self) -> None:
        plan = po.build_plan(DEFAULT_PERSONAS, "task", sleep_s=0)

        def fake_runner(argv: list[str]) -> str:
            name = argv[argv.index("--persona") + 1]
            return f"{name}: no issues"

        report = po.run(plan, runner=fake_runner)
        assert "code-reviewer: no issues" in report["merged"]
        assert "test-engineer: no issues" in report["merged"]
        assert "security-auditor: no issues" in report["merged"]

    def test_empty_plan_returns_empty_report(self) -> None:
        plan = po.build_plan([], "task", sleep_s=0)

        def should_not_be_called(argv: list[str]) -> str:
            raise AssertionError("runner must not be called for empty plan")

        report = po.run(plan, runner=should_not_be_called)
        assert report["merged"] == ""
        assert report["persona_outputs"] == {}


# ---------------------------------------------------------------------------
# merge_report — triage by severity (mirrors the "triage" principle)
# ---------------------------------------------------------------------------

class TestMergeReport:
    """merge_report sorts findings by severity: critical > important > low."""

    def test_sorts_critical_before_important_before_low(self) -> None:
        outputs = {
            "security-auditor": "low: minor nit\nimportant: needs fix",
            "code-reviewer": "critical: SQL injection\nlow: typo",
            "test-engineer": "important: missing edge case",
        }
        merged = po.merge_report(outputs, severities=["critical", "important", "low"])
        crit_pos = merged.index("critical:")
        imp_pos = merged.index("important: needs fix")
        # Every critical line must come before every important line.
        assert crit_pos < imp_pos

    def test_unknown_severity_lines_go_last(self) -> None:
        outputs = {"code-reviewer": "informational: fyi\nlow: typo"}
        merged = po.merge_report(outputs, severities=["critical", "important", "low"])
        low_pos = merged.index("low:")
        info_pos = merged.index("informational:")
        assert low_pos < info_pos, "known-severity lines precede unclassified ones"

    def test_empty_outputs_yields_empty_string(self) -> None:
        assert po.merge_report({}, severities=["critical", "important"]) == ""
