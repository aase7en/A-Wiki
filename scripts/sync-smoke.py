#!/usr/bin/env python3
"""Non-destructive smoke test for A-Wiki sync logic using temporary repos."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

import sync  # noqa: E402


def git(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=check)


def init_repo(path: Path) -> None:
    path.mkdir(parents=True)
    git(["init", "-b", "main"], path)
    git(["config", "user.email", "agent@a-wiki.local"], path)
    git(["config", "user.name", "A-Wiki Agent"], path)
    (path / "README.md").write_text("# Sync Smoke\n", encoding="utf-8")
    git(["add", "README.md"], path)
    git(["commit", "-m", "init"], path)


def main() -> int:
    original_cwd = Path.cwd()
    tmp = Path(tempfile.mkdtemp(prefix="awiki-sync-smoke-"))
    try:
        remote = tmp / "remote.git"
        repo = tmp / "repo"
        git(["init", "--bare", str(remote)], tmp)
        init_repo(repo)
        git(["remote", "add", "origin", str(remote)], repo)
        git(["push", "--set-upstream", "origin", "main"], repo)

        (repo / "wiki").mkdir()
        (repo / "wiki" / "smoke.md").write_text("# Smoke\n", encoding="utf-8")
        os.chdir(repo)
        ok = sync.sync_now("sync-smoke")
        if not ok:
            print("FAIL: sync_now returned false", file=sys.stderr)
            return 1
        status, _, _ = sync.run_cmd(["git", "status", "--short"])
        if status.strip():
            print(f"FAIL: temp repo still dirty: {status}", file=sys.stderr)
            return 1
        print("OK — sync smoke committed and pushed a temp wiki change")
        return 0
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())

