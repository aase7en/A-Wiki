"""awiki_cli — thin launcher packaged for pip ("pip install awiki").

The brain itself lives in the A-Wiki repo (clone it once). This package
just guarantees the `awiki` command exists everywhere and dispatches to
the repo's conductor CLI with the right interpreter, so users get:

    awiki search "esp32 lora"   |  awiki status  |  awiki plan "<objective>"

Root resolution: AWIKI_ROOT env → walk up from cwd for the repo markers.
No repo found → actionable error (exit 2), never a traceback.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_MARKERS = ("AGENTS.md", "skills-registry.json")


def find_repo_root() -> Path:
    env = os.environ.get("AWIKI_ROOT", "").strip()
    if env:
        p = Path(env).resolve()
        if all((p / m).exists() for m in _MARKERS):
            return p
        sys.stderr.write(f"AWIKI_ROOT={env} is not an A-Wiki repo "
                         f"(missing {_MARKERS})\n")
        raise SystemExit(2)
    cur = Path.cwd().resolve()
    for candidate in (cur, *cur.parents):
        if all((candidate / m).exists() for m in _MARKERS):
            return candidate
    sys.stderr.write(
        "awiki: no A-Wiki repo found (looked for AGENTS.md + "
        "skills-registry.json upward from cwd).\n"
        "Fix: run inside your A-Wiki clone, or:\n"
        "  git clone https://github.com/aase7en/A-Wiki.git\n"
        "  cd A-Wiki && bash scripts/setup-local.sh\n"
        "  export AWIKI_ROOT=$PWD\n")
    raise SystemExit(2)


def build_command(args: list[str]) -> list[str]:
    # `awiki adopt <repo>` runs the brain's adopt installer (does NOT need
    # cwd to be a repo — it may be run from anywhere)
    if args and args[0] == "adopt":
        root = find_repo_root()
        return [sys.executable,
                str(root / "scripts" / "awiki-adopt.py"), *args[1:]]
    if args and args[0] == "skill":
        root = find_repo_root()
        return [sys.executable,
                str(root / "scripts" / "skill-pipeline.py"), *args[1:]]
    root = find_repo_root()
    return [sys.executable, "-m", "conductor", *args]


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    cmd = build_command(args)
    return subprocess.run(cmd, cwd=str(find_repo_root())).returncode


if __name__ == "__main__":
    raise SystemExit(main())
