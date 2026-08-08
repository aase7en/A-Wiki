#!/usr/bin/env python3
"""
check_history_divergence.py — SessionStart guard against post-rewrite divergence.

ROOT CAUSE (2026-07-11 incident):
  History was rewritten via `git filter-repo` + force push. Every device was
  reset to the new history EXCEPT the Mac (offline at the time). When the Mac
  came back online, `git pull --rebase` would either:
    (a) merge the OLD pre-rewrite history back in → pollutes the repo, OR
    (b) create a chaotic divergence that's hard to recover from.

  The recovery recipe — `git fetch origin && git reset --hard origin/main` —
  was only documented in session-memory.md (fragile: relies on a human
  remembering). This hook automates the detection.

DETECTION LOGIC:
  After `git fetch origin main` (done by session_start.py's git_pull step),
  compare HEAD vs origin/main:
    - SAFE: HEAD is an ancestor of origin/main (just behind, fast-forward OK)
    - SAFE: origin/main is an ancestor of HEAD (just ahead, normal local work)
    - SAFE: HEAD == origin/main (in sync)
    - DIVERGED: neither is an ancestor of the other → TRUE divergence.
      This is the signature of a history rewrite (or a very unusual fork).
  Criticality escalates if the merge-base is older than STALE_DAYS (default 30):
    a stale merge-base + divergence = almost certainly a rewrite, not a normal
    feature-branch split.

ACTION:
  Emit a CRITICAL warning to stderr (injected into the session context). Does
  NOT block (no exit(2)) — the user may have a legitimate reason to be on a
  divergent history (e.g. mid-rebase, experimentation). The warning tells them
  exactly what to do if it's the rewrite case.

CLI (for testing / manual check):
  python scripts/hooks/check_history_divergence.py            # check + warn
  python scripts/hooks/check_history_divergence.py --quiet    # check, exit code only
  python scripts/hooks/check_history_divergence.py --json     # machine-readable

Exit codes: 0 = safe or just-behind/ahead; 1 = diverged (warning emitted).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
# A-Wiki uses `main`; some legacy forks may still be on `master`. Try main
# first, fall back to master so the guard works on either convention.
PRIMARY_REF = "origin/main"
FALLBACK_REF = "origin/master"
STALE_DAYS = 30  # merge-base older than this + divergence = CRITICAL


def _resolve_remote_ref(repo_root: Path | str) -> str | None:
    """Return whichever remote-tracking ref exists (main preferred)."""
    for ref in (PRIMARY_REF, FALLBACK_REF):
        rc, _ = _git(["rev-parse", "--verify", ref], repo_root)
        if rc == 0:
            return ref
    return None


def _git(args: list[str], repo_root: Path | str = REPO_ROOT) -> tuple[int, str]:
    """Run git, return (returncode, stdout+stderr stripped). Never raises."""
    try:
        r = subprocess.run(
            ["git"] + args, cwd=str(repo_root),
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            timeout=15,
        )
        return r.returncode, (r.stdout + r.stderr).strip()
    except Exception as e:
        return 99, str(e)


def _is_ancestor(a: str, b: str, repo_root: Path | str = REPO_ROOT) -> bool:
    """True if commit `a` is an ancestor of commit `b`."""
    rc, _ = _git(["merge-base", "--is-ancestor", a, b], repo_root)
    return rc == 0


def _commit_date(commit: str, repo_root: Path | str = REPO_ROOT) -> int | None:
    """Unix timestamp of `commit`, or None if unavailable."""
    rc, out = _git(["show", "-s", "--format=%ct", commit], repo_root)
    if rc == 0 and out:
        try:
            return int(out.strip())
        except ValueError:
            return None
    return None


def _rev_count(commit: str, repo_root: Path | str = REPO_ROOT) -> int:
    """Number of commits reachable from `commit`."""
    rc, out = _git(["rev-list", "--count", commit], repo_root)
    if rc == 0 and out:
        try:
            return int(out.strip())
        except ValueError:
            return 0
    return 0


def check(repo_root: Path | str = REPO_ROOT) -> dict:
    """Check divergence between HEAD and origin/main (or origin/master).

    Returns a dict with keys: status, head, origin, remote_ref, merge_base,
    diverged, head_only_count, origin_only_count, merge_base_age_days,
    critical, message.

    status is one of: "in_sync", "behind", "ahead", "diverged",
    "no_remote", "error".
    """
    result = {
        "status": "error", "head": None, "origin": None, "remote_ref": None,
        "merge_base": None, "diverged": False, "head_only_count": 0,
        "origin_only_count": 0, "merge_base_age_days": None,
        "critical": False, "message": "",
    }

    # Resolve HEAD.
    rc, head = _git(["rev-parse", "HEAD"], repo_root)
    if rc != 0:
        result["message"] = f"cannot resolve HEAD: {head}"
        return result
    result["head"] = head

    # Resolve remote-tracking ref (must have been fetched already by git_pull).
    remote_ref = _resolve_remote_ref(repo_root)
    if remote_ref is None:
        result["status"] = "no_remote"
        result["message"] = (
            "no origin/main or origin/master available "
            "(run `git fetch origin` first)"
        )
        return result
    result["remote_ref"] = remote_ref

    rc, origin = _git(["rev-parse", remote_ref], repo_root)
    if rc != 0:
        result["status"] = "no_remote"
        result["message"] = f"{remote_ref} not available (run `git fetch origin` first)"
        return result
    result["origin"] = origin

    # In sync?
    if head == origin:
        result["status"] = "in_sync"
        result["message"] = "HEAD == origin/main (in sync)"
        return result

    # Ancestor checks.
    head_ancestor_of_origin = _is_ancestor(head, origin, repo_root)
    origin_ancestor_of_head = _is_ancestor(origin, head, repo_root)

    if head_ancestor_of_origin and not origin_ancestor_of_head:
        result["status"] = "behind"
        result["message"] = "HEAD is behind origin/main (fast-forward will work)"
        return result
    if origin_ancestor_of_head and not head_ancestor_of_origin:
        result["status"] = "ahead"
        result["message"] = "HEAD is ahead of origin/main (normal local commits)"
        return result
    if head_ancestor_of_origin and origin_ancestor_of_head:
        # Same commit reachable both ways — treat as in_sync (shouldn't happen
        # since head != origin checked above, but be defensive).
        result["status"] = "in_sync"
        return result

    # Neither is an ancestor → TRUE divergence.
    result["diverged"] = True
    result["status"] = "diverged"

    # Merge-base + counts.
    rc, mb = _git(["merge-base", head, origin], repo_root)
    if rc == 0 and mb:
        result["merge_base"] = mb
        mb_date = _commit_date(mb, repo_root)
        if mb_date:
            import time
            age_s = int(time.time()) - mb_date
            result["merge_base_age_days"] = age_s // 86400
        head_only = _rev_count(f"{mb}..{head}", repo_root)
        origin_only = _rev_count(f"{mb}..{origin}", repo_root)
        result["head_only_count"] = head_only
        result["origin_only_count"] = origin_only

    # Criticality: divergence + stale merge-base = almost certainly a rewrite.
    age = result.get("merge_base_age_days")
    if age is not None and age >= STALE_DAYS:
        result["critical"] = True
        result["message"] = (
            f"🚨 HISTORY DIVERGENCE DETECTED (likely rewrite). HEAD and "
            f"{remote_ref} share no recent common ancestor "
            f"(merge-base is {age} days old; HEAD has {result['head_only_count']} "
            f"commit(s) origin lacks; origin has {result['origin_only_count']} "
            f"HEAD lacks).\n"
            f"   → If this is the post-rewrite recovery case (e.g. Mac after "
            f"2026-07-11 filter-repo), run:\n"
            f"       git fetch origin && git reset --hard origin/main\n"
            f"   → (DO NOT `git pull` — it will merge the old history back in "
            f"and pollute the repo. Reset --hard is the only safe path.)\n"
            f"   → Backup of pre-rewrite history: "
            f"drive/backups/pre-rewrite-20260711-5dafd58.bundle"
        )
    else:
        result["message"] = (
            f"⚠️ HEAD and {remote_ref} have diverged "
            f"(merge-base age: {age} days; HEAD+{result['head_only_count']} "
            f"origin+{result['origin_only_count']}). "
            f"If unexpected, investigate before pulling."
        )

    return result


def emit_warning(result: dict) -> None:
    """Write the warning to stderr (injected into session context)."""
    if result.get("diverged"):
        sys.stderr.write(result["message"] + "\n")


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    p.add_argument("--quiet", action="store_true", help="no stderr output; exit code only")
    p.add_argument("--json", action="store_true", help="machine-readable JSON output")
    args = p.parse_args()

    result = check()

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif not args.quiet:
        emit_warning(result)

    sys.exit(1 if result.get("diverged") else 0)


if __name__ == "__main__":
    main()
