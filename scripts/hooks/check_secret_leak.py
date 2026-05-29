#!/usr/bin/env python3
"""
Hook: Secret Leak Guard
-----------------------
Blocks tool calls and git commits that contain real-looking secrets.

This is broader than `check_apikey.py`: it scans the hook payload and, for
commit/push commands, the staged diff. It intentionally allows obvious
placeholders used in documentation.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Pattern:
    name: str
    regex: re.Pattern[str]


SECRET_PATTERNS = [
    Pattern("OpenAI/Anthropic/OpenRouter style key", re.compile(r"\bsk-[A-Za-z0-9_-]{24,}\b")),
    Pattern("OpenRouter v1 key", re.compile(r"\bsk-or-v1-[A-Za-z0-9_-]{24,}\b")),
    Pattern("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b")),
    Pattern("Groq API key", re.compile(r"\bgsk_[0-9A-Za-z]{24,}\b")),
    Pattern("GitHub classic token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{30,}\b")),
    Pattern("GitHub fine-grained token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{40,}\b")),
    Pattern("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    Pattern("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    Pattern("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
]

PLACEHOLDER_MARKERS = [
    "...",
    "example",
    "placeholder",
    "redacted",
    "your_",
    "your-",
    "xxxx",
    "<",
    ">",
    "test",
    "demo",
    "sample",
]


def _flatten(value: Any) -> str:
    """Turn hook JSON into text without caring about its schema."""
    if isinstance(value, dict):
        return "\n".join(_flatten(v) for v in value.values())
    if isinstance(value, list):
        return "\n".join(_flatten(v) for v in value)
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return ""


def _is_placeholder(token: str) -> bool:
    lower = token.lower()
    return any(marker in lower for marker in PLACEHOLDER_MARKERS)


def _redact(token: str) -> str:
    if len(token) <= 12:
        return "***"
    return f"{token[:6]}...{token[-4:]}"


def scan_text(text: str, source: str) -> list[str]:
    hits: list[str] = []
    for pattern in SECRET_PATTERNS:
        for match in pattern.regex.finditer(text):
            token = match.group(0)
            if _is_placeholder(token):
                continue
            hits.append(f"{source}: {pattern.name}: {_redact(token)}")
    return hits


def _looks_like_git_write(command: str) -> bool:
    return bool(re.search(r"\bgit\s+(commit|push)\b", command))


def _staged_diff() -> str:
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--no-ext-diff"],
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout


def main() -> int:
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        return 0

    payload_text = _flatten(input_data)
    hits = scan_text(payload_text, "hook payload")

    command = ""
    if isinstance(input_data, dict):
        tool_input = input_data.get("tool_input", {})
        if isinstance(tool_input, dict):
            command = str(tool_input.get("command", ""))

    if command and _looks_like_git_write(command):
        staged = _staged_diff()
        hits.extend(scan_text(staged, "staged diff"))

    if not hits:
        return 0

    sys.stderr.write(
        "BLOCKED: possible secret leak detected\n\n"
        + "\n".join(f"- {hit}" for hit in hits[:20])
        + "\n\n"
        + "Move secrets to Drive `.secrets` or environment variables, then retry.\n"
        + "Only redacted prefixes/suffixes are shown above.\n"
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
