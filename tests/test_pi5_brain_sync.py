"""
Tests for scripts/hermes/pi5-brain-sync.py — container-side brain sync for Pi5.

Root cause being fixed (docs/architecture/hermes-cross-agent-handoff.md +
2026-07-10 static audit of scripts/hermes/auto-sync-from-git.sh):

1. The 6h cron path could NEVER deliver updates into the container: it looked
   for ``scripts/hermes/hermes-export-*.tar.gz`` in the repo, but ``.gitignore``
   excludes ``*.tar.gz`` — so ``git pull`` never brings a package and the sync
   exits at "No package." every run. The canonical brain clone
   ``/opt/data/A-Wiki`` was only ever updated by hand (C3', Chunk E Phase 3).
2. If a tarball HAD appeared, line 52 would clobber ``terminal.cwd`` with a
   host path (``/home/umbrel/A-Wiki``) that does not exist inside the
   container, detaching Hermes from the brain.
3. ``sudo -S -p ''`` with cron's empty stdin fails silently (sudo on the Pi5
   is passwordful — verified 2026-07-02); the new plan uses ``sudo -n`` so a
   missing sudoers rule fails fast and loud.

This module replaces the tarball flow with a direct fast-forward of the
canonical clone inside the container, reusing the conflict-resolution recipe
proven in C3'.1 and Chunk E Phase 3 (stash → ff-only → pop, auto-gen conflicts
restored from HEAD, anything else aborts leaving the stash intact).

Tests cover the PURE logic only: no subprocess, no docker, no git (Iron Law #1
— failing-first, CI-safe). Mirrors the import + stub-runner pattern of
tests/test_telegram_command_router.py.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# scripts/hermes/ has no __init__.py (not an importable package); load the
# file by absolute path via importlib so the test is hermetic.
import importlib.util as _ilu  # noqa: E402

_MOD_PATH = REPO_ROOT / "scripts" / "hermes" / "pi5-brain-sync.py"
_spec = _ilu.spec_from_file_location("pi5_brain_sync", _MOD_PATH)
assert _spec is not None and _spec.loader is not None, f"cannot load {_MOD_PATH}"
pbs = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(pbs)  # type: ignore[union-attr]

CONTAINER = "hermes-agent_web_1"
CLONE_DIR = "/opt/data/A-Wiki"


# ---------------------------------------------------------------------------
# classify_conflict — which stash-pop conflicts are safe to auto-resolve
# ---------------------------------------------------------------------------

class TestClassifyConflict:
    """Only machine-regenerated files may be auto-resolved from HEAD.

    The auto-gen set is exactly what C3' and Phase 3 hit in practice:
    wiki/context/*, .wiki-graph.json, brain-map.canvas, per-subdir CLAUDE.md.
    Everything else must be treated as a manual conflict (fail-soft abort).
    """

    def test_wiki_context_is_autogen(self) -> None:
        assert pbs.classify_conflict("wiki/context/wiki-overview.md") == "autogen"

    def test_wiki_graph_json_is_autogen(self) -> None:
        assert pbs.classify_conflict(".wiki-graph.json") == "autogen"

    def test_brain_map_canvas_is_autogen(self) -> None:
        assert pbs.classify_conflict("brain-map.canvas") == "autogen"

    def test_subdir_claude_md_is_autogen(self) -> None:
        assert pbs.classify_conflict("wiki/concepts/iot/CLAUDE.md") == "autogen"

    def test_root_claude_md_is_MANUAL(self) -> None:
        # Iron Law #5: root CLAUDE.md is lock-protected — never auto-resolve.
        assert pbs.classify_conflict("CLAUDE.md") == "manual"

    def test_ordinary_wiki_page_is_manual(self) -> None:
        assert pbs.classify_conflict("wiki/entities/env/aeration-tank.md") == "manual"

    def test_script_is_manual(self) -> None:
        assert pbs.classify_conflict("scripts/hermes/persona-orchestrator.py") == "manual"

    def test_device_only_investment_script_is_manual(self) -> None:
        # The known device-only tree from C3' — must never be clobbered.
        assert pbs.classify_conflict("scripts/investment/f_score.py") == "manual"


# ---------------------------------------------------------------------------
# build_container_sync_script — the bash run INSIDE the container
# ---------------------------------------------------------------------------

class TestBuildContainerSyncScript:
    """The generated script must encode the C3'-proven recipe, and must NOT
    contain any trace of the broken tarball / cwd-clobber flow."""

    def setup_method(self) -> None:
        self.script = pbs.build_container_sync_script(CLONE_DIR)

    def test_targets_the_canonical_clone(self) -> None:
        assert CLONE_DIR in self.script

    def test_fetches_origin_main(self) -> None:
        assert "git fetch origin main" in self.script

    def test_up_to_date_guard_short_circuits_with_exit_3(self) -> None:
        # Already-current clone must exit 3 (distinct from "synced" 0) so the
        # caller can skip the pointless gateway HUP — live run 2026-07-10
        # showed a no-op sync HUP-ing a stale pid and failing the rescan leg.
        assert "merge-base --is-ancestor" in self.script
        up_idx = self.script.index("UP-TO-DATE")
        assert "exit 3" in self.script[up_idx : up_idx + 120]

    def test_stashes_untracked_device_files(self) -> None:
        assert "stash push --include-untracked" in self.script

    def test_fast_forward_only_never_merge_commit(self) -> None:
        assert "--ff-only" in self.script

    def test_autogen_conflicts_restored_from_head(self) -> None:
        assert "git checkout HEAD --" in self.script

    def test_every_autogen_pattern_is_in_the_case_statement(self) -> None:
        for pattern in pbs.AUTOGEN_PATTERNS:
            assert pattern in self.script, f"missing auto-gen pattern: {pattern}"

    def test_manual_conflict_aborts_with_exit_2_and_keeps_stash(self) -> None:
        assert "MANUAL-CONFLICT" in self.script
        assert "exit 2" in self.script
        # The abort path must NOT drop the stash (device-only files live there).
        abort_idx = self.script.index("MANUAL-CONFLICT")
        assert "stash drop" not in self.script[abort_idx : abort_idx + 200]

    def test_no_tarball_flow(self) -> None:
        assert "tar.gz" not in self.script
        assert "profile import" not in self.script

    def test_no_cwd_clobber(self) -> None:
        assert "terminal.cwd" not in self.script
        assert "config set" not in self.script


# ---------------------------------------------------------------------------
# build_docker_exec_argv — how the host invokes the container
# ---------------------------------------------------------------------------

class TestBuildDockerExecArgv:
    def test_uses_sudo_non_interactive(self) -> None:
        argv = pbs.build_docker_exec_argv(CONTAINER, "echo hi")
        # sudo -n = fail fast in cron instead of hanging/silently failing on
        # the passwordful sudo (the old script's `sudo -S -p ''` bug).
        assert argv[:2] == ["sudo", "-n"]

    def test_runs_as_hermes_user_by_default(self) -> None:
        argv = pbs.build_docker_exec_argv(CONTAINER, "echo hi")
        i = argv.index("--user")
        assert argv[i + 1] == "hermes"  # preserve uid-1000 file ownership

    def test_container_and_script_are_passed_through(self) -> None:
        argv = pbs.build_docker_exec_argv(CONTAINER, "echo marker-xyz")
        assert CONTAINER in argv
        assert argv[-1] == "echo marker-xyz"
        assert "bash" in argv


# ---------------------------------------------------------------------------
# build_rescan_argv — SIGHUP the gateway so new skill content is scanned
# ---------------------------------------------------------------------------

class TestBuildRescanArgv:
    def test_sends_hup_to_gateway_pid(self) -> None:
        argv = pbs.build_rescan_argv(CONTAINER)
        joined = " ".join(argv)
        assert "HUP" in joined
        assert "gateway.pid" in joined

    def test_extracts_numeric_pid_from_json_pidfile(self) -> None:
        # Phase 3 discovery: /opt/data/gateway.pid contains JSON, not a bare
        # int — a plain `kill -HUP $(cat ...)` breaks. The command must
        # extract digits.
        joined = " ".join(pbs.build_rescan_argv(CONTAINER))
        assert "grep -o" in joined or "tr -cd" in joined

    def test_rescan_is_fail_soft_on_stale_pid(self) -> None:
        # Live 2026-07-10: s6 respawns the gateway after HUP but gateway.pid
        # can lag, so `kill` may hit a dead pid. Rescan is best-effort — a
        # failed HUP must warn and exit 0, never fail the sync run.
        joined = " ".join(pbs.build_rescan_argv(CONTAINER))
        assert "if kill -HUP" in joined  # kill guarded, not bare
        assert "stale" in joined or "next" in joined  # warning text
        assert "2>/dev/null" in joined  # kill error suppressed, message wins


# ---------------------------------------------------------------------------
# build_plan + execute — orchestration with an injectable runner
# ---------------------------------------------------------------------------

class TestPlanAndExecute:
    def test_plan_orders_sync_before_rescan(self) -> None:
        plan = pbs.build_plan(CONTAINER, CLONE_DIR)
        names = [step[0] for step in plan]
        assert names == ["container-sync", "gateway-rescan"]

    def test_execute_runs_rescan_after_clean_sync(self) -> None:
        calls: list[str] = []

        def runner(name: str, argv: list[str]) -> int:
            calls.append(name)
            return 0

        rc = pbs.execute(pbs.build_plan(CONTAINER, CLONE_DIR), runner)
        assert calls == ["container-sync", "gateway-rescan"]
        assert rc == 0

    def test_execute_still_rescans_after_manual_conflict_exit_2(self) -> None:
        # exit 2 = FF landed but stash-pop hit a manual conflict; the tree IS
        # updated, so the gateway should still rescan. Overall rc stays 2 so
        # cron logs show the conflict.
        calls: list[str] = []

        def runner(name: str, argv: list[str]) -> int:
            calls.append(name)
            return 2 if name == "container-sync" else 0

        rc = pbs.execute(pbs.build_plan(CONTAINER, CLONE_DIR), runner)
        assert "gateway-rescan" in calls
        assert rc == 2

    def test_execute_skips_rescan_when_ff_failed(self) -> None:
        # exit 1 = nothing changed in the clone; rescan is pointless noise.
        calls: list[str] = []

        def runner(name: str, argv: list[str]) -> int:
            calls.append(name)
            return 1 if name == "container-sync" else 0

        rc = pbs.execute(pbs.build_plan(CONTAINER, CLONE_DIR), runner)
        assert calls == ["container-sync"]
        assert rc == 1

    def test_execute_skips_rescan_when_up_to_date_and_reports_success(self) -> None:
        # exit 3 = UP-TO-DATE: nothing changed → no HUP, and the overall run
        # is a SUCCESS (0) — cron must not log a no-op as an error.
        calls: list[str] = []

        def runner(name: str, argv: list[str]) -> int:
            calls.append(name)
            return 3 if name == "container-sync" else 0

        rc = pbs.execute(pbs.build_plan(CONTAINER, CLONE_DIR), runner)
        assert calls == ["container-sync"]
        assert rc == 0


# ---------------------------------------------------------------------------
# CLI — dry-run by default (CI-safe), --apply to execute
# ---------------------------------------------------------------------------

class TestCLI:
    def test_dry_run_is_default_and_runs_nothing(self, capsys) -> None:
        executed: list[str] = []
        rc = pbs.main([], runner=lambda name, argv: executed.append(name) or 0)
        assert rc == 0
        assert executed == []
        out = capsys.readouterr().out
        assert "container-sync" in out  # plan is printed for review

    def test_apply_executes_the_plan(self) -> None:
        executed: list[str] = []
        rc = pbs.main(
            ["--apply"], runner=lambda name, argv: executed.append(name) or 0
        )
        assert rc == 0
        assert executed == ["container-sync", "gateway-rescan"]

    def test_container_and_clone_dir_are_overridable(self, capsys) -> None:
        rc = pbs.main(["--container", "my-c", "--clone-dir", "/opt/data/X"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "my-c" in out
        assert "/opt/data/X" in out
