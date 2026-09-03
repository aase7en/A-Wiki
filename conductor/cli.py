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

    p_review = sub.add_parser(
        "review", help="thin external-review bridge (ReviewBus WRAP)")
    rsub = p_review.add_subparsers(dest="review_cmd", required=True)
    r_open = rsub.add_parser("open", help="open an exact-head review cycle")
    r_open.add_argument("--task", required=True)
    r_open.add_argument("--tests", nargs="+", required=True,
                        help="required test commands")
    r_open.add_argument("--reviewer", default=None)
    r_open.add_argument("--json", action="store_true")
    r_ing = rsub.add_parser("ingest", help="ingest a durable reviewer result")
    r_ing.add_argument("--task", required=True)
    r_ing.add_argument("--file", required=True, help="path to result JSON")
    r_ing.add_argument("--json", action="store_true")
    r_st = rsub.add_parser("status", help="task readiness/status")
    r_st.add_argument("--task", required=True)
    r_st.add_argument("--json", action="store_true")
    r_rs = rsub.add_parser("resolve", help="resolve a finding with a fix sha")
    r_rs.add_argument("--task", required=True)
    r_rs.add_argument("--finding", required=True)
    r_rs.add_argument("--fix-sha", required=True)
    r_rs.add_argument("--json", action="store_true")
    r_vf = rsub.add_parser("verify-finding", help="verify an addressed finding")
    r_vf.add_argument("--task", required=True)
    r_vf.add_argument("--finding", required=True)
    r_vf.add_argument("--json", action="store_true")
    r_rt = rsub.add_parser("record-retest", help="record trusted retest evidence")
    r_rt.add_argument("--task", required=True)
    r_rt.add_argument("--ok", required=True, choices=("true", "false"))
    r_rt.add_argument("--sha", default=None,
                      help="retested sha (default: current HEAD)")
    r_rt.add_argument("--json", action="store_true")
    r_ci = rsub.add_parser("record-ci", help="record trusted CI evidence")
    r_ci.add_argument("--task", required=True)
    r_ci.add_argument("--ok", required=True, choices=("true", "false"))
    r_ci.add_argument("--json", action="store_true")

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

    if args.cmd == "review":
        from .review_bridge import MAX_RESULT_BYTES, ReviewBridge, ReviewBridgeError
        bridge = ReviewBridge(REPO_ROOT)
        ok = args.ok == "true" if hasattr(args, "ok") else None
        try:
            if args.review_cmd == "open":
                out = bridge.open(args.task, args.tests,
                                  reviewer=args.reviewer)
            elif args.review_cmd == "ingest":
                from pathlib import Path as _P
                path = _P(args.file)
                if not path.is_file():
                    raise ReviewBridgeError(f"result file not found: {args.file}")
                import json as _json
                try:
                    size = path.stat().st_size
                    if size > MAX_RESULT_BYTES:
                        raise ReviewBridgeError(
                            f"result file exceeds size bound ({MAX_RESULT_BYTES} bytes)")
                    payload = _json.loads(path.read_text(encoding="utf-8"))
                except ReviewBridgeError:
                    raise
                except (OSError, UnicodeError, _json.JSONDecodeError) as e:
                    raise ReviewBridgeError(
                        f"result file unreadable/invalid JSON: {e}") from None
                out = bridge.ingest(args.task, payload)
            elif args.review_cmd == "status":
                out = bridge.status(args.task)
            elif args.review_cmd == "resolve":
                out = bridge.resolve(args.task, args.finding,
                                     fix_sha=args.fix_sha)
            elif args.review_cmd == "verify-finding":
                out = bridge.verify_finding(args.task, args.finding)
            elif args.review_cmd == "record-retest":
                out = bridge.record_retest(args.task, ok=ok, sha=args.sha)
            elif args.review_cmd == "record-ci":
                out = bridge.record_ci(args.task, ok=ok)
            else:  # pragma: no cover — argparse required=True guards this
                return 2
        except ReviewBridgeError as e:
            _emit({"ok": False, "error": str(e)}, args.json)
            return 1
        out = {"ok": True, **out}
        _emit(out, args.json)
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
