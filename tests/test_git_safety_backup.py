"""Tests for scripts/hooks/git_safety_backup.py — Git Safety Net (Z1).

Iron Law #1: failing tests written FIRST.

Z1 ป้องกัน commit หายจาก git pull --rebase:
- backup_head() — snapshot HEAD ก่อน rebase
- find_lost_commits() — หา dangling commits ที่หายไป
- recover_lost_commits() — cherry-pick กลับ
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "hooks"))

import git_safety_backup as gsb  # noqa: E402  -- module under test (created by Z1)


def _run_git(args: list[str], cwd: Path) -> str:
    """Run git command, return stdout."""
    r = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"git {args} failed: {r.stderr}")
    return r.stdout.strip()


def _make_repo(tmp_path: Path) -> Path:
    """Create a temp git repo with 1 initial commit. Returns repo path."""
    repo = tmp_path / "test-repo"
    repo.mkdir()
    _run_git(["init", "-b", "main"], repo)
    _run_git(["config", "user.email", "test@test.com"], repo)
    _run_git(["config", "user.name", "Test"], repo)
    (repo / "file1.txt").write_text("initial")
    _run_git(["add", "."], repo)
    _run_git(["commit", "-m", "initial"], repo)
    return repo


# ---------------------------------------------------------------------------
# 1. backup_head — writes HEAD hash to backup file
# ---------------------------------------------------------------------------
def test_backup_head_writes_commit_hash(tmp_path):
    repo = _make_repo(tmp_path)
    backup_file = tmp_path / "backup.jsonl"
    gsb.backup_head(repo, backup_file=backup_file)
    assert backup_file.is_file()
    entries = [json.loads(l) for l in backup_file.read_text().splitlines() if l.strip()]
    assert len(entries) == 1
    head = _run_git(["rev-parse", "HEAD"], repo)
    assert entries[0]["head"] == head
    assert "ts" in entries[0]


# ---------------------------------------------------------------------------
# 2. backup_head — multiple calls append (not overwrite)
# ---------------------------------------------------------------------------
def test_backup_head_appends(tmp_path):
    repo = _make_repo(tmp_path)
    backup_file = tmp_path / "backup.jsonl"
    gsb.backup_head(repo, backup_file=backup_file)
    # make another commit
    (repo / "file2.txt").write_text("second")
    _run_git(["add", "."], repo)
    _run_git(["commit", "-m", "second"], repo)
    gsb.backup_head(repo, backup_file=backup_file)
    entries = [json.loads(l) for l in backup_file.read_text().splitlines() if l.strip()]
    assert len(entries) == 2
    assert entries[0]["head"] != entries[1]["head"]


# ---------------------------------------------------------------------------
# 3. backup_head — caps at 50 entries (FIFO)
# ---------------------------------------------------------------------------
def test_backup_head_caps_at_50(tmp_path):
    repo = _make_repo(tmp_path)
    backup_file = tmp_path / "backup.jsonl"
    for i in range(55):
        (repo / f"f{i}.txt").write_text(str(i))
        _run_git(["add", "."], repo)
        _run_git(["commit", "-m", f"c{i}"], repo)
        gsb.backup_head(repo, backup_file=backup_file)
    entries = [json.loads(l) for l in backup_file.read_text().splitlines() if l.strip()]
    assert len(entries) <= 50


# ---------------------------------------------------------------------------
# 4. find_lost_commits — detects dropped commits after rebase
# ---------------------------------------------------------------------------
def test_find_lost_commits_detects_dropped(tmp_path):
    """Simulate: commit A → backup → reset to before A → find_lost should find A."""
    repo = _make_repo(tmp_path)
    # commit A (our work)
    (repo / "work.txt").write_text("important work")
    _run_git(["add", "."], repo)
    _run_git(["commit", "-m", "important work"], repo)
    commit_a = _run_git(["rev-parse", "HEAD"], repo)
    # backup before "rebase"
    backup_file = tmp_path / "backup.jsonl"
    gsb.backup_head(repo, backup_file=backup_file)
    # simulate rebase dropping A: reset to initial commit
    initial = _run_git(["rev-list", "--max-parents=0", "HEAD"], repo)
    _run_git(["reset", "--hard", initial], repo)
    # now find_lost should detect commit_a as lost
    lost = gsb.find_lost_commits(repo, backup_file=backup_file)
    assert len(lost) >= 1
    assert any(commit_a.startswith(l[:7]) or l.startswith(commit_a[:7]) for l in lost)


# ---------------------------------------------------------------------------
# 5. find_lost_commits — returns empty when nothing lost
# ---------------------------------------------------------------------------
def test_find_lost_commits_empty_when_nothing_lost(tmp_path):
    repo = _make_repo(tmp_path)
    backup_file = tmp_path / "backup.jsonl"
    gsb.backup_head(repo, backup_file=backup_file)
    # no rebase, no reset — HEAD still matches backup
    lost = gsb.find_lost_commits(repo, backup_file=backup_file)
    assert lost == []


# ---------------------------------------------------------------------------
# 6. find_lost_commits — missing backup file → empty
# ---------------------------------------------------------------------------
def test_find_lost_commits_missing_backup_file(tmp_path):
    repo = _make_repo(tmp_path)
    lost = gsb.find_lost_commits(repo, backup_file=tmp_path / "nonexistent.jsonl")
    assert lost == []


# ---------------------------------------------------------------------------
# 7. recover_lost_commits — cherry-picks back
# ---------------------------------------------------------------------------
def test_recover_lost_commits_restores_files(tmp_path):
    """commit with new file → lost → recover → file restored."""
    repo = _make_repo(tmp_path)
    (repo / "precious.txt").write_text("don't lose me")
    _run_git(["add", "."], repo)
    _run_git(["commit", "-m", "precious"], repo)
    precious_commit = _run_git(["rev-parse", "HEAD"], repo)
    backup_file = tmp_path / "backup.jsonl"
    gsb.backup_head(repo, backup_file=backup_file)
    # simulate loss
    initial = _run_git(["rev-list", "--max-parents=0", "HEAD"], repo)
    _run_git(["reset", "--hard", initial], repo)
    assert not (repo / "precious.txt").exists()
    # recover
    recovered = gsb.recover_lost_commits(repo, backup_file=backup_file)
    assert len(recovered) >= 1
    assert (repo / "precious.txt").exists()
    assert (repo / "precious.txt").read_text() == "don't lose me"


# ---------------------------------------------------------------------------
# 8. is_rebase_command — detects git pull --rebase / git rebase
# ---------------------------------------------------------------------------
def test_is_rebase_command_detects_pull_rebase():
    assert gsb.is_rebase_command("git pull --rebase origin main") is True
    assert gsb.is_rebase_command("git pull --rebase") is True
    assert gsb.is_rebase_command("git rebase main") is True
    assert gsb.is_rebase_command("git rebase --abort") is True


def test_is_rebase_command_ignores_normal_commands():
    assert gsb.is_rebase_command("git pull origin main") is False  # no --rebase
    assert gsb.is_rebase_command("git commit -m test") is False
    assert gsb.is_rebase_command("git push") is False
    assert gsb.is_rebase_command("git status") is False


# ---------------------------------------------------------------------------
# 9. has_unpushed_commits — detects local-only commits
# ---------------------------------------------------------------------------
def test_has_unpushed_commits_detects_local(tmp_path):
    repo = _make_repo(tmp_path)
    # no remote → all commits are "unpushed"
    n = gsb.count_unpushed_commits(repo)
    assert n >= 1  # at least the initial commit


# ===========================================================================
# Z3 — check_git_rebase_safety.py (PreToolUse hook integration)
# ===========================================================================
# Z3 คือ PreToolUse hook บน Bash. มันต้อง:
#   (a) จับ git pull --rebase / git rebase ได้
#   (b) auto-backup HEAD (safety net)
#   (c) ไม่ block (exit 0 — warn only)
#   (d) ลงทะเบียนใน .claude/settings.json (ไม่งั้นไม่อัตโนมัติ)
#
# Tests ด้านล่างยืนยันทั้ง 4 ข้อ — โดยเฉพาะ (d) ป้องกัน regression
# ที่ "สร้างไฟล์ hook แต่ลืมเสียบ settings.json" (เหตุการณ์ Z3 ค้าง 2026-07-16)
# ===========================================================================

def _make_hook_input(command: str) -> str:
    """Build PreToolUse Bash input JSON like Claude Code sends to hooks."""
    return json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": command},
    })


def test_z3_hook_registered_in_settings():
    """Z3 MUST be registered in .claude/settings.json PreToolUse → Bash matcher.

    This is the test that caught the original gap: the hook file existed but
    was never wired into settings.json, so it never ran. Iron Law #1 RED.
    """
    settings_path = REPO_ROOT / ".claude" / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    pretooluse = settings.get("hooks", {}).get("PreToolUse", [])
    bash_hooks = []
    for group in pretooluse:
        if group.get("matcher") == "Bash":
            for h in group.get("hooks", []):
                bash_hooks.append(h.get("command", ""))
    # Z3 hook must be among the registered Bash PreToolUse hooks
    joined = " ".join(bash_hooks)
    assert "check-git-rebase-safety" in joined or "check_git_rebase_safety" in joined, (
        "Z3 hook (check-git-rebase-safety) is NOT registered in "
        ".claude/settings.json PreToolUse → Bash. It exists as a file but "
        "will never run. Wire it in."
    )


def test_z3_hook_does_not_block_pull_rebase(tmp_path, monkeypatch, capsys):
    """Z3 must NEVER block — only warn + backup. Exit code must be 0."""
    repo = _make_repo(tmp_path)
    monkeypatch.setattr(gsb, "REPO_ROOT", repo)
    monkeypatch.setattr(gsb, "BACKUP_FILE", tmp_path / "backup.jsonl")
    # import the hook module fresh
    import importlib
    import check_git_rebase_safety as z3hook
    importlib.reload(z3hook)
    monkeypatch.setattr(z3hook, "REPO_ROOT", repo, raising=False)
    # feed input via stdin
    monkeypatch.setattr("sys.stdin", _StdinStub(_make_hook_input("git pull --rebase origin main")))
    exit_code = z3hook.main()
    assert exit_code == 0, "Z3 must not block (warn-only)"


def test_z3_hook_no_backup_for_normal_git(tmp_path, monkeypatch):
    """Z3 must NOT fire for non-rebase git commands (no backup pollution)."""
    repo = _make_repo(tmp_path)
    backup_file = tmp_path / "backup.jsonl"
    monkeypatch.setattr(gsb, "REPO_ROOT", repo)
    monkeypatch.setattr(gsb, "BACKUP_FILE", backup_file)
    import importlib
    import check_git_rebase_safety as z3hook
    importlib.reload(z3hook)
    monkeypatch.setattr(z3hook, "REPO_ROOT", repo, raising=False)
    monkeypatch.setattr("sys.stdin", _StdinStub(_make_hook_input("git status")))
    z3hook.main()
    # no backup should have been written for a normal git command
    assert not backup_file.is_file(), "Z3 should not backup for non-rebase commands"


class _StdinStub:
    """Minimal stdin stub that simulates sys.stdin for hooks reading JSON."""
    def __init__(self, payload: str):
        self._payload = payload

    def read(self):
        return self._payload
