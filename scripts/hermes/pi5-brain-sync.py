#!/usr/bin/env python3
"""
pi5-brain-sync.py — Fast-forward the canonical A-Wiki clone INSIDE the Hermes
container on the Pi5, then SIGHUP the gateway so updated skills are rescanned.

Replaces the tarball leg of auto-sync-from-git.sh, which could never work:
the flow imported ``scripts/hermes/hermes-export-*.tar.gz`` from the repo, but
``.gitignore`` excludes ``*.tar.gz`` — no package ever arrives via git pull,
so the container brain (``/opt/data/A-Wiki``) was only ever updated by hand
(C3' 2026-07-02, Chunk E Phase 3 2026-07-07). See
docs/architecture/hermes-cross-agent-handoff.md §"LIVE PI5 REALITY".

Conflict handling reuses the recipe both manual deploys converged on:
stash (incl. untracked device-only files) → ff-only merge → stash pop;
auto-generated files that conflict are restored from HEAD (gen-index.py
regenerates them anyway); ANY other conflict aborts with exit 2, leaving the
stash intact for a human — this script must never destroy device-only work
like scripts/investment/.

sudo notes: the Pi5's sudo is passwordful and cron has no stdin, so every
docker command uses ``sudo -n`` — it fails fast and loud instead of hanging.
One-time setup on the Pi5 (as an admin):

    echo 'umbrel ALL=(root) NOPASSWD: /usr/bin/docker exec *' \
        | sudo tee /etc/sudoers.d/awiki-hermes-sync

Usage:
    python3 scripts/hermes/pi5-brain-sync.py              # dry-run (default)
    python3 scripts/hermes/pi5-brain-sync.py --apply      # execute
    python3 scripts/hermes/pi5-brain-sync.py --container hermes-agent_web_1 \
        --clone-dir /opt/data/A-Wiki --apply

Exit codes: 0 = synced or already up-to-date · 1 = fast-forward impossible
(diverged clone; nothing changed) · 2 = FF landed but a manual conflict is
parked in the stash (gateway still rescanned — tree IS updated).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from typing import Callable, List, Tuple

DEFAULT_CONTAINER = "hermes-agent_web_1"
DEFAULT_CLONE_DIR = "/opt/data/A-Wiki"
GATEWAY_PID_FILE = "/opt/data/gateway.pid"

# Machine-regenerated files that are safe to restore from HEAD when they
# conflict on stash pop — exactly the set C3' and Phase 3 hit in practice.
# Root CLAUDE.md is intentionally absent (Iron Law #5: lock-protected).
AUTOGEN_PATTERNS = [
    "wiki/context/*",
    ".wiki-graph.json",
    "brain-map.canvas",
    "*/CLAUDE.md",
]

Runner = Callable[[str, List[str]], int]
Plan = List[Tuple[str, List[str]]]


def classify_conflict(path: str) -> str:
    """Return "autogen" for machine-regenerated paths, else "manual"."""
    import fnmatch

    for pattern in AUTOGEN_PATTERNS:
        if fnmatch.fnmatch(path, pattern):
            return "autogen"
    return "manual"


def build_container_sync_script(clone_dir: str) -> str:
    """Bash executed inside the container (as the hermes user).

    Kept as one generated string so the pure logic — guards, patterns, exit
    codes — is unit-testable without docker. The case-statement patterns are
    derived from AUTOGEN_PATTERNS so bash and Python can never disagree.
    """
    case_patterns = "|".join(AUTOGEN_PATTERNS)
    return f"""set -e
cd {clone_dir}
git fetch origin main
if git merge-base --is-ancestor origin/main HEAD; then
  echo "UP-TO-DATE: HEAD already contains origin/main"
  exit 0
fi
STASHED=0
if ! git diff --quiet || ! git diff --cached --quiet || [ -n "$(git status --porcelain)" ]; then
  git stash push --include-untracked -m awiki-pi5-brain-sync
  STASHED=1
