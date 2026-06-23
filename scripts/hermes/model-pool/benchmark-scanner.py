#!/usr/bin/env python3
"""
Benchmark Scanner — Advisory Model Discovery
A-Wiki Brain · Hermes Agent

Scans 3 benchmark sources for cheaper/smarter models than the current chain.
ADVISORY ONLY: writes a report, NEVER edits config. Alerts via Telegram if a
candidate crosses the suggest threshold.

Sources:
  - ArtificialAnalysis    (https://artificialanalysis.ai/)
  - ChatbotArena          (https://huggingface.co/spaces/lmarena-ai/chatbot-arena)
  - Open LLM Leaderboard  (https://huggingface.co/open-llm-leaderboard)

Usage:
    python3 benchmark-scanner.py --dry-run        # no network, build stub report
    python3 benchmark-scanner.py                  # live scan + advisory report
    python3 benchmark-scanner.py --json           # JSON to stdout
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", ".."))
CFG_PATH = os.path.join(SCRIPT_DIR, "model-priority-config.json")
POOL_PATH = os.path.join(SCRIPT_DIR, "model-pool.json")
REPORT_DIR = os.path.join(REPO_ROOT, "reports", "benchmark")

SOURCES = [
    {"name": "ArtificialAnalysis", "url": "https://artificialanalysis.ai/",
     "metrics": ["cost_per_1m_tokens", "performance_score", "latency"]},
    {"name": "ChatbotArena",
     "url": "https://huggingface.co/spaces/lmarena-ai/chatbot-arena",
     "metrics": ["elo_rating"]},
    {"name": "OpenLLMLeaderboard",
     "url": "https://huggingface.co/open-llm-leaderboard",
     "metrics": ["benchmark_scores"]},
]

DEFAULT_THRESHOLD = {"cost_savings_percent": 20, "performance_gain_percent": 5}


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return default
    return default


def current_chain(pool):
    """Extract current text fallback chain as baseline."""
    return pool.get("fallback_chain", {}).get("text", [])


def fetch_source(source):
    """Best-effort fetch of a source. Returns raw text or None.

    Network access is best-effort: on Pi5 offline or rate-limit, returns None
    and the report marks the source as 'unreachable'.
    """
    try:
        import urllib.request
        req = urllib.request.Request(source["url"], headers={"User-Agent": "A-Wiki-benchmark-scanner/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001
        return None


def parse_candidates(source_name, raw):
    """Heuristic candidate extraction. Real parsing is source-specific and volatile;
    this stub returns an empty list and logs that manual review is needed.

    In production, each source needs a dedicated parser (often scraping or an
    unofficial API). Until those exist, the scanner focuses on:
      - proving the source was reachable
      - emitting the report skeleton for manual review
    """
    if not raw:
        return []
    # Placeholder: real parsers TBD per source. Avoid false positives.
    return []


def build_report(dry_run=False):
    cfg = load_json(CFG_PATH, {})
    pool = load_json(POOL_PATH, {"fallback_chain": {"text": []}})
    threshold = cfg.get("benchmark_sources", {}).get("suggest_threshold", DEFAULT_THRESHOLD)

    sources_state = []
    for src in SOURCES:
        if dry_run:
            raw, reachable = None, False
            note = "dry-run: no network"
        else:
            raw = fetch_source(src)
            reachable = raw is not None
            note = "ok" if reachable else "unreachable / fetch failed"
        candidates = parse_candidates(src["name"], raw)
        sources_state.append({
            "name": src["name"],
            "url": src["url"],
            "reachable": reachable,
            "candidate_count": len(candidates),
            "candidates": candidates,
            "note": note,
        })

    suggestions = []
    # Advisory logic: a candidate is suggested if it beats threshold on cost OR
    # performance vs the current chain. Without live parsers, suggestions stay empty
    # and the report serves as a reachability + manual-review prompt.
    for s in sources_state:
        for c in s["candidates"]:
            cost_save = c.get("cost_savings_percent", 0)
            perf_gain = c.get("performance_gain_percent", 0)
            if cost_save >= threshold["cost_savings_percent"] or \
               perf_gain >= threshold["performance_gain_percent"]:
                suggestions.append({
                    "candidate": c.get("model"),
                    "source": s["name"],
                    "cost_savings_percent": cost_save,
                    "performance_gain_percent": perf_gain,
                    "action": "PROPOSE to user (advisory, NOT auto-applied)",
                })

    return {
        "schema_version": 1,
        "generated_at": now_iso(),
        "mode": "advisory_only",
        "threshold": threshold,
        "current_chain": current_chain(pool),
        "sources": sources_state,
        "suggestions": suggestions,
        "summary": (
            f"{sum(1 for s in sources_state if s['reachable'])}/{len(sources_state)} sources reachable; "
            f"{len(suggestions)} suggestion(s) above threshold."
        ),
        "note": "Advisory only. This scanner never edits config. Review suggestions manually.",
    }


def write_report(report):
    os.makedirs(REPORT_DIR, exist_ok=True)
    stamp = time.strftime("%Y%m%d", time.gmtime())
    path = os.path.join(REPORT_DIR, f"benchmark-{stamp}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    return path


def notify_telegram(message):
    notify = os.path.join(os.path.dirname(SCRIPT_DIR), "notify-telegram.sh")
    if not os.path.exists(notify):
        return False
    escaped = message.replace("'", "'\\''")
    return os.system(f"bash {notify} '{escaped}'") == 0


def main():
    parser = argparse.ArgumentParser(description="Benchmark Scanner (advisory only)")
    parser.add_argument("--dry-run", action="store_true", help="no network, skeleton report")
    parser.add_argument("--json", action="store_true", help="JSON to stdout instead of file+text")
    args = parser.parse_args()

    report = build_report(dry_run=args.dry_run)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return

    path = write_report(report)
    print(f"Report: {path}")
    print(report["summary"])
    for s in report["sources"]:
        flag = "OK " if s["reachable"] else "OFF"
        print(f"  [{flag}] {s['name']:20s} {s['url']}")
    if report["suggestions"]:
        print("Suggestions (advisory):")
        for sug in report["suggestions"]:
            print(f"  - {sug['candidate']} ({sug['source']}): "
                  f"save {sug['cost_savings_percent']}% / gain {sug['performance_gain_percent']}%")
        notify_telegram(
            f"[Hermes] Benchmark scanner found {len(report['suggestions'])} suggestion(s). "
            f"Report: {path}")


if __name__ == "__main__":
    main()
