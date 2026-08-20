#!/usr/bin/env python3
"""awiki memory promote — five-gate L2→L3 promotion (Phase 5).

Manual-with-evidence, DRY-RUN FIRST. The promoted candidate IS the verified
L2 source entry's stored summary (R-P5-001) — there is no free-form text
argument. --apply writes exactly one reviewable candidate under
wiki/promotion-candidates/ — never Git refs/remotes.

  python scripts/memory/promote.py <project-root> --source-ts 1755... \
      --evidence commit_sha=10507cee            # dry-run (default)
  python scripts/memory/promote.py <project> --source-ts ... --evidence ... --apply
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import promotion as promo


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Five-gate memory promotion (dry-run first)")
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--source-ts", type=float, required=True,
                        help="ts of the L2 source entry — its stored summary is the candidate")
    parser.add_argument("--evidence", required=True,
                        help="type=value e.g. commit_sha=10507cee / experiment_id=EXP-1")
    parser.add_argument("--data-root", type=Path, default=None)
    parser.add_argument("--apply", action="store_true",
                        help="write the candidate file (still never touches Git)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    etype, _, evalue = args.evidence.partition("=")
    result = promo.promote(
        project_root=args.project_root.resolve(),
        provenance={"type": etype, "value": evalue},
        source_layer="L2",
        source_entry_ts=args.source_ts,
        dry_run=not args.apply,
        data_root=args.data_root,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    else:
        for g in result["gates"]:
            mark = "PASS" if g["passed"] else "FAIL"
            print(f"[{mark}] {g['gate']}: {g['detail']}")
        print(f"ok={result['ok']} written={result.get('written', False)} "
              f"candidate={result.get('candidate_path', '-')}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
