#!/usr/bin/env python3
"""a_escalate.py — package a stuck problem into a prompt for a stronger model.

Renders a SELF-CONTAINED context pack: goal, constraints, what has already been
tried, the files involved, done-criteria, and the one question being asked. The
receiving model has none of this session's context, so anything left implicit is
simply lost — that is the whole failure mode this script exists to prevent.

Output goes to exports/escalate/<slug>.md (gitignored, ephemeral) and the path
is printed. Nothing is sent anywhere: the user copies it to whichever model they
want. Deliberate — escalation targets change faster than any hardcoded list.

Usage
-----
    python scripts/a_escalate.py --goal "..." --question "..." \
        [--constraint C]... [--tried T]... [--file F]... [--done D]... \
        [--no-ledger] [--stdout]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "exports" / "escalate"

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError, ValueError):
        pass


def slugify(text: str, maxlen: int = 48) -> str:
    """ASCII-safe filename stem. Thai goals are common, so fall back to a date."""
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    s = s[:maxlen].strip("-")
    return s or datetime.now().strftime("%Y%m%d-%H%M%S")


def recent_attempts(limit: int = 8) -> list[str]:
    """Pull prior failures/lessons from the Memory Ledger.

    "What did you already try" is the single most valuable field in an
    escalation and the one a human is least likely to write out in full.
    """
    ledger = REPO_ROOT / ".tmp" / "memory-ledger.jsonl"
    if not ledger.exists():
        return []
    out: list[str] = []
    try:
        for line in ledger.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if entry.get("type") not in ("failure", "lesson", "decision"):
                continue
            summary = _clean_summary(entry.get("summary") or "")
            if summary:
                out.append(f"[{entry.get('type')}] {summary}")
    except OSError:
        return []
    # De-duplicate while keeping order — the ledger repeats itself a lot.
    seen: set[str] = set()
    deduped = [s for s in out if not (s in seen or seen.add(s))]
    return deduped[-limit:]


def _clean_summary(summary: str) -> str:
    """First line only, capped, with shell/commit noise dropped.

    Some ledger entries are captured verbatim from commit commands, so their
    summary can be a whole multi-line message complete with heredoc markers.
    Pasting that into an escalation pack buries the real signal.
    """
    line = summary.strip().splitlines()[0].strip() if summary.strip() else ""
    if not line:
        return ""
    if line.startswith("$(") or "<<'EOF'" in line or line.startswith("git "):
        return ""
    if len(line) > 160:
        line = line[:157].rstrip() + "..."
    return line


def git_context() -> dict[str, str]:
    """Branch + recent commits, so the reviewer knows what changed lately."""
    def run(args: list[str]) -> str:
        try:
            r = subprocess.run(args, cwd=REPO_ROOT, capture_output=True,
                               text=True, encoding="utf-8", errors="replace", timeout=10)
            return r.stdout.strip() if r.returncode == 0 else ""
        except Exception:
            return ""
    return {
        "branch": run(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
        "recent": run(["git", "log", "--oneline", "-5"]),
        "dirty": run(["git", "status", "--porcelain"]),
    }


def read_excerpt(path: str, max_lines: int = 60) -> str:
    p = (REPO_ROOT / path) if not Path(path).is_absolute() else Path(path)
    try:
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        return f"(could not read {path}: {exc})"
    body = "\n".join(lines[:max_lines])
    if len(lines) > max_lines:
        body += f"\n... ({len(lines) - max_lines} more lines)"
    return body


def render(args: argparse.Namespace) -> str:
    git = git_context()
    tried = list(args.tried or [])
    if not args.no_ledger:
        tried += recent_attempts()

    L: list[str] = [
        "# Escalation request",
        "",
        "You are being asked to think through a problem that a coding agent got "
        "stuck on. Everything needed is below — you have no other context from "
        "that session.",
        "",
        "## The question",
        "",
        args.question.strip(),
        "",
        "## Goal",
        "",
        args.goal.strip(),
        "",
    ]

    if args.constraint:
        L += ["## Constraints (non-negotiable)", ""]
        L += [f"- {c}" for c in args.constraint]
        L += [""]

    if args.done:
        L += ["## Done criteria", ""]
        L += [f"- [ ] {d}" for d in args.done]
        L += [""]

    if tried:
        L += ["## Already tried (do not re-suggest these)", ""]
        L += [f"- {t}" for t in tried]
        L += [""]

    if args.file:
        L += ["## Relevant files", ""]
        for f in args.file:
            L += [f"### `{f}`", "", "```", read_excerpt(f), "```", ""]

    L += [
        "## Environment",
        "",
        f"- repo: A-Wiki (branch `{git['branch'] or 'unknown'}`)",
        f"- uncommitted changes: {'yes' if git['dirty'] else 'no'}",
        "",
    ]
    if git["recent"]:
        L += ["Recent commits:", "", "```", git["recent"], "```", ""]

    L += [
        "## What I want back",
        "",
        "1. Your reading of the ACTUAL root cause — say so plainly if the framing "
        "above is wrong.",
        "2. A concrete plan, in steps small enough to verify one at a time.",
        "3. For each step: how to prove it worked.",
        "4. Anything you would NOT do, and why.",
        "",
        "Be direct. If part of this is a bad idea, say that first.",
        "",
        "---",
        f"_generated {datetime.now().strftime('%Y-%m-%d %H:%M')} by "
        f"`scripts/a_escalate.py` (A-Wiki /A-Escalate)_",
    ]
    return "\n".join(L) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--goal", required=True, help="what you are trying to achieve")
    ap.add_argument("--question", required=True, help="the single question to ask")
    ap.add_argument("--constraint", action="append", help="repeatable")
    ap.add_argument("--tried", action="append", help="repeatable")
    ap.add_argument("--file", action="append", help="repeatable; excerpt is embedded")
    ap.add_argument("--done", action="append", help="repeatable; done criteria")
    ap.add_argument("--no-ledger", action="store_true",
                    help="do not pull prior attempts from the Memory Ledger")
    ap.add_argument("--stdout", action="store_true", help="print instead of writing a file")
    ap.add_argument("--slug", help="override the output filename stem")
    a = ap.parse_args(argv)

    content = render(a)
    if a.stdout:
        print(content)
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    gitignore = OUT_DIR / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(
            "# Escalation packs (ephemeral). Regenerated on demand; never source of truth.\n"
            "*\n!.gitignore\n",
            encoding="utf-8",
        )
    out = OUT_DIR / f"{a.slug or slugify(a.goal)}.md"
    out.write_text(content, encoding="utf-8")
    rel = out.relative_to(REPO_ROOT)
    print(f"📤 escalation pack -> {rel}  ({len(content)} chars)")
    print("   copy its contents into the stronger model; nothing was sent anywhere.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