fi
if ! git merge --ff-only origin/main; then
  echo "FF-FAILED: clone has diverged from origin/main — manual fix needed"
  [ "$STASHED" = "1" ] && git stash pop || true
  exit 1
fi
if [ "$STASHED" = "1" ]; then
  if ! git stash pop; then
    MANUAL=0
    for f in $(git diff --name-only --diff-filter=U); do
      case "$f" in
        {case_patterns})
          git checkout HEAD -- "$f"
          git add "$f"
          echo "AUTOGEN-RESOLVED: $f (restored from HEAD; gen-index.py regenerates it)"
          ;;
        *)
          echo "MANUAL-CONFLICT: $f — left in the stash for a human"
          MANUAL=1
          ;;
      esac
    done
    if [ "$MANUAL" = "1" ]; then
      echo "recover with: cd {clone_dir} && git status && git stash pop"
      exit 2
    fi
    git stash drop
  fi
fi
echo "SYNCED: $(git log --oneline -1)"
"""


def build_docker_exec_argv(
    container: str, script: str, user: str = "hermes"
) -> List[str]:
    # sudo -n: the Pi5's sudo is passwordful; in cron this fails immediately
    # with a clear error instead of the old `sudo -S -p ''` silent hang.
    # --user hermes preserves uid-1000 ownership of everything git touches.
    return [
        "sudo", "-n",
        "docker", "exec", "--user", user,
        container,
        "bash", "-lc", script,
    ]


def build_rescan_argv(container: str) -> List[str]:
    # The gateway only rescans /opt/data/skills on SIGHUP or restart.
    # gateway.pid contains JSON (Phase 3 discovery), not a bare int — extract
    # the first digit-run instead of `cat`-ing the whole file into kill.
    script = (
        f'PID=$(grep -o "[0-9]\\+" {GATEWAY_PID_FILE} 2>/dev/null | head -1); '
        f'if [ -n "$PID" ]; then kill -HUP "$PID" && echo "HUP sent to $PID"; '
        f'else echo "no gateway.pid — skills load on next container restart"; fi'
    )
    return build_docker_exec_argv(container, script)


def build_plan(container: str, clone_dir: str) -> Plan:
    return [
        ("container-sync", build_docker_exec_argv(
            container, build_container_sync_script(clone_dir))),
        ("gateway-rescan", build_rescan_argv(container)),
    ]


def execute(plan: Plan, runner: Runner) -> int:
    """Run the plan. Rescan is skipped only when the sync changed nothing
    (rc 1); a manual-conflict sync (rc 2) DID update the tree, so the gateway
    still rescans and the overall rc stays 2 for cron logs."""
    overall = 0
    for name, argv in plan:
        if name == "gateway-rescan" and overall == 1:
            print("[skip] gateway-rescan — clone unchanged")
            continue
        rc = runner(name, argv)
        print(f"[{name}] exit {rc}")
        if rc != 0 and overall == 0:
            overall = rc
    return overall


def _subprocess_runner(name: str, argv: List[str]) -> int:
    return subprocess.run(argv).returncode


def main(argv: List[str] | None = None, runner: Runner = _subprocess_runner) -> int:
    parser = argparse.ArgumentParser(
        description="FF the A-Wiki clone inside the Hermes container + rescan")
    parser.add_argument("--apply", action="store_true",
                        help="execute (default: dry-run prints the plan)")
    parser.add_argument("--container", default=DEFAULT_CONTAINER)
    parser.add_argument("--clone-dir", default=DEFAULT_CLONE_DIR)
    args = parser.parse_args(argv)

    plan = build_plan(args.container, args.clone_dir)

    if not args.apply:
        print("DRY-RUN — nothing executed. Plan:")
        for name, cmd in plan:
            print(f"\n== {name} ==")
            print(" ".join(cmd[:8]) + (" …" if len(cmd) > 8 else ""))
            if name == "container-sync":
                print("--- inner script ---")
                print(cmd[-1])
        return 0

    return execute(plan, runner)


if __name__ == "__main__":
    sys.exit(main())
