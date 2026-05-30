#!/usr/bin/env python3
"""Deterministic A-Wiki skill evaluation harness.

This is the local/free gate before any SkillOpt-style optimization. It scores
skill Markdown files against small JSON suites without calling an LLM.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]


def resolve_path(raw: str, *, base_dir: Path) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    candidate = REPO_ROOT / path
    if candidate.exists():
        return candidate
    return base_dir / path


def contains(text: str, phrase: str, *, case_sensitive: bool) -> bool:
    def normalize(value: str) -> str:
        return " ".join(value.replace("`", "").split())

    text = normalize(text)
    phrase = normalize(phrase)
    if case_sensitive:
        return phrase in text
    return phrase.lower() in text.lower()


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def evaluate_case(case: dict[str, Any], *, suite_dir: Path, skill_override: str | None) -> dict[str, Any]:
    skill_raw = skill_override or case.get("skill")
    if not skill_raw:
        raise ValueError(f"case {case.get('id', '<unknown>')} has no skill path")

    skill_path = resolve_path(str(skill_raw), base_dir=suite_dir)
    text = skill_path.read_text(encoding="utf-8")
    case_sensitive = bool(case.get("case_sensitive", False))

    missing = [
        phrase
        for phrase in case.get("required", [])
        if not contains(text, str(phrase), case_sensitive=case_sensitive)
    ]
    forbidden_hits = [
        phrase
        for phrase in case.get("forbidden", [])
        if contains(text, str(phrase), case_sensitive=case_sensitive)
    ]

    max_chars = case.get("max_chars")
    too_long = bool(max_chars is not None and len(text) > int(max_chars))
    min_chars = case.get("min_chars")
    too_short = bool(min_chars is not None and len(text) < int(min_chars))

    passed = not missing and not forbidden_hits and not too_long and not too_short
    return {
        "id": case.get("id", ""),
        "skill": display_path(skill_path),
        "passed": passed,
        "missing": missing,
        "forbidden_hits": forbidden_hits,
        "too_long": too_long,
        "too_short": too_short,
        "weight": float(case.get("weight", 1.0)),
    }


def evaluate_suite(suite_path: Path, *, skill_override: str | None = None) -> dict[str, Any]:
    suite = json.loads(suite_path.read_text(encoding="utf-8"))
    cases = suite.get("cases", [])
    if not isinstance(cases, list) or not cases:
        raise ValueError(f"{suite_path} has no cases")

    results = [
        evaluate_case(case, suite_dir=suite_path.parent, skill_override=skill_override)
        for case in cases
    ]
    total_weight = sum(row["weight"] for row in results)
    passed_weight = sum(row["weight"] for row in results if row["passed"])
    score = passed_weight / total_weight if total_weight else 0.0
    failed = [row for row in results if not row["passed"]]

    return {
        "suite": suite.get("suite", suite_path.stem),
        "description": suite.get("description", ""),
        "score": round(score, 6),
        "passed": not failed,
        "total_cases": len(results),
        "passed_cases": len(results) - len(failed),
        "failed_cases": len(failed),
        "cases": results,
    }


def format_text(payload: dict[str, Any]) -> str:
    status = "PASS" if payload["passed"] else "FAIL"
    lines = [
        f"{status} {payload['suite']} score={payload['score']:.3f} "
        f"({payload['passed_cases']}/{payload['total_cases']} cases)",
    ]
    for row in payload["cases"]:
        mark = "OK" if row["passed"] else "FAIL"
        lines.append(f"- {mark} {row['id']} [{row['skill']}]")
        if row["missing"]:
            lines.append("  missing: " + ", ".join(row["missing"]))
        if row["forbidden_hits"]:
            lines.append("  forbidden: " + ", ".join(row["forbidden_hits"]))
        if row["too_long"]:
            lines.append("  too_long: true")
        if row["too_short"]:
            lines.append("  too_short: true")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate A-Wiki skill Markdown against deterministic suites")
    parser.add_argument("--suite", required=True, help="Path to eval suite JSON")
    parser.add_argument("--skill", default=None, help="Override skill path for all cases")
    parser.add_argument("--threshold", type=float, default=1.0, help="Minimum score to pass")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    suite_path = resolve_path(args.suite, base_dir=REPO_ROOT)
    payload = evaluate_suite(suite_path, skill_override=args.skill)
    payload["threshold"] = args.threshold
    payload["passed"] = payload["score"] >= args.threshold and payload["failed_cases"] == 0

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_text(payload))

    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
