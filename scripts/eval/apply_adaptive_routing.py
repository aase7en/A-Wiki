#!/usr/bin/env python3
"""apply_adaptive_routing.py — CLI for P4 adaptive routing.

Loads observatory stats + eval results + swap history, calls
adaptive_routing.recommend_model_changes(), prints a preview by default,
and writes frontmatter only when --apply is passed (so the user can review
recommendations before any change — mirrors apply_eval_results.py).

Usage:
  # Preview only (default — no writes)
  python scripts/eval/apply_adaptive_routing.py \\
      --stats-json <path-or-url> \\
      --eval-results evals/subagents/results/

  # Actually apply the recommendations
  python scripts/eval/apply_adaptive_routing.py --stats-json ... --eval-results ... --apply

  # Emit JSON instead of the human-readable table
  python scripts/eval/apply_adaptive_routing.py --stats-json ... --json

Swap-history file (optional): .tmp/adaptive-routing-log.jsonl — one JSON
object per line: {subagent, from, to, ts}. Used for flap detection.
Missing file → no flap history (all changes pass the flap check).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))

import adaptive_routing as ar  # noqa: E402
from apply_eval_results import build_suite_to_subagents  # noqa: E402

SUBAGENTS_DIR = REPO_ROOT / "agents" / "subagents"
SUITES_DIR = REPO_ROOT / "evals" / "subagents"
RESULTS_DIR = SUITES_DIR / "results"
DEFAULT_STATS_URL = "http://localhost:7790/api/subagents/stats?since=604800"
HISTORY_FILE = REPO_ROOT / ".tmp" / "adaptive-routing-log.jsonl"


def _load_json_source(src: str) -> dict:
    """Load JSON from a file path or http(s) URL."""
    if src.startswith("http://") or src.startswith("https://"):
        import urllib.request
        with urllib.request.urlopen(src, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    return json.loads(Path(src).read_text(encoding="utf-8"))


def _load_results(results_path: Path) -> dict:
    """Merge all results-*.json files (or one file) into a single dict."""
    rpath = Path(results_path)
    if rpath.is_dir():
        files = sorted(rpath.glob("results-*.json"))
    elif rpath.is_file():
        files = [rpath]
    else:
        return {}
    merged: dict = {}
    for f in files:
        try:
            merged.update(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            continue
    return merged


def _load_current_models() -> dict[str, str]:
    """Read the current `model:` field from every agents/subagents/*.md."""
    import re
    out: dict[str, str] = {}
    if not SUBAGENTS_DIR.is_dir():
        return out
    for p in SUBAGENTS_DIR.glob("*.md"):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        m = re.search(r"^name:\s*[\"']?([^\"'\n]+)[\"']?\s*$", text, re.MULTILINE)
        name = m.group(1).strip() if m else p.stem
        mm = re.search(r"^model:\s*[\"']?([^\"'\n]+)[\"']?\s*$", text, re.MULTILINE)
        out[name] = mm.group(1).strip() if mm else ""
    return out


def _load_history() -> list[dict]:
    if not HISTORY_FILE.is_file():
        return []
    out: list[dict] = []
    for line in HISTORY_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def _append_history(subagent: str, frm: str, to: str) -> None:
    """Append a swap record to the history file (for future flap detection)."""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    rec = {"subagent": subagent, "from": frm, "to": to, "ts": time.time()}
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1].strip())
    p.add_argument("--stats-json", default=DEFAULT_STATS_URL,
                   help="path or URL to observatory stats JSON "
                        "(default: live dashboard 7d window)")
    p.add_argument("--eval-results", default=str(RESULTS_DIR),
                   help="dir or file of eval results (default: evals/subagents/results/)")
    p.add_argument("--apply", action="store_true",
                   help="actually rewrite frontmatter (default: preview only)")
    p.add_argument("--json", action="store_true", help="emit raw JSON output")
    p.add_argument("--min-samples", type=int, default=None,
                   help="override min_samples guardrail")
    p.add_argument("--min-delta", type=float, default=None,
                   help="override min_delta guardrail")
    args = p.parse_args()

    # Load inputs.
    try:
        stats = _load_json_source(args.stats_json)
    except Exception as e:
        print(f"Failed to load stats from {args.stats_json}: {e}", file=sys.stderr)
        return 1
    eval_results = _load_results(Path(args.eval_results))
    if not eval_results:
        print(f"No eval results found at {args.eval_results}.", file=sys.stderr)
        print("Run scripts/eval/run_subagent_eval.py --all --apply first.", file=sys.stderr)
        return 1
    current_models = _load_current_models()
    suite_to_subagents = build_suite_to_subagents(SUITES_DIR)
    history = _load_history()

    config = {}
    if args.min_samples is not None:
        config["min_samples"] = args.min_samples
    if args.min_delta is not None:
        config["min_delta"] = args.min_delta

    changes = ar.recommend_model_changes(
        stats, eval_results, current_models, suite_to_subagents,
        config=config or None, history=history)

    if args.json:
        print(json.dumps({"changes": changes}, indent=2, ensure_ascii=False))
    else:
        print(ar.render_preview(changes))

    if args.apply:
        applied = ar.apply_changes(changes, agents_dir=SUBAGENTS_DIR)
        # Append swap records for future flap detection.
        for c in changes:
            if c.get("status") == "recommend" and c["current"] != c["recommended"]:
                _append_history(c["subagent"], c["current"], c["recommended"])
        print(f"\n{applied} file(s) updated.", file=sys.stderr)
    else:
        print("\n(preview only — re-run with --apply to write frontmatter)",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
