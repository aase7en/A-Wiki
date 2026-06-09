"""
route.py — Universal CLI entry for A-Wiki cost-aware ingestion.

Used by every agent (Claude Code MCP, Codex CLI, Gemini CLI, Cursor,
Windsurf, Cline, Copilot, Aider) and by shell wrappers route.sh /
route.ps1 / route.cmd.

Usage examples:
  python scripts/batch/route.py --domain ai-tools --limit 50
  python scripts/batch/route.py --tier 1 --file raw/foo.md
  python scripts/batch/route.py --tier 2 --slugs s1,s2,s3
  python scripts/batch/route.py --estimate --limit 100
  A_WIKI_ROUTE_TIER=2 python scripts/batch/route.py --limit 100
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "batch"))

from collect import write_results  # noqa: E402
from config import load_conf  # noqa: E402
from router import (  # noqa: E402
    build_requests,
    discover_backlog,
    dispatch,
    estimate_cost,
    select_tier,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="A-Wiki cost-aware ingestion router (universal harness)",
    )
    p.add_argument("--tier", type=int, choices=[1, 2, 3], help="Force a tier (1=DeepSeek, 2=OpenAI batch, 3=Anthropic batch)")
    p.add_argument("--backend", choices=["deepseek", "openai", "anthropic"], help="Force a backend (alias for --tier)")
    p.add_argument("--domain", help="Domain hint (iot|env|ai-tools|pharmacy|it|general)")
    p.add_argument("--limit", type=int, help="Max files to ingest in this run")
    p.add_argument("--slugs", help="Comma-separated list of slugs (filters raw/ scan)")
    p.add_argument("--file", help="Single raw/<file> path (overrides scan)")
    p.add_argument("--estimate", action="store_true", help="Print cost estimate per tier and exit (no API call)")
    p.add_argument("--dry-run", action="store_true", help="Build requests + select tier but do not call the API")
    p.add_argument("--no-gen-index", action="store_true", help="Skip gen-index.py after writing (tier-1 only)")
    p.add_argument("--json", action="store_true", help="Emit JSON result (default: human-readable)")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    slugs = [s.strip() for s in args.slugs.split(",")] if args.slugs else None

    try:
        paths = discover_backlog(
            domain_hint=args.domain, limit=args.limit, slugs=slugs, file=args.file
        )
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if not paths:
        print("No files to ingest (raw/ scan returned 0 candidates not yet under wiki/sources/).")
        return 0

    conf = load_conf()
    # Build requests first so the complexity classifier can inspect them.
    provisional = build_requests(paths, 1, domain_hint=args.domain)
    tier, tier_reason = select_tier(
        paths,
        cli_tier=args.tier,
        cli_backend=args.backend,
        conf=conf,
        requests=provisional,
    )
    requests = build_requests(paths, tier, domain_hint=args.domain)

    if args.estimate:
        report = {
            "n_files": len(paths),
            "selected_tier": tier,
            "tier_reason": tier_reason,
            "tiers": {
                t: estimate_cost(requests, t, conf)
                for t in (0, 1, 2, 3)
                if conf.has_section(f"tier_{t}")
            },
        }
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    if args.dry_run:
        out = {
            "tier": tier,
            "tier_reason": tier_reason,
            "n_requests": len(requests),
            "requests": [asdict(r) for r in requests[:5]],
            "truncated": len(requests) > 5,
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0

    try:
        submitted = dispatch(requests, tier)
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if submitted.get("mode") == "realtime":
        summary = write_results(submitted["results"], run_gen_index=not args.no_gen_index)
        out = {
            "tier": tier,
            "tier_reason": tier_reason,
            "mode": "realtime",
            "written": summary["written"],
            "skipped": summary["skipped"],
        }
    else:
        out = {
            "tier": tier,
            "tier_reason": tier_reason,
            "mode": "batch",
            "batch_id": submitted["batch_id"],
            "input_path": submitted.get("input_path"),
            "next_step": f"poll: py -3 scripts/batch/poll.py --batch {submitted['batch_id']}",
            "then": f"collect: py -3 scripts/batch/collect.py --batch {submitted['batch_id']}",
        }

    if args.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        _print_human(out)
    return 0


def _print_human(out: dict) -> None:
    reason = out.get("tier_reason", "")
    suffix = f"  ({reason})" if reason else ""
    print(f"Tier: {out['tier']}  |  Mode: {out['mode']}{suffix}")
    if out["mode"] == "realtime":
        print(f"Written: {len(out['written'])}")
        for w in out["written"]:
            print(f"  ✓ {w}")
        if out["skipped"]:
            print(f"Skipped: {len(out['skipped'])}")
            for s in out["skipped"][:10]:
                print(f"  ✗ {s['slug']} — {s['reason']}")
    else:
        print(f"Batch ID: {out['batch_id']}")
        print(f"Input:    {out['input_path']}")
        print(f"Next:     {out['next_step']}")
        print(f"Then:     {out['then']}")


if __name__ == "__main__":
    raise SystemExit(main())
