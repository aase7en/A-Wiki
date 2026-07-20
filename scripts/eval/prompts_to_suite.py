#!/usr/bin/env python3
"""
prompts_to_suite.py — Generate eval suite from prod-log prompts (Y2).

อ่าน .tmp/prompts/<subagent>-*.jsonl → dedupe + filter (min_count) →
auto-generate eval suite JSON (stdout) สำหรับ user review ก่อน import ผ่าน X3 GUI.

Privacy: prompts ผ่าน redaction แล้ว (Y1 prompt_redactor.redact).
No auto-write to evals/ — output ไป stdout เท่านั้น (human review required).

Usage:
  python scripts/eval/prompts_to_suite.py --subagent clinical-reasoner
  python scripts/eval/prompts_to_suite.py --subagent clinical-reasoner --min-count 3
  python scripts/eval/prompts_to_suite.py --subagent X --suite-name my-prod-suite
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PROMPTS_DIR = REPO_ROOT / ".tmp" / "prompts"


def collect_prompts(
    subagent: str,
    prompts_dir: Path | str = PROMPTS_DIR,
    min_count: int = 1,
) -> list[dict[str, Any]]:
    """Read prompt logs for a subagent → dedupe + count.

    Returns: [{prompt, count}, ...] sorted by count desc.
    """
    pdir = Path(prompts_dir)
    if not pdir.is_dir():
        return []
    counter: Counter = Counter()
    for f in sorted(pdir.glob(f"{subagent}-*.jsonl")):
        try:
            for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                prompt = entry.get("prompt", "").strip()
                if prompt:
                    counter[prompt] += 1
        except Exception:
            continue
    return [{"prompt": p, "count": c} for p, c in counter.most_common() if c >= min_count]


def _extract_keywords(text: str, top_n: int = 2) -> list[str]:
    """Extract top-N meaningful keywords from text (for auto-required).

    Simple heuristic: words >3 chars, not stopwords, sorted by length desc.
    """
    STOPWORDS = {"the", "and", "for", "with", "from", "this", "that", "what",
                 "how", "why", "summarize", "analyze", "explain", "about", "please"}
    words = re.findall(r"[A-Za-z]{4,}", text.lower())
    meaningful = [w for w in words if w not in STOPWORDS]
    # Dedupe preserving order, take top N by first occurrence
    seen = set()
    unique = []
    for w in meaningful:
        if w not in seen:
            seen.add(w)
            unique.append(w)
    return unique[:top_n]


def build_suite(
    subagent: str,
    collected: list[dict[str, Any]],
    suite_name: str | None = None,
) -> dict[str, Any]:
    """Build an eval suite dict from collected prompts.

    Auto-generates case ids + required keywords. Forbidden = ["i don't know"].
    """
    name = suite_name or f"prod-{subagent}"
    cases = []
    for i, item in enumerate(collected):
        prompt = item["prompt"]
        keywords = _extract_keywords(prompt)
        cases.append({
            "id": f"prod-{i+1}",
            "subagent": subagent,
            "prompt": prompt,
            "required": keywords,
            "forbidden": ["i don't know"],
        })
    return {
        "suite": name,
        "description": f"Production-derived eval suite for {subagent} ({len(cases)} cases from {sum(c['count'] for c in collected)} logged prompts). Auto-generated — review before use.",
        "cases": cases,
    }


def build_suite_from_logs(
    subagent: str,
    prompts_dir: Path | str = PROMPTS_DIR,
    min_count: int = 3,
    suite_name: str | None = None,
) -> dict[str, Any] | None:
    """One-call: collect + build. Returns None ถ้า no prompts meet threshold."""
    collected = collect_prompts(subagent, prompts_dir, min_count)
    if not collected:
        return None
    return build_suite(subagent, collected, suite_name)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1].strip())
    p.add_argument("--subagent", required=True, help="subagent name (e.g. clinical-reasoner)")
    p.add_argument("--min-count", type=int, default=3,
                   help="minimum prompt occurrence count (default: 3 — filters one-offs)")
    p.add_argument("--suite-name", default=None,
                   help="custom suite name (default: prod-<subagent>)")
    args = p.parse_args()

    suite = build_suite_from_logs(args.subagent, PROMPTS_DIR, args.min_count, args.suite_name)
    if suite is None:
        print(f"No prompts for '{args.subagent}' (min_count={args.min_count}).", file=sys.stderr)
        print(f"  Checked: {PROMPTS_DIR}/{args.subagent}-*.jsonl", file=sys.stderr)
        print("  Set AWIKI_LOG_PROMPTS=1 to start collecting.", file=sys.stderr)
        return 1

    # Output suite JSON to stdout (for user review + import via X3 GUI)
    print(json.dumps(suite, indent=2, ensure_ascii=False))
    print(f"\n# 💡 Review above suite → import via dashboard ✏️ Suite Editor (X3)", file=sys.stderr)
    print(f"# {len(suite['cases'])} cases from {sum(c['count'] for c in collect_prompts(args.subagent, PROMPTS_DIR, args.min_count))} prompts", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
