#!/usr/bin/env python3
"""A-Wiki SkillOpt candidate gate.

Use this after SkillOpt (or any optimizer) proposes a candidate skill document.
The gate accepts only candidates that meet the threshold and do not regress
against the current skill on the same deterministic A-Wiki suite.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from awiki_eval import REPO_ROOT, evaluate_suite, format_text, resolve_path


def build_gate_payload(
    *,
    suite_path: Path,
    current_skill: str,
    candidate_skill: str,
    threshold: float,
    min_delta: float,
) -> dict:
    current = evaluate_suite(suite_path, skill_override=current_skill)
    candidate = evaluate_suite(suite_path, skill_override=candidate_skill)

    current_score = float(current["score"])
    candidate_score = float(candidate["score"])
    delta = round(candidate_score - current_score, 6)
    accept = candidate_score >= threshold and delta >= min_delta and candidate["failed_cases"] == 0

    return {
        "suite": candidate["suite"],
        "action": "accept" if accept else "reject",
        "current_score": current_score,
        "candidate_score": candidate_score,
        "delta": delta,
        "threshold": threshold,
        "min_delta": min_delta,
        "current": current,
        "candidate": candidate,
    }


def format_gate_text(payload: dict) -> str:
    lines = [
        f"{payload['action'].upper()} {payload['suite']} "
        f"current={payload['current_score']:.3f} "
        f"candidate={payload['candidate_score']:.3f} "
        f"delta={payload['delta']:.3f}",
        "",
        "Candidate detail:",
        format_text(payload["candidate"]),
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Gate SkillOpt candidate skills for A-Wiki")
    parser.add_argument("--suite", required=True, help="Path to eval suite JSON")
    parser.add_argument("--current-skill", required=True, help="Current skill Markdown path")
    parser.add_argument("--candidate-skill", required=True, help="Candidate skill Markdown path")
    parser.add_argument("--threshold", type=float, default=1.0, help="Minimum candidate score")
    parser.add_argument("--min-delta", type=float, default=0.0, help="Minimum candidate-current score delta")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    suite_path = resolve_path(args.suite, base_dir=REPO_ROOT)
    payload = build_gate_payload(
        suite_path=suite_path,
        current_skill=args.current_skill,
        candidate_skill=args.candidate_skill,
        threshold=args.threshold,
        min_delta=args.min_delta,
    )

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_gate_text(payload))

    return 0 if payload["action"] == "accept" else 1


if __name__ == "__main__":
    sys.exit(main())
