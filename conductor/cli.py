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

    if args.cmd == "plan":
        from .plan import plan_objective
        wos = plan_objective(args.objective, REPO_ROOT, write=args.write)
        _emit({"schema": "awiki-conductor/v1",
               "work_orders": wos}, args.json)
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
