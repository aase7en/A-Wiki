#!/usr/bin/env python3
"""Check or sync the Sunday Invest Moon roadmap mirror in the product repo."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CANONICAL = REPO_ROOT / "wiki" / "synthesis" / "sunday-invest-moon-roadmap.md"


def default_mirror() -> Path:
    """Find the local product roadmap mirror without hardcoding a private repo name."""
    env_root = os.environ.get("PWQ_ROOT")
    if env_root:
        return Path(env_root).expanduser() / "ROADMAP.md"

    for candidate in sorted(REPO_ROOT.parent.glob("*/pixel-wealth-quest/ROADMAP.md")):
        if candidate.is_file():
            return candidate

    return REPO_ROOT.parent / "pixel-wealth-quest" / "ROADMAP.md"


def roadmaps_match(canonical: Path, mirror: Path) -> bool:
    return canonical.is_file() and mirror.is_file() and canonical.read_bytes() == mirror.read_bytes()


def sync_roadmap(canonical: Path, mirror: Path) -> None:
    if not canonical.is_file():
        raise FileNotFoundError(f"canonical roadmap not found: {canonical}")
    mirror.parent.mkdir(parents=True, exist_ok=True)
    mirror.write_bytes(canonical.read_bytes())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check or sync A-Wiki's canonical Sunday Invest Moon roadmap to the product repo."
    )
    parser.add_argument("--canonical", type=Path, default=DEFAULT_CANONICAL)
    parser.add_argument(
        "--mirror",
        type=Path,
        default=None,
        help="Mirror ROADMAP.md path. Defaults to PWQ_ROOT/ROADMAP.md or an auto-discovered sibling product repo.",
    )
    parser.add_argument("--sync", action="store_true", help="Overwrite the mirror with the canonical roadmap.")
    args = parser.parse_args(argv)

    canonical = args.canonical.expanduser().resolve()
    mirror = (args.mirror or default_mirror()).expanduser().resolve()

    try:
        if args.sync:
            sync_roadmap(canonical, mirror)
            print(f"SYNCED: {canonical} -> {mirror}")
            return 0
        if roadmaps_match(canonical, mirror):
            print(f"MATCH: {canonical} == {mirror}")
            return 0
        print(f"DRIFT: {canonical} != {mirror}")
        return 2
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
