#!/usr/bin/env python3
"""Scout model capability scores from public leaderboards (offline-first).

Loads the committed scorecard (wiki/context/model-capability-scores.json) as the
durable base, then best-effort refreshes per-dimension scores from three
leaderboards. Any source that fails or returns nothing simply contributes
nothing — the committed value stays. Never raises on network/parse failure.

Sources:
  swe_bench       https://www.swebench.com/                              (coding / resolve-issue)
  terminal_bench  https://www.tbench.ai/leaderboard/terminal-bench/2.0   (agentic / terminal)
  nl2repobench    https://github.com/multimodal-art-projection/NL2RepoBench (NL -> repo code)
  aider_polyglot  https://aider.chat/docs/leaderboards/                  (edit/refactor, multi-lang)
  livecodebench   https://livecodebench.github.io/                       (contaminant-controlled coding)

NOTE: most rendered leaderboards have no clean JSON feed (verified 2026-06-16:
aider.chat/assets/leaderboard.json = 404, swebench.com / tbench.ai are JS pages).
_parse_markdown_scores extracts `|model|...|NN.N|` rows when present; pages that
are not machine-readable simply contribute nothing -> committed value is kept.
This is the "live + offline fallback" contract. Dedicated parsers can be added
per-source later without touching build_cache (it iterates SOURCES dynamically).

Usage:
  python3 scripts/model-capability-scout.py            # best-effort refresh -> .tmp cache
  python3 scripts/model-capability-scout.py --offline  # committed scores only
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SCORECARD = REPO_ROOT / "wiki" / "context" / "model-capability-scores.json"
DEFAULT_OUT = REPO_ROOT / ".tmp" / "model-capability-cache.json"

# Source endpoints. GitHub raw is parseable JSON/markdown; the rendered
# leaderboard pages have no guaranteed clean API, so they degrade to "unparseable".
SOURCES = {
    "swe_bench": {
        "label": "SWE-bench",
        "url": "https://www.swebench.com/",
    },
    "terminal_bench": {
        "label": "Terminal-Bench 2.0",
        "url": "https://www.tbench.ai/leaderboard/terminal-bench/2.0",
    },
    "nl2repobench": {
        "label": "NL2RepoBench",
        "url": "https://raw.githubusercontent.com/multimodal-art-projection/NL2RepoBench/main/README.md",
    },
    "aider_polyglot": {
        "label": "Aider Polyglot",
        "url": "https://aider.chat/docs/leaderboards/",
    },
    "livecodebench": {
        "label": "LiveCodeBench",
        "url": "https://livecodebench.github.io/",
    },
}


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def load_scorecard() -> dict[str, Any]:
    """Load the committed scorecard — the durable floor. Never fails hard."""
    try:
        return json.loads(SCORECARD.read_text("utf-8"))
    except Exception:
        return {
            "schema_version": 1,
            "families": {},
            "dimensions": ["swe_bench", "terminal_bench", "nl2repobench", "reasoning", "speed"],
            "neutral_default": 50,
            "note": "scorecard missing/unreadable; empty base",
        }


def fetch_text(url: str, timeout: int) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "a-wiki-capability-scout"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def _match_family(families: dict[str, Any], label: str) -> str | None:
    """Map a leaderboard model label to a scorecard family key via match substrings."""
    low = label.lower()
    for key, fam in families.items():
        if any(s in low for s in fam.get("match", [])):
            return key
    return None


def scout_source(dimension: str, families: dict[str, Any], offline: bool, timeout: int) -> dict[str, Any]:
    """Best-effort fetch one leaderboard. Returns {status, scores:{family:score}}.

    The rendered leaderboard pages (swebench.com, tbench.ai) expose no stable
    machine-readable feed, so without a dedicated parser they are reported
    "unparseable" and contribute nothing — the committed value is kept. This is
    intentional: the committed scorecard is the source of truth; the scout is
    best-effort polish, never a hard dependency.
    """
    src = SOURCES.get(dimension)
    if not src:
        return {"status": "skipped", "scores": {}}
    if offline:
        return {"status": "skipped-offline", "scores": {}}
    try:
        text = fetch_text(src["url"], timeout)
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError):
        return {"status": "error", "scores": {}, "url": src["url"]}

    scores = _parse_markdown_scores(dimension, families, text)
    if scores:
        return {"status": "ok", "scores": scores, "url": src["url"]}
    return {"status": "unparseable", "scores": {}, "url": src["url"]}


def _parse_markdown_scores(dimension: str, families: dict[str, Any], text: str) -> dict[str, int]:
    """Parse a markdown leaderboard table of form `| model | ... | NN.N |`.

    Only matches rows where a family substring is present and a percentage-like
    number can be extracted. Robust to absence — returns {} when nothing parses.
    """
    import re

    scores: dict[str, int] = {}
    for line in text.splitlines():
        if "|" not in line:
            continue
        fam = _match_family(families, line)
        if not fam or fam in scores:
            continue
        nums = re.findall(r"(\d{1,3}(?:\.\d+)?)\s*%?", line)
        vals = [float(n) for n in nums if 0 <= float(n) <= 100]
        if vals:
            scores[fam] = round(max(vals))
    return scores


def build_cache(offline: bool, timeout: int) -> dict[str, Any]:
    base = load_scorecard()
    result = copy.deepcopy(base)
    families = result.get("families", {})
    sources_status: dict[str, Any] = {}

    for dimension in list(SOURCES.keys()):
        outcome = scout_source(dimension, families, offline, timeout)
        sources_status[dimension] = {
            "status": outcome["status"],
            "url": outcome.get("url", SOURCES.get(dimension, {}).get("url", "")),
        }
        for fam_key, val in outcome.get("scores", {}).items():
            fam = families.get(fam_key)
            if fam is not None:
                fam[dimension] = val
                fam["as_of"] = now_iso()[:10]
                fam["confidence"] = "refreshed"

    result["families"] = families
    result["generated_at"] = now_iso()
    result["offline"] = offline
    result["sources_status"] = sources_status
    result["base"] = "wiki/context/model-capability-scores.json"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Scout model capability scores (offline-first).")
    parser.add_argument("--offline", action="store_true", help="committed scores only; no network")
    parser.add_argument("--offline-ok", action="store_true", help="never hard-fail on network (default behavior)")
    parser.add_argument("--timeout", type=int, default=8, help="per-source network timeout seconds")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output cache JSON path")
    parser.add_argument("--quiet", action="store_true", help="suppress text output")
    args = parser.parse_args()

    try:
        cache = build_cache(offline=args.offline, timeout=args.timeout)
    except Exception as exc:  # absolute backstop — degrade to committed
        cache = load_scorecard()
        cache["generated_at"] = now_iso()
        cache["scout_error"] = str(exc)

    try:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(cache, ensure_ascii=False, indent=2), "utf-8")
    except Exception as exc:
        if not args.quiet:
            sys.stderr.write(f"⚠️ capability scout: could not write cache: {exc}\n")
        return 0  # offline-first: never block the router

    if not args.quiet:
        statuses = cache.get("sources_status", {})
        summary = ", ".join(f"{k}={v.get('status')}" for k, v in statuses.items())
        sys.stderr.write(f"🏁 capability scout → {args.out} ({summary or 'committed only'})\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
