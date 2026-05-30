#!/usr/bin/env python3
"""Validate A-Wiki session memory stays light enough for SessionStart hooks."""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SESSION_MEMORY = REPO_ROOT / "wiki" / "context" / "session-memory.md"
DEFAULT_BACKLOG = REPO_ROOT / "wiki" / "context" / "project-backlog.md"


@dataclass(frozen=True)
class Finding:
    level: str
    message: str


def extract_active_block(text: str) -> list[str]:
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.startswith("## ") and "Active TODOs" in line:
            start = index + 1
            break
    if start is None:
        return []

    block: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        block.append(line)
    return block


def todo_items(block: list[str], checked: bool | None = None) -> list[str]:
    pattern = re.compile(r"^- \[(?P<mark>[ xX])\] ")
    items: list[str] = []
    for line in block:
        match = pattern.match(line.strip())
        if not match:
            continue
        is_checked = match.group("mark").lower() == "x"
        if checked is None or checked == is_checked:
            items.append(line.strip())
    return items


def analyze(
    session_memory: Path = DEFAULT_SESSION_MEMORY,
    backlog: Path = DEFAULT_BACKLOG,
    max_active: int = 12,
    max_line_chars: int = 260,
) -> tuple[list[Finding], dict[str, int | bool]]:
    findings: list[Finding] = []
    if not session_memory.is_file():
        return [Finding("FAIL", f"missing session memory: {session_memory}")], {}

    text = session_memory.read_text(encoding="utf-8", errors="replace")
    block = extract_active_block(text)
    if not block:
        findings.append(Finding("FAIL", "missing ## Active TODOs block"))

    open_items = todo_items(block, checked=False)
    done_items = todo_items(block, checked=True)

    if done_items:
        findings.append(Finding("WARN", f"{len(done_items)} checked item(s) still in Active TODOs"))
    if len(open_items) > max_active:
        findings.append(Finding("FAIL", f"{len(open_items)} active TODOs exceeds cap {max_active}"))

    long_items = [item for item in open_items if len(item) > max_line_chars]
    if long_items:
        findings.append(Finding("WARN", f"{len(long_items)} active TODO(s) exceed {max_line_chars} chars"))

    if not backlog.is_file():
        findings.append(Finding("WARN", f"project backlog missing: {backlog}"))

    summary = {
        "active_open": len(open_items),
        "active_checked": len(done_items),
        "active_cap": max_active,
        "long_active": len(long_items),
        "backlog_exists": backlog.is_file(),
    }
    if not any(f.level == "FAIL" for f in findings):
        findings.insert(0, Finding("OK", f"{len(open_items)} active TODO(s), cap {max_active}"))
    return findings, summary


def exit_code(findings: list[Finding], fail_on_warn: bool = False) -> int:
    if any(f.level == "FAIL" for f in findings):
        return 1
    if fail_on_warn and any(f.level == "WARN" for f in findings):
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Check session-memory TODO hygiene.")
    parser.add_argument("--session-memory", default=str(DEFAULT_SESSION_MEMORY))
    parser.add_argument("--backlog", default=str(DEFAULT_BACKLOG))
    parser.add_argument("--max-active", type=int, default=12)
    parser.add_argument("--max-line-chars", type=int, default=260)
    parser.add_argument("--fail-on-warn", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    findings, summary = analyze(
        session_memory=Path(args.session_memory),
        backlog=Path(args.backlog),
        max_active=args.max_active,
        max_line_chars=args.max_line_chars,
    )
    if args.json:
        print(
            json.dumps(
                {
                    "summary": summary,
                    "findings": [finding.__dict__ for finding in findings],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        for finding in findings:
            print(f"[{finding.level}] {finding.message}")
    return exit_code(findings, fail_on_warn=args.fail_on_warn)


if __name__ == "__main__":
    raise SystemExit(main())
