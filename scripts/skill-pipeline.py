#!/usr/bin/env python3
"""skill-pipeline CLI — Slice B (thin wrapper over scripts/lib/skill_pipeline).

  python scripts/skill-pipeline.py list
  python scripts/skill-pipeline.py eval <id>
  python scripts/skill-pipeline.py approve <id>       # THE one button
  python scripts/skill-pipeline.py scout "gap one" "gap two"
  python scripts/skill-pipeline.py propose-from-page wiki/concepts/x.md

Queue: .tmp/skill-proposals/ (durable, reviewable, nothing auto-applies).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))
import skill_pipeline as pipe  # noqa: E402

QUEUE = REPO_ROOT / ".tmp" / "skill-proposals"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="A-Wiki skill pipeline")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    p_eval = sub.add_parser("eval"); p_eval.add_argument("id")
    p_app = sub.add_parser("approve"); p_app.add_argument("id")
    p_scout = sub.add_parser("scout")
    p_scout.add_argument("gaps", nargs="+")
    p_prop = sub.add_parser("propose-from-page"); p_prop.add_argument("page")
    args = ap.parse_args(argv)

    if args.cmd == "list":
        rows = pipe.list_proposals(QUEUE)
        if not rows:
            print("(no proposals — queue is empty)")
        for r in rows:
            mark = {"ready": "✅", "draft": "📝", "failed": "❌",
                    "approved": "🎉"}.get(r["status"], "?")
            print(f"{mark} {r['id']:34} {r['status']:9} {r['source']:9} "
                  f"{(r.get('description') or '')[:60]}")
        return 0
    if args.cmd == "eval":
        ev = pipe.run_eval(args.id, QUEUE, REPO_ROOT,
                           REPO_ROOT / ".tmp" / "skill-eval")
        print("PASS" if ev["passed"] else "FAIL")
        return 0 if ev["passed"] else 1
    if args.cmd == "approve":
        return pipe.approve(args.id, QUEUE)
    if args.cmd == "scout":
        created = pipe.scout_gaps(args.gaps, QUEUE,
                                   REPO_ROOT / "skills-registry.json")
        for p in created:
            print(f"queued: {p['id']} <- {p.get('url', p.get('page', ''))}")
        if not created:
            print("(nothing new — gaps covered or no finds)")
        return 0
    if args.cmd == "propose-from-page":
        prop = pipe.propose_from_page(args.page, QUEUE)
        print(f"queued: {prop['id']} (draft) — next: eval {prop['id']}")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
