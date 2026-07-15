#!/usr/bin/env python3
"""
apply_eval_results.py — recommend model changes from eval results.

Reads evals/subagents/results/*.json (produced by run_subagent_eval.py --apply)
and, for each suite+subagent, recommends the model with the highest pass@k.
Prints a diff preview of the `model:` field changes that WOULD be applied to
each subagent's frontmatter. Does NOT write unless --write is passed (so the
user can review the recommendation before any change).

Usage:
  python scripts/eval/apply_eval_results.py --results evals/subagents/results/
  python scripts/eval/apply_eval_results.py --latest           # use newest results file only
  python scripts/eval/apply_eval_results.py --latest --write   # actually apply the changes
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SUBAGENTS_DIR = REPO_ROOT / "agents" / "subagents"
SUITES_DIR = REPO_ROOT / "evals" / "subagents"
RESULTS_DIR = SUITES_DIR / "results"


def load_results(path: Path) -> dict[str, Any]:
    """Load a results JSON file. Returns {} on failure."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {}


def build_suite_to_subagents(suites_dir: Path) -> dict[str, list[str]]:
    """Derive {suite_name: [unique subagent names]} from eval suite files.

    Reads each evals/subagents/*.json (NOT the results/ subdir), extracts the
    `subagent` field from every case, and dedups while preserving first-seen
    order. This map lets build_change_preview resolve a suite recommendation
    to the concrete agents/subagents/<name>.md files that --write must edit.

    P1 fix: before this existed, main() called build_change_preview(recs) with
    suite_to_subagents=None, producing "<all in suite:...>" placeholders that
    --write could never resolve to a file — so no frontmatter was ever edited.
    """
    suites_dir = Path(suites_dir)
    mapping: dict[str, list[str]] = {}
    if not suites_dir.is_dir():
        return mapping
    for p in sorted(suites_dir.glob("*.json")):
        # Skip the results/ subdir if suites_dir is the parent.
        if p.parent.name == "results":
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        suite_name = data.get("suite")
        cases = data.get("cases")
        if not suite_name or not isinstance(cases, list):
            continue  # not an eval suite (e.g. a results file at top level)
        seen: list[str] = []
        for c in cases:
            sa = c.get("subagent")
            if sa and sa not in seen:
                seen.append(sa)
        if seen:
            mapping[suite_name] = seen
    return mapping


def best_model_per_suite(results: dict) -> dict[str, dict]:
    """For each suite, return {suite: {best_model, pass_at_k, per_model}}."""
    out: dict[str, dict] = {}
    for suite_name, suite_res in results.items():
        by_model = suite_res.get("by_model", {})
        if not by_model:
            continue
        best = None
        best_rate = -1.0
        per = {}
        for model, mr in by_model.items():
            rate = mr.get("pass_at_k", 0.0)
            per[model] = rate
            if rate > best_rate or (rate == best_rate and best is None):
                best_rate = rate
                best = model
        out[suite_name] = {"best_model": best, "pass_at_k": best_rate, "per_model": per}
    return out


def current_model_in_frontmatter(subagent_path: Path) -> str:
    """Read the current `model:` field from a subagent's frontmatter."""
    if not subagent_path.is_file():
        return ""
    text = subagent_path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^model:\s*[\"']?([^\"'\n]+)[\"']?\s*$", text, re.MULTILINE)
    return m.group(1).strip() if m else ""


def build_change_preview(
    recommendations: dict[str, dict],
    suite_to_subagents: dict[str, list[str]] | None = None,
) -> list[dict]:
    """Build a list of proposed {subagent, current, recommended, suite} changes.

    suite_to_subagents maps a suite name to the subagents it covers. If None,
    we cannot map suites → individual subagents, so the preview is suite-level only.
    """
    changes = []
    for suite, rec in recommendations.items():
        if suite_to_subagents:
            for sa in suite_to_subagents.get(suite, []):
                sa_path = SUBAGENTS_DIR / f"{sa}.md"
                cur = current_model_in_frontmatter(sa_path)
                if rec["best_model"] and rec["best_model"] != cur:
                    changes.append({
                        "subagent": sa, "suite": suite,
                        "current": cur, "recommended": rec["best_model"],
                        "pass_at_k": rec["pass_at_k"],
                    })
        else:
            # Suite-level only (no per-subagent mapping provided).
            changes.append({
                "subagent": f"<all in suite:{suite}>", "suite": suite,
                "current": "(varies)", "recommended": rec["best_model"],
                "pass_at_k": rec["pass_at_k"],
            })
    return changes


def render_preview(changes: list[dict]) -> str:
    """Human-readable preview of proposed changes."""
    if not changes:
        return "No changes recommended — every subagent already uses its best model."
    lines = ["Recommended model changes (review before --write):", ""]
    lines.append(f"{'subagent':<32} {'current':<24} → {'recommended':<24} {'pass@k'}")
    lines.append("-" * 100)
    for c in changes:
        cur_short = c["current"].split(":")[-1] if c["current"].startswith("custom:") else c["current"]
        rec_short = c["recommended"].split(":")[-1] if c["recommended"].startswith("custom:") else c["recommended"]
        lines.append(f"{c['subagent']:<32} {cur_short:<24} → {rec_short:<24} {c['pass_at_k']:.2f}")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1].strip())
    p.add_argument("--results", default=str(RESULTS_DIR),
                   help="dir or file of results JSON (default: evals/subagents/results/)")
    p.add_argument("--latest", action="store_true",
                   help="use only the newest results-*.json file")
    p.add_argument("--write", action="store_true",
                   help="actually rewrite the frontmatter model: fields (default: preview only)")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    # Gather result files.
    rpath = Path(args.results)
    if rpath.is_dir():
        files = sorted(rpath.glob("results-*.json"))
        if args.latest and files:
            files = [files[-1]]
    elif rpath.is_file():
        files = [rpath]
    else:
        print(f"No results found at {rpath}", file=sys.stderr)
        return 1

    if not files:
        print(f"No results-*.json files in {rpath}. Run run_subagent_eval.py --apply first.",
              file=sys.stderr)
        return 1

    # Merge all results files.
    merged: dict = {}
    for f in files:
        merged.update(load_results(f))

    recs = best_model_per_suite(merged)
    # P1 fix: map suites → concrete subagent files so --write can find them.
    # Without this, build_change_preview emits "<all in suite:...>" placeholders
    # and --write silently edits zero files.
    suite_to_subagents = build_suite_to_subagents(SUITES_DIR)
    changes = build_change_preview(recs, suite_to_subagents=suite_to_subagents)

    if args.json:
        print(json.dumps({"recommendations": recs, "changes": changes}, indent=2, ensure_ascii=False))
    else:
        print(render_preview(changes))

    if args.write:
        print("\n--write mode: applying changes to frontmatter...", file=sys.stderr)
        applied = 0
        for c in changes:
            sa_path = SUBAGENTS_DIR / f"{c['subagent']}.md"
            if not sa_path.is_file():
                continue
            text = sa_path.read_text(encoding="utf-8")
            new_text = re.sub(
                r"^model:\s*.+$",
                f"model: {c['recommended']}",
                text, count=1, flags=re.MULTILINE,
            )
            if new_text != text:
                sa_path.write_text(new_text, encoding="utf-8")
                applied += 1
                print(f"  ✓ {c['subagent']}: {c['current']} → {c['recommended']}", file=sys.stderr)
        print(f"\n{applied} file(s) updated.", file=sys.stderr)
    else:
        print("\n(preview only — re-run with --write to apply)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
