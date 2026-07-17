#!/usr/bin/env python3
"""
git_safety_backup.py — Git Safety Net (Z1): กัน commit หายจาก pull --rebase.

ปัญหา: `git pull --rebase` (รันอัตโนมัติใน session_start.py) ทิ้ง commits
ของ session อื่นออกจาก history. ต้องไล่ reflog หา dangling commits เอง.

แก้: 3 ชั้นป้องกัน
  1. backup_head() — snapshot HEAD ก่อน rebase → .tmp/git-head-backup.jsonl
  2. find_lost_commits() — เทียบ HEAD ปัจจุบันกับ backup → หา dangling
  3. recover_lost_commits() — cherry-pick กลับ

CLI:
  python scripts/hooks/git_safety_backup.py --backup    # snapshot HEAD
  python scripts/hooks/git_safety_backup.py --check     # หา lost commits
  python scripts/hooks/git_safety_backup.py --recover   # cherry-pick กลับ
  python scripts/hooks/git_safety_backup.py --status    # สรุป

Backup file: .tmp/git-head-backup.jsonl (gitignored, local-only, caps 50).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKUP_FILE = REPO_ROOT / ".tmp" / "git-head-backup.jsonl"
MAX_ENTRIES = 50


def _git(args: list[str], repo_root: Path | str = REPO_ROOT) -> str:
    """Run git command, return stdout (stripped). Raises on failure."""
    r = subprocess.run(
        ["git"] + args, cwd=str(repo_root), capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    if r.returncode != 0:
        raise RuntimeError(f"git {args[:2]} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def backup_head(
    repo_root: Path | str = REPO_ROOT,
    backup_file: Path | str = BACKUP_FILE,
) -> str | None:
    """Snapshot current HEAD commit hash to backup file.

    Appends to JSONL (1 line per backup). Caps at MAX_ENTRIES (FIFO).
    Returns the HEAD hash, or None if git fails.
    """
    try:
        head = _git(["rev-parse", "HEAD"], repo_root)
    except Exception:
        return None
    bfile = Path(backup_file)
    bfile.parent.mkdir(parents=True, exist_ok=True)
    entry = {"ts": round(time.time(), 3), "head": head}
    # Read existing entries, append, cap
    existing: list[str] = []
    if bfile.is_file():
        existing = [l for l in bfile.read_text(encoding="utf-8").splitlines() if l.strip()]
    existing.append(json.dumps(entry))
    # FIFO cap
    if len(existing) > MAX_ENTRIES:
        existing = existing[-MAX_ENTRIES:]
    bfile.write_text("\n".join(existing) + "\n", encoding="utf-8")
    return head


def _load_backups(backup_file: Path | str = BACKUP_FILE) -> list[dict]:
    """Load backup entries from JSONL. Returns list of {ts, head}."""
    bfile = Path(backup_file)
    if not bfile.is_file():
        return []
    out = []
    for line in bfile.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def find_lost_commits(
    repo_root: Path | str = REPO_ROOT,
    backup_file: Path | str = BACKUP_FILE,
) -> list[str]:
    """Find ALL commits dropped by rebase/reset — not just the backup HEAD.

    Bug fixed 2026-07-17: previously this returned only the backup HEAD hash
    itself. When a session made N unpushed commits and rebase dropped all N,
    only the last one was recovered — earlier commits' files stayed lost.
    Now for each backup HEAD that is not reachable from current HEAD, we
    enumerate ALL commits in that backup HEAD's history that are NOT on the
    current HEAD (``git rev-list <backup_head> --not HEAD``). This returns
    every dropped commit, oldest-first, so recover_lost_commits() can
    cherry-pick them in order.

    Returns list of commit hashes (oldest-first within each backup; backups
    checked newest-first so the most recent loss wins on duplicates).
    """
    backups = _load_backups(backup_file)
    if not backups:
        return []
    try:
        # Get all commits reachable from current HEAD
        reachable = set(
            _git(["rev-list", "HEAD"], repo_root).splitlines()
        )
    except Exception:
        return []

    lost: list[str] = []
    seen_backup_heads: set[str] = set()
    # Check backups newest-first (most recent loss is most relevant)
    for entry in reversed(backups):
        head = entry.get("head", "")
        if not head or head in seen_backup_heads:
            continue
        seen_backup_heads.add(head)
        if head in reachable:
            continue  # this backup is still on HEAD — no loss from it
        # Verify the backup HEAD still exists in git objects (dangling)
        try:
            _git(["cat-file", "-t", head], repo_root)
        except Exception:
            continue  # commit garbage-collected, skip
        # Enumerate ALL commits in this backup HEAD not reachable from
        # current HEAD. --not HEAD = exclude commits reachable from HEAD.
        # Order: oldest-first (so cherry-pick applies them in order).
        try:
            dropped = _git(
                ["rev-list", "--reverse", head, "--not", "HEAD"],
                repo_root,
            ).splitlines()
        except Exception:
            # rev-list failed (e.g. HEAD unborn) — fall back to just the head
            dropped = [head]
        for c in dropped:
            if c and c not in reachable and c not in lost:
                lost.append(c)
    return lost


def recover_lost_commits(
    repo_root: Path | str = REPO_ROOT,
    backup_file: Path | str = BACKUP_FILE,
) -> list[str]:
    """Cherry-pick all lost commits back onto current HEAD.

    Returns list of successfully recovered commit hashes.
    """
    lost = find_lost_commits(repo_root, backup_file)
    recovered = []
    for commit in lost:
        try:
            r = subprocess.run(
                ["git", "cherry-pick", "--allow-empty", commit],
                cwd=str(repo_root), capture_output=True, text=True,
                encoding="utf-8", errors="replace",
            )
            if r.returncode == 0:
                recovered.append(commit)
            else:
                # cherry-pick conflict — abort this one, continue
                subprocess.run(["git", "cherry-pick", "--abort"],
                               cwd=str(repo_root), capture_output=True)
                sys.stderr.write(f"⚠️ cherry-pick {commit[:8]} conflicted — skipped\n")
        except Exception as e:
            sys.stderr.write(f"⚠️ recover {commit[:8]} failed: {e}\n")
    return recovered


def is_rebase_command(command: str) -> bool:
    """True if command is `git pull --rebase` or `git rebase`."""
    if not command:
        return False
    c = command.strip().lower()
    if "git pull" in c and "--rebase" in c:
        return True
    if re.search(r"\bgit rebase\b", c):
        return True
    return False


def count_unpushed_commits(
    repo_root: Path | str = REPO_ROOT,
    remote: str = "origin",
    branch: str = "main",
) -> int:
    """Count commits on local branch that haven't been pushed to remote."""
    try:
        ref = f"{remote}/{branch}"
        # Check if remote ref exists
        _git(["rev-parse", ref], repo_root)
    except Exception:
        # No remote ref → all commits are "unpushed"
        try:
            return len(_git(["rev-list", "HEAD", "--count"], repo_root).splitlines())
        except Exception:
            return 0
    try:
        out = _git(["rev-list", f"{ref}..HEAD", "--count"], repo_root)
        return int(out.strip()) if out.strip().isdigit() else 0
    except Exception:
        return 0


