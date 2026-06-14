#!/usr/bin/env python3
"""
scripts/crew-dispatch.py — Backward-compatible shim for Sanji's Kitchen crew dispatch.

This replaces the old model-name-based crew (Nami/Robin/Luffy/Franky) with
capability-role delegation via scripts/swarm/delegate.sh.

The old crew mapping was:
  Nami   (Gemini)    → search, lookup, url tasks
  Robin  (DeepSeek)  → analyze, compare, reason tasks
  Luffy  (Groq)      → scan, lint, execute tasks
  Franky (OpenRouter) → fallback / race

New: delegate.sh handles routing automatically by task_type — no model names in config.

Usage:
  python3 scripts/crew-dispatch.py --task "search:<query>"
  python3 scripts/crew-dispatch.py --task "reason:<question>"
  python3 scripts/crew-dispatch.py --task "summarize:<text>"
  python3 scripts/crew-dispatch.py --task "scan:<description>"
  python3 scripts/crew-dispatch.py --task "compare:<a> vs <b>"
  python3 scripts/crew-dispatch.py --task "race:<prompt>"    # parallel race all free models
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DELEGATE_SH = REPO_ROOT / "scripts" / "swarm" / "delegate.sh"

# Map old crew names to task_types (for legacy callers)
CREW_ALIAS_MAP: dict[str, str] = {
    "nami": "search",
    "robin": "reason",
    "luffy": "scan",
    "franky": "race",
    "zoro": "compare",
    "usopp": "lookup",
}

# Map task prefix to task_type
TASK_TYPE_MAP: dict[str, str] = {
    "search": "search",
    "lookup": "lookup",
    "url": "search",
    "analyze": "reason",
    "analyse": "reason",
    "reason": "reason",
    "compare": "compare",
    "scan": "scan",
    "lint": "scan",
    "execute": "scan",
    "summarize": "summarize",
    "summary": "summarize",
    "race": "race",
}


def parse_task(task_str: str) -> tuple[str, str]:
    """
    Parse --task argument into (task_type, prompt).
    Formats: "search:query" or "nami:query" or "query" (defaults to search)
    """
    if ":" in task_str:
        prefix, _, prompt = task_str.partition(":")
        prefix = prefix.strip().lower()
        prompt = prompt.strip()
        # Resolve crew alias first, then task type
        task_type = CREW_ALIAS_MAP.get(prefix, TASK_TYPE_MAP.get(prefix, "search"))
        return task_type, prompt
    # No prefix — default to search
    return "search", task_str.strip()


def dispatch(task_type: str, prompt: str, json_output: bool = False) -> int:
    """Call delegate.sh with the given task_type and prompt."""
    if not DELEGATE_SH.exists():
        msg = f"delegate.sh not found at {DELEGATE_SH}"
        if json_output:
            print(json.dumps({"error": msg}))
        else:
            print(f"❌ {msg}", file=sys.stderr)
        return 1

    try:
        result = subprocess.run(
            ["bash", str(DELEGATE_SH), task_type, prompt],
            capture_output=not json_output,
            text=True,
            timeout=90,
            cwd=str(REPO_ROOT),
        )
        if json_output and result.returncode != 0:
            print(json.dumps({"error": result.stderr.strip(), "code": result.returncode}))
        elif json_output and result.returncode == 0:
            print(json.dumps({"result": result.stdout.strip()}))
        elif result.returncode != 0:
            sys.stderr.write(result.stderr or "delegate.sh failed\n")
        return result.returncode
    except subprocess.TimeoutExpired:
        msg = "delegate.sh timed out after 90s"
        if json_output:
            print(json.dumps({"error": msg}))
        else:
            print(f"❌ {msg}", file=sys.stderr)
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Backward-compatible crew dispatch shim → routes via delegate.sh"
    )
    parser.add_argument(
        "--task",
        required=True,
        help='Task in format "type:prompt" or "prompt". Type: search|lookup|reason|compare|scan|race',
    )
    parser.add_argument("--json", action="store_true", dest="json_output", help="JSON output")
    parser.add_argument(
        "--crew",
        help="(Legacy) crew member name — mapped to task_type automatically",
    )
    args = parser.parse_args()

    task_str = args.task
    if args.crew:
        crew = args.crew.lower()
        task_type = CREW_ALIAS_MAP.get(crew, "search")
        sys.exit(dispatch(task_type, task_str, args.json_output))

    task_type, prompt = parse_task(task_str)
    sys.exit(dispatch(task_type, prompt, args.json_output))


if __name__ == "__main__":
    main()
