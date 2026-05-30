#!/usr/bin/env python3
"""A-Wiki skill quality dashboard.

The report focuses on A-Wiki-owned skills and intentionally skips vendor
snapshots (`_upstream/`, `skills/ecosystem/`) to keep the signal high.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]

SKILL_ROOTS = [
    "skills/claude-code",
    "skills/claude-thai",
    "skills/domain",
    "skills/delegation",
    "agent-skills/engineering",
    "agent-skills/productivity",
]

SKIP_PARTS = {"_upstream", "ecosystem", "__pycache__"}
SOFT_MAX_CHARS = 18000
HARD_MAX_CHARS = 35000


@dataclass(frozen=True)
class SkillQuality:
    level: str
    path: str
    name: str
    chars: int
    eval_covered: bool
    issues: list[str]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw = text[4:end]
    body = text[end + 4 :].lstrip("\n")
    meta: dict[str, Any] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta, body


def discover_skill_files() -> list[Path]:
    skills: list[Path] = []
    for root in SKILL_ROOTS:
        base = REPO_ROOT / root
        if not base.exists():
            continue
        for path in base.rglob("SKILL.md"):
            if any(part in SKIP_PARTS for part in path.relative_to(REPO_ROOT).parts):
                continue
            skills.append(path)
    return sorted(set(skills))


def discover_eval_coverage() -> set[Path]:
    covered: set[Path] = set()
    eval_root = REPO_ROOT / "evals" / "awiki"
    if not eval_root.exists():
        return covered
    for suite in eval_root.glob("*.json"):
        try:
            data = json.loads(suite.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for case in data.get("cases", []):
            skill = case.get("skill")
            if not skill:
                continue
            path = Path(skill)
            if not path.is_absolute():
                path = REPO_ROOT / path
            covered.add(path.resolve())
    return covered


def title_from_path(path: Path) -> str:
    if path.parent.name:
        return path.parent.name
    return path.stem


def dangerous_patterns(text: str) -> list[str]:
    normalized = text.replace("`", "")
    normalized_lower = normalized.lower()
    patterns = [
        r"\bgit\s+reset\s+--hard\b",
        r"\bgit\s+push\s+--force\b",
        r"\bgit\s+checkout\s+--\b",
        r"\bgit\s+clean\s+-f\b",
        r"\bgit\s+add\s+raw/?\b",
    ]
    has_safety_guard = (
        "git status first" in normalized_lower
        and ("รอ user confirm" in normalized or "user confirm" in normalized_lower)
        and ("stash" in normalized_lower or "เสนอ stash" in normalized)
    )
    hits = []
    for pattern in patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            if not has_safety_guard:
                hits.append("dangerous-git-pattern")
            break
    if re.search(r"\bedit\s+raw/", text, flags=re.IGNORECASE):
        hits.append("raw-edit-pattern")
    return hits


def analyze_skill(path: Path, eval_covered: set[Path]) -> SkillQuality:
    text = path.read_text(encoding="utf-8", errors="replace")
    meta, body = parse_frontmatter(text)
    issues: list[str] = []

    if not meta:
        issues.append("missing-frontmatter")
    else:
        if not meta.get("name"):
            issues.append("missing-name")
        if not meta.get("description"):
            issues.append("missing-description")

    if not body.lstrip().startswith("#"):
        issues.append("missing-h1")

    resolved = path.resolve()
    covered = resolved in eval_covered
    if not covered:
        issues.append("no-eval-coverage")

    if len(text) > HARD_MAX_CHARS:
        issues.append("too-long-hard")
    elif len(text) > SOFT_MAX_CHARS:
        issues.append("too-long-soft")

    issues.extend(dangerous_patterns(text))

    if any(issue in issues for issue in ("dangerous-git-pattern", "raw-edit-pattern", "too-long-hard")):
        level = "FAIL"
    elif issues:
        level = "WARN"
    else:
        level = "OK"

    return SkillQuality(
        level=level,
        path=rel(path),
        name=str(meta.get("name") or title_from_path(path)),
        chars=len(text),
        eval_covered=covered,
        issues=issues,
    )


def summarize(results: list[SkillQuality]) -> dict[str, int]:
    counts = {"OK": 0, "WARN": 0, "FAIL": 0}
    for result in results:
        counts[result.level] = counts.get(result.level, 0) + 1
    counts["total"] = len(results)
    return counts


def format_markdown(results: list[SkillQuality]) -> str:
    counts = summarize(results)
    lines = [
        "# A-Wiki Skill Quality Report",
        "",
        f"Total: {counts['total']} | OK: {counts['OK']} | WARN: {counts['WARN']} | FAIL: {counts['FAIL']}",
        "",
        "| Level | Skill | Eval | Chars | Issues |",
        "|---|---|---:|---:|---|",
    ]
    for result in results:
        issue_text = ", ".join(result.issues) if result.issues else "-"
        eval_text = "yes" if result.eval_covered else "no"
        lines.append(f"| {result.level} | `{result.path}` | {eval_text} | {result.chars} | {issue_text} |")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Report quality issues in A-Wiki-owned skills.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    parser.add_argument("--fail-on-warn", action="store_true", help="Exit non-zero on WARN as well as FAIL.")
    args = parser.parse_args()

    eval_covered = discover_eval_coverage()
    results = [analyze_skill(path, eval_covered) for path in discover_skill_files()]

    if args.json:
        payload = {"summary": summarize(results), "skills": [asdict(result) for result in results]}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_markdown(results))

    if any(result.level == "FAIL" for result in results):
        return 1
    if args.fail_on_warn and any(result.level == "WARN" for result in results):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
