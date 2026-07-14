#!/usr/bin/env python3
"""council.py — thin CLI wrapper around scripts/lib/council_room.py.

Brainstorm Council: fan a question out to K free/cheap models in parallel
via the existing scripts/swarm/delegate.sh, collect their answers into a
transcript, and let the MODERATOR (the primary agent, running in-session —
never this script) synthesize afterward with `synthesize`. This CLI does
the cheap orchestration only; it never calls a paid model itself and never
writes synthesis text on its own.

Usage:
  council.py ask "question" [--participants N] [--task-type T] [--timeout S]
  council.py synthesize <id> (--text "..." | --file path) [--author NAME]
  council.py show <id>
  council.py list

See docs/protocols/brainstorm-council.md for the full protocol.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import council_room as cr  # noqa: E402

# Same cp874/Thai-Windows safety pattern as council_room.py — this CLI
# prints engine answers verbatim, which may contain non-cp874 characters.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass


def _cmd_ask(args: argparse.Namespace) -> int:
    transcript = cr.convene(
        args.question,
        n=args.participants,
        task_type=args.task_type,
        timeout=args.timeout,
        list_secret_names=cr.default_list_secret_names,
    )

    ok_count = 0
    for p in transcript["participants"]:
        if p["status"] == "ok":
            ok_count += 1
        print(f"[{p['engine']}] {p['status']} ({p['latency_s']}s)")
        print(p["answer"])
        print("")

    if not transcript["participants"]:
        print("no participants available (no API keys configured / all disabled)", file=sys.stderr)

    path = cr.COUNCIL_DIR / f"{transcript['id']}.json"
    print(f"transcript: {path}")

    if ok_count > 0:
        print(
            "→ moderator: python scripts/swarm/council.py synthesize "
            f'{transcript["id"]} --text "..."'
        )
        return 0

    print("no participant produced an answer — nothing to synthesize", file=sys.stderr)
    return 1


def _cmd_synthesize(args: argparse.Namespace) -> int:
    text = args.text
    if args.file:
        try:
            text = Path(args.file).read_text(encoding="utf-8")
        except OSError as exc:
            print(f"error reading --file: {exc}", file=sys.stderr)
            return 1

    try:
        cr.add_synthesis(args.council_id, text, author=args.author)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"synthesis added to {args.council_id}")
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    try:
        transcript = cr.load_council(args.council_id)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"id: {transcript.get('id')}")
    print(f"question: {transcript.get('question')}")
    print(f"task_type: {transcript.get('task_type')}")
    print(f"created_at: {transcript.get('created_at')}")
    print(f"status: {transcript.get('status')}")
    print("participants:")
    for p in transcript.get("participants", []):
        print(f"  [{p.get('engine')}] {p.get('status')} ({p.get('latency_s')}s)")
        print(f"    {p.get('answer')}")

    synthesis = transcript.get("synthesis")
    if synthesis:
        print(f"synthesis ({synthesis.get('author')}, {synthesis.get('added_at')}):")
        print(f"  {synthesis.get('text')}")
    else:
        print("synthesis: (none yet)")
    return 0


def _cmd_list(_args: argparse.Namespace) -> int:
    councils = cr.list_councils()
    if not councils:
        print("no councils found")
        return 0

    print(f"{'id':<28} {'ok/total':<9} {'synth':<6} question")
    for c in councils:
        synth = "yes" if c["has_synthesis"] else "no"
        okt = f"{c['participants_ok']}/{c['participants_total']}"
        question = (c.get("question") or "")[:60]
        print(f"{c['id']:<28} {okt:<9} {synth:<6} {question}")
    return 0


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(
        prog="council.py",
        description="Brainstorm Council — fan a question out to K free/cheap "
        "models in parallel; the primary agent (moderator) synthesizes after.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    ask_p = sub.add_parser("ask", help="convene a council round")
    ask_p.add_argument("question")
    ask_p.add_argument("--participants", type=int, default=cr.DEFAULT_PARTICIPANTS)
    ask_p.add_argument("--task-type", default=cr.DEFAULT_TASK_TYPE)
    ask_p.add_argument("--timeout", type=float, default=90)
    ask_p.set_defaults(func=_cmd_ask)

    syn_p = sub.add_parser("synthesize", help="record the moderator's synthesis")
    syn_p.add_argument("council_id")
    syn_group = syn_p.add_mutually_exclusive_group(required=True)
    syn_group.add_argument("--text")
    syn_group.add_argument("--file")
    syn_p.add_argument("--author", default="primary-agent")
    syn_p.set_defaults(func=_cmd_synthesize)

    show_p = sub.add_parser("show", help="pretty-print a transcript")
    show_p.add_argument("council_id")
    show_p.set_defaults(func=_cmd_show)

    list_p = sub.add_parser("list", help="list councils, newest first")
    list_p.set_defaults(func=_cmd_list)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
