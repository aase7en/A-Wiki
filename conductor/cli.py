"""awiki conductor — CLI router (status / gate / plan)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _emit(data: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
        return
    for k, v in data.items():
        print(f"{k:12}: {v}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="conductor", description="A-Wiki Conductor v0.1.0")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_status = sub.add_parser("status", help="unified read-only status")
    p_status.add_argument("--json", action="store_true")

    p_gate = sub.add_parser("gate", help="entry-gate GO/NO-GO verdict")
    p_gate.add_argument("--topic", required=True)
    p_gate.add_argument("--agent", default="unknown")
    p_gate.add_argument("--json", action="store_true")

    p_verify = sub.add_parser("verify", help="run repo gates bounded → JSON")
    p_verify.add_argument("--gates", default="registry",
                          help="comma list: registry,scan,health")
    p_verify.add_argument("--json", action="store_true")

    p_recall = sub.add_parser("recall", help="search L1 memory ledger (read-only)")
    p_recall.add_argument("--query", required=True)
    p_recall.add_argument("--limit", type=int, default=10)
    p_recall.add_argument("--json", action="store_true")

    p_claim = sub.add_parser("claim", help="append a COLLAB claim row (gate-guarded)")
    p_claim.add_argument("--topic", required=True)
    p_claim.add_argument("--agent", required=True)
    p_claim.add_argument("--scope", default="<scope>")
    p_claim.add_argument("--branch", default="<branch>")
    p_claim.add_argument("--json", action="store_true")

    p_search = sub.add_parser("search", help="wiki knowledge search (fts|hybrid)")
    p_search.add_argument("--query", required=True)
    p_search.add_argument("--mode", default="hybrid", choices=("fts", "hybrid"))
    p_search.add_argument("--limit", type=int, default=8)
    p_search.add_argument("--json", action="store_true")

    p_related = sub.add_parser("related", help="graph neighbors of a wiki page")
    p_related.add_argument("--page", required=True)
    p_related.add_argument("--type", default=None, help="edge type filter")
    p_related.add_argument("--json", action="store_true")

    p_hubs = sub.add_parser("hubs", help="top hub pages by graph degree")
    p_hubs.add_argument("--domain", default=None)
    p_hubs.add_argument("--limit", type=int, default=10)
    p_hubs.add_argument("--json", action="store_true")

    p_models = sub.add_parser("models", help="model policy + runtime slots (read-only)")
    p_models.add_argument("--json", action="store_true")

    p_plan = sub.add_parser("plan", help="objective → work orders")
    p_plan.add_argument("objective")
    p_plan.add_argument("--write", action="store_true",
                        help="write WO files under docs/work-orders/")
    p_plan.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)

    if args.cmd == "status":
        from .state import conductor_status
        _emit(conductor_status(REPO_ROOT), args.json)
        return 0

    if args.cmd == "gate":
        from .gate import entry_gate
        v = entry_gate(REPO_ROOT, topic=args.topic, agent=args.agent)
        _emit(v, args.json)
        return 0 if v["verdict"] == "GO" else 1

    if args.cmd == "verify":
        from .bridge import run_verify
        out = run_verify(REPO_ROOT, gates=[g.strip() for g in args.gates.split(",") if g.strip()])
        _emit(out, args.json)
        return 0 if out["all_passed"] else 1

    if args.cmd == "recall":
        from .bridge import recall
        _emit({"schema": "awiki-conductor/v1",
               "hits": recall(args.query, limit=args.limit)}, args.json)
        return 0

    if args.cmd == "claim":
        from .bridge import add_claim, ClaimConflict
        try:
            out = add_claim(REPO_ROOT, topic=args.topic, agent=args.agent,
                            scope=args.scope, branch=args.branch)
        except ClaimConflict as e:
            _emit({"claimed": False, "reason": str(e)}, args.json)
            return 1
        _emit(out, args.json)
        return 0

    if args.cmd == "search":
        from .bridge import search_wiki
        _emit(search_wiki(args.query, mode=args.mode, limit=args.limit), args.json)
        return 0

    if args.cmd == "related":
        from .bridge import related_pages
        _emit(related_pages(args.page, edge_type=args.type), args.json)
        return 0

    if args.cmd == "hubs":
        from .bridge import graph_hubs
        _emit(graph_hubs(limit=args.limit, domain=args.domain), args.json)
        return 0

    if args.cmd == "models":
        import sys as _sys
        _sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))
        from model_policy import PolicyError, policy_summary
        try:
            _emit(policy_summary(), args.json)
        except PolicyError as e:
            # Read-only button must degrade with a clean verdict, never a
            # traceback (e.g. pyyaml missing on a fresh machine).
            _emit({"schema": "awiki-conductor/v1", "models_unavailable": True,
                   "reason": str(e)}, args.json)
            return 1
        return 0

    if args.cmd == "plan":
        from .plan import plan_objective
        wos = plan_objective(args.objective, REPO_ROOT, write=args.write)
        _emit({"schema": "awiki-conductor/v1",
               "work_orders": wos}, args.json)
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
