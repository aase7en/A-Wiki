#!/usr/bin/env python3
"""Validate A-Wiki cross-agent handoff documents.

Default mode is advisory: schema issues warn but exit 0. Secret-looking tokens
always fail. Use --strict to make schema issues fail.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
try:
    from scripts.hooks.check_secret_leak import scan_text as hook_scan_text
except Exception:  # pragma: no cover - fallback is for minimal copied test repos.
    hook_scan_text = None

PLACEHOLDER_MARKERS = (
    "replace this line",
    "not exported yet",
    "define the smallest",
    "path/to/file",
    "not exported",
    "unknown",
    "todo here",
    "tbd",
    "xxx",
)
VALID_STATUSES = {"todo", "doing", "done", "blocked", "skipped"}


@dataclass(frozen=True)
class SecretPattern:
    name: str
    regex: re.Pattern[str]


# Fallback mirror of scripts/hooks/check_secret_leak.py for minimal handoff test
# repos where hooks are not copied.
SECRET_PATTERNS = [
    SecretPattern("OpenAI/Anthropic/OpenRouter style key", re.compile(r"\bsk-[A-Za-z0-9_-]{24,}\b")),
    SecretPattern("OpenRouter v1 key", re.compile(r"\bsk-or-v1-[A-Za-z0-9_-]{24,}\b")),
    SecretPattern("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b")),
    SecretPattern("Groq API key", re.compile(r"\bgsk_[0-9A-Za-z]{24,}\b")),
    SecretPattern("GitHub classic token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{30,}\b")),
    SecretPattern("GitHub fine-grained token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{40,}\b")),
    SecretPattern("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    SecretPattern("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    SecretPattern("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
]
SECRET_PLACEHOLDER_MARKERS = ("...", "example", "placeholder", "your_", "your-", "xxxx", "<", ">", "test", "demo", "sample", "redacted")


def is_secret_placeholder(token: str) -> bool:
    lower = token.lower()
    return any(marker in lower for marker in SECRET_PLACEHOLDER_MARKERS)


def redact(token: str) -> str:
    if len(token) <= 12:
        return "***"
    return f"{token[:6]}...{token[-4:]}"


def scan_secrets(text: str) -> list[str]:
    if hook_scan_text is not None:
        return hook_scan_text(text, "handoff")

    hits: list[str] = []
    for pattern in SECRET_PATTERNS:
        for match in pattern.regex.finditer(text):
            token = match.group(0)
            if not is_secret_placeholder(token):
                hits.append(f"{pattern.name}: {redact(token)}")
    return hits


def section(text: str, heading: str) -> str | None:
    pattern = re.compile(rf"^## {re.escape(heading)}\s*$([\s\S]*?)(?=^## |\Z)", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return None
    return match.group(1).strip()


def has_placeholder(value: str) -> bool:
    lower = value.strip().lower()
    if not lower or lower in {"-", "none", "n/a"}:
        return True
    return any(marker in lower for marker in PLACEHOLDER_MARKERS)


def split_markdown_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def task_rows(text: str) -> list[list[str]]:
    board = section(text, "Task Board")
    if not board:
        return []
    rows: list[list[str]] = []
    for line in board.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = split_markdown_row(stripped)
        if len(cells) != 6:
            continue
        first = cells[0].lower()
        if first in {"id", "---"} or set(first) <= {"-"}:
            continue
        if all(set(cell) <= {"-", " "} for cell in cells):
            continue
        rows.append(cells)
    return rows


def blocked_ids_with_details(text: str) -> set[str]:
    blocked = section(text, "Blocked") or ""
    ids: set[str] = set()
    for line in blocked.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = split_markdown_row(stripped)
        if len(cells) < 3 or cells[0].lower() in {"chunk", "---"}:
            continue
        if cells[0] != "-" and not has_placeholder(cells[1]) and not has_placeholder(cells[2]):
            ids.add(cells[0])
    return ids


def validate_schema(text: str) -> list[str]:
    issues: list[str] = []

    resume = section(text, "Resume Here")
    if resume is None:
        issues.append("Missing required section: Resume Here")
    else:
        next_lines = [line for line in resume.splitlines() if "**Next action**" in line]
        if len(next_lines) != 1:
            issues.append("Resume Here must contain exactly one **Next action** line")
        elif has_placeholder(next_lines[0].split(":", 1)[-1]):
            issues.append("Resume Here next action is empty or placeholder text")
        if "**Verify**" not in resume:
            issues.append("Resume Here must include **Verify** with the cheapest validation command")
        if "**Canonical source**" not in resume:
            issues.append("Resume Here must include **Canonical source**")
        if "**Do not redo**" not in resume:
            issues.append("Resume Here must include **Do not redo**")

    for required in ("Exact Resume Command", "Suggested Skills", "Cost Tier Snapshot", "Failed Approaches", "Key Decisions", "Open Decisions"):
        body = section(text, required)
        if body is None:
            issues.append(f"Missing required section: {required}")
        elif not body.strip():
            issues.append(f"Section is empty: {required}")

    rows = task_rows(text)
    if not rows:
        issues.append("Task Board must contain at least one non-placeholder row")
    blockers = blocked_ids_with_details(text)
    for row in rows:
        chunk_id, status, goal, files, verify, note = row
        if has_placeholder(chunk_id):
            issues.append("Task Board row has placeholder ID")
        if status.lower() not in VALID_STATUSES:
            issues.append(f"Task Board row {chunk_id} has invalid status: {status}")
        for label, value in (("goal", goal), ("files", files), ("verify", verify), ("handoff note", note)):
            if has_placeholder(value):
                issues.append(f"Task Board row {chunk_id} has empty or placeholder {label}")
        if status.lower() == "blocked" and chunk_id not in blockers:
            issues.append(f"Task Board row {chunk_id} is blocked but has no blocker details")

    return issues


def resolve_path(args: argparse.Namespace) -> Path:
    if args.template:
        return REPO_ROOT / "handoff.md.example"
    if args.path:
        return Path(args.path)
    return Path("handoff.md")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate A-Wiki cross-agent handoff files.")
    parser.add_argument("--path", help="Handoff file path. Defaults to handoff.md.")
    parser.add_argument("--template", action="store_true", help="Validate tracked handoff.md.example.")
    parser.add_argument("--strict", action="store_true", help="Fail on schema warnings.")
    args = parser.parse_args()

    path = resolve_path(args)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        sys.stderr.write(f"handoff check failed: cannot read {path}: {exc}\n")
        return 1 if args.strict else 0

    secret_hits = scan_secrets(text)
    if secret_hits:
        sys.stderr.write("BLOCKED: possible secret leak detected in handoff\n\n")
        sys.stderr.write("\n".join(f"- {hit}" for hit in secret_hits[:20]) + "\n")
        return 2

    issues = validate_schema(text)
    if issues:
        sys.stderr.write("handoff check warnings:\n")
        sys.stderr.write("\n".join(f"- {issue}" for issue in issues) + "\n")
        return 1 if args.strict else 0

    print(f"handoff check OK: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