def status_report(repo_root: Path | str = REPO_ROOT,
                  backup_file: Path | str = BACKUP_FILE) -> dict:
    """Summary: backup count, lost commits, unpushed count."""
    backups = _load_backups(backup_file)
    lost = find_lost_commits(repo_root, backup_file)
    unpushed = count_unpushed_commits(repo_root)
    return {
        "backup_count": len(backups),
        "last_backup_ts": backups[-1]["ts"] if backups else None,
        "lost_commit_count": len(lost),
        "lost_commits": lost,
        "unpushed_commits": unpushed,
    }


def main() -> int:
    import argparse
    # Regression guard (2026-07-17): hooks_runner.py:get_hooks() runs ALL *.py
    # in scripts/hooks/ when no specific hook is passed. This file lives in
    # that dir (library + CLI). When invoked blind (no flag args), argparse's
    # required-group error would exit 2 — which broke:
    #   test_hooks_runner_own_writes_survive_cp874
    #   TestHooksRunnerCLI::test_all_hooks_run_successfully
    # Detect the "called as a generic hook" case (no flags + stdin is a hook
    # payload, not a TTY) and no-op. This keeps it safe to import as a module.
    if not any(a.startswith("--") for a in sys.argv[1:]):
        # No flag args. If stdin is not a TTY, hooks_runner is calling us blind.
        if not sys.stdin.isatty():
            return 0  # no-op — this is a library, not a standalone hook
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1].strip())
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--backup", action="store_true", help="snapshot HEAD now")
    g.add_argument("--check", action="store_true", help="find lost commits")
    g.add_argument("--recover", action="store_true", help="cherry-pick lost commits back")
    g.add_argument("--status", action="store_true", help="summary report")
    args = p.parse_args()

    if args.backup:
        head = backup_head()
        print(f"✓ Backed up HEAD: {head[:12] if head else '(failed)'}")
        return 0 if head else 1

    if args.check:
        lost = find_lost_commits()
        if not lost:
            print("✓ No lost commits — all backups reachable from HEAD.")
        else:
            print(f"⚠️ Found {len(lost)} lost commit(s):")
            for c in lost:
                try:
                    msg = _git(["log", "-1", "--format=%s", c])
                except Exception:
                    msg = "(unable to read message)"
                print(f"  {c[:12]} {msg}")
            print("\nRecover: python scripts/hooks/git_safety_backup.py --recover")
        return 0

    if args.recover:
        lost = find_lost_commits()
        if not lost:
            print("✓ No lost commits to recover.")
            return 0
        print(f"Recovering {len(lost)} commit(s)...")
        recovered = recover_lost_commits()
        print(f"✓ Recovered {len(recovered)}/{len(lost)} commit(s).")
        return 0

    if args.status:
        s = status_report()
        print(f"Git Safety Net Status:")
        print(f"  Backups: {s['backup_count']}")
        print(f"  Lost commits: {s['lost_commit_count']}")
        print(f"  Unpushed commits: {s['unpushed_commits']}")
        if s["lost_commits"]:
            print(f"  ⚠️ Recover: python scripts/hooks/git_safety_backup.py --recover")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
