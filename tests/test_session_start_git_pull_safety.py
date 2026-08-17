"""Tests for scripts/hooks/session_start.py::git_pull — DISC-001 safety guards.

Iron Law #1: failing tests written FIRST (A-Wiki vNext Phase 1 / P1.1).

Incident DISC-001 (2026-08-17): SessionStart ran `git pull --rebase origin main`
on ANY branch — a concurrent session on a migration branch had its history
rewritten by an external session and 3 uncommitted generated-surface edits
were lost. These tests pin the guard contract:

  G1  only the `main` branch may be synced — never any other branch
  G2  a dirty tracked working tree blocks sync (untracked files are fine)
  G3  sync is fast-forward only — `--rebase` must never appear again
  G4  ff-failure (diverged local main) warns and leaves the repo untouched
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SESSION_START = REPO_ROOT / "scripts" / "hooks" / "session_start.py"

spec = importlib.util.spec_from_file_location("session_start_gpull_mod", SESSION_START)
assert spec and spec.loader
session_start = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = session_start
spec.loader.exec_module(session_start)


class _Proc:
    def __init__(self, rc=0, out="", err=""):
        self.returncode = rc
        self.stdout = out
        self.stderr = err


class FakeGit:
    """Scripted subprocess.run: answers rev-parse / status / pull by subcommand."""

    def __init__(self, branch="main", porcelain="", pull_rc=0, pull_out="Already up to date."):
        self.branch = branch
        self.porcelain = porcelain
        self.pull_rc = pull_rc
        self.pull_out = pull_out
        self.calls: list[list[str]] = []

    def __call__(self, cmd, **kw):
        self.calls.append(list(cmd))
        sub = cmd[1] if len(cmd) > 1 else ""
        if sub == "rev-parse":
            return _Proc(0, self.branch)
        if sub == "status":
            return _Proc(0, self.porcelain)
        if sub == "pull":
            if self.pull_rc == 0:
                return _Proc(0, self.pull_out)
            return _Proc(self.pull_rc, "", "fatal: Not possible to fast-forward, aborting.")
        return _Proc(0, "")

    def flat(self) -> list[str]:
        return [" ".join(c) for c in self.calls]


@pytest.fixture
def fake_git(monkeypatch):
    def _make(**kw):
        fg = FakeGit(**kw)
        monkeypatch.setattr(session_start.subprocess, "run", fg)
        return fg

    return _make


# ---------------------------------------------------------------------------
# G1 — branch guard
# ---------------------------------------------------------------------------
class TestG1BranchGuard:
    def test_non_main_branch_is_never_pulled(self, fake_git, capsys):
        fg = fake_git(branch="refactor/awiki-kernel-vnext-clean")
        session_start.git_pull(REPO_ROOT)
        assert not any(" pull" in f" {c}" or c.startswith("git pull") for c in fg.flat())
        assert "refactor/awiki-kernel-vnext-clean" in capsys.readouterr().err

    def test_detached_head_is_never_pulled(self, fake_git):
        fg = fake_git(branch="HEAD")
        session_start.git_pull(REPO_ROOT)
        assert not any("pull" in c for c in fg.flat())

    def test_main_branch_proceeds_to_sync(self, fake_git):
        fg = fake_git(branch="main")
        session_start.git_pull(REPO_ROOT)
        assert any("pull" in c for c in fg.flat())


# ---------------------------------------------------------------------------
# G2 — dirty working tree guard
# ---------------------------------------------------------------------------
class TestG2DirtyTreeGuard:
    def test_unstaged_change_blocks_pull(self, fake_git, capsys):
        fg = fake_git(porcelain=" M scripts/foo.py")
        session_start.git_pull(REPO_ROOT)
        assert not any("pull" in c for c in fg.flat())
        assert "skip" in capsys.readouterr().err.lower()

    def test_staged_change_blocks_pull(self, fake_git):
        fg = fake_git(porcelain="M  scripts/foo.py")
        session_start.git_pull(REPO_ROOT)
        assert not any("pull" in c for c in fg.flat())

    def test_untracked_only_tree_still_pulls(self, fake_git):
        fg = fake_git(porcelain="?? scratch/notes.md")
        session_start.git_pull(REPO_ROOT)
        assert any("pull" in c for c in fg.flat())


# ---------------------------------------------------------------------------
# G3 — fast-forward only
# ---------------------------------------------------------------------------
class TestG3FFOnly:
    def test_pull_uses_ff_only(self, fake_git):
        fg = fake_git()
        session_start.git_pull(REPO_ROOT)
        pulls = [c for c in fg.flat() if "pull" in c]
        assert pulls, "git_pull never issued a pull on a clean main branch"
        assert all("--ff-only" in c for c in pulls)

    def test_rebase_never_appears_in_any_command(self, fake_git):
        fg = fake_git()
        session_start.git_pull(REPO_ROOT)
        assert not any("--rebase" in c for c in fg.flat())


# ---------------------------------------------------------------------------
# G4 — ff failure + robustness
# ---------------------------------------------------------------------------
class TestG4FFFailureAndRobustness:
    def test_diverged_main_warns_without_recovery_or_reset(self, fake_git, capsys):
        fg = fake_git(pull_rc=128)
        session_start.git_pull(REPO_ROOT)  # must not raise
        flat = fg.flat()
        assert not any(k in c for c in flat for k in ("rebase", "reset", "merge"))
        err = capsys.readouterr().err.lower()
        assert "fast-forward" in err or "failed" in err

    def test_success_after_real_update_prints_sync_message(self, fake_git, capsys):
        fg = fake_git(pull_out="Fast-forward 3 files changed")
        session_start.git_pull(REPO_ROOT)
        assert any("pull" in c for c in fg.flat())
        assert "synced" in capsys.readouterr().err.lower()

    def test_timeout_on_guard_query_does_not_raise(self, monkeypatch):
        def boom(cmd, **kw):
            raise subprocess.TimeoutExpired(cmd, 30)

        monkeypatch.setattr(session_start.subprocess, "run", boom)
        session_start.git_pull(REPO_ROOT)  # must not raise
