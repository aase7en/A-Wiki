#!/usr/bin/env python3
"""
persona-orchestrator.py — realize "subagent fan-out" as a SEQUENTIAL pass.
=========================================================================

Hermes has NO native subagent / parallel fan-out capability (no ``/task``
command; ``parallel_fan_out`` in ``lifecycle-config.json`` is aspirational).
This orchestrator emulates fan-out by running one ``hermes chat -q --persona
<name> "$TASK"`` call per persona, in sequence, then merging the outputs into
a single triaged report.

THIS IS SEQUENTIAL, NOT PARALLEL.  There is no concurrency, by framework
design.  Free-tier Pi5 models (DeepSeek V4-Flash, Gemini-Flash-Lite) are
rate-limited at 15-30 RPM, so sequential is also the only realistic option.

Design principles (adapted from Dan Martell's "Replacement Ladder"):
  - Draft, do not send — the orchestrator produces a draft report for the
    human to review (10-20% final polish), never auto-ships.
  - One sharp question, not a guess — each persona is told to ask one
    clarifying question when unsure rather than fabricating.
  - Triage + merge — outputs are sorted by severity (critical/important/low),
    mirroring an inbox triage (Urgent/Delegate/FYI).
  - Act-without-asking low-stakes / ask-on high-stakes — ``--dry-run``
    (default) never calls Hermes; ``--apply`` does.

Pure functions (``build_plan``, ``load_personas``, ``run``, ``merge_report``)
are import-safe and unit-tested without subprocess.  The default runner
spawns ``hermes`` via subprocess; tests inject a stub.

Usage
-----
::

    # Default: dry-run, print the plan as JSON (CI-safe, no Hermes call).
    python scripts/hermes/persona-orchestrator.py --task "review PR #42"

    # Override the persona set.
    python scripts/hermes/persona-orchestrator.py \\
        --personas code-reviewer,test-engineer \\
        --task "review PR #42"

    # Run for real (sequentially calls hermes chat).
    python scripts/hermes/persona-orchestrator.py --apply --task "..."

    # Read personas from lifecycle-config.json (default).
    python scripts/hermes/persona-orchestrator.py --task "..." # auto-loads

Exit codes
----------
- 0 = success (plan printed in dry-run, or run completed)
- 1 = misconfiguration (lifecycle-config missing/unreadable, empty personas)

See: docs/architecture/hermes-cross-agent-handoff.md (Chunk B)
     skills/awiki/hermes-fan-out/SKILL.md
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable

# Default inter-call sleep (seconds). Free-tier models allow ~15-30 RPM = one
# call every 2-4s; 4s is the safe floor that avoids 429 throttling on Pi5.
DEFAULT_SLEEP_S = 4

# Severity order for triage: highest first. Lines tagged with an earlier
# severity must appear before later ones in the merged report. Mirrors
# lifecycle-config.json "merge_on": ["critical", "important"].
DEFAULT_SEVERITIES = ["critical", "important", "low"]

# Hermes CLI invocation contract (documented at runbooks/hermes-raspberry-pi5.md
# and awiki-init-pi5.sh:180). The task is the LAST argv element as one string.
HERMES_CMD = "hermes"


def build_plan(personas: list[str], task: str, sleep_s: int) -> dict[str, Any]:
    """Construct an execution plan WITHOUT running anything.

    The plan is a JSON-serializable dict with:
      - ``calls``: list of ``{persona, argv}`` in persona order.
      - ``sleeps``: list of sleep durations BETWEEN calls (length = n_personas - 1).

    Pure function: no subprocess, no I/O.  This is what unit tests assert.
    """
    calls = [
        {
            "persona": name,
            "argv": [HERMES_CMD, "chat", "-q", "--persona", name, task],
        }
        for name in personas
    ]
    # n personas → n-1 inter-call sleeps (no trailing sleep after the last call).
    sleeps = [sleep_s for _ in range(max(0, len(personas) - 1))]
    return {"calls": calls, "sleeps": sleeps}


def load_personas(config_path: Path | str) -> list[str]:
    """Read the ``personas.parallel_fan_out`` list from a lifecycle config.

    Returns an empty list (not an error) when the key is absent or empty —
    callers decide whether an empty persona set is fatal (CLI does: exit 1).
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []
    return list(data.get("personas", {}).get("parallel_fan_out", []) or [])


def run(
    plan: dict[str, Any],
    runner: Callable[[list[str]], str] | None = None,
) -> dict[str, Any]:
    """Execute a plan sequentially, returning a merged report.

    ``runner`` is a callable ``(argv) -> stdout_str``.  The default runner
    shells out to ``hermes`` via subprocess; tests inject a stub that returns
    canned output without spawning anything.

    Returns ``{"persona_outputs": {persona: str}, "merged": str}``.
    """
    if runner is None:
        runner = _default_runner

    persona_outputs: dict[str, str] = {}
    calls = plan["calls"]
    sleeps = plan["sleeps"]

    for i, call in enumerate(calls):
        persona_outputs[call["persona"]] = runner(call["argv"])
        # Sleep between calls, not after the last.
        if i < len(sleeps):
            time.sleep(sleeps[i])

    merged = merge_report(persona_outputs, severities=DEFAULT_SEVERITIES)
    return {"persona_outputs": persona_outputs, "merged": merged}


def _default_runner(argv: list[str]) -> str:
    """Real runner: shell out to the hermes CLI and capture stdout."""
    result = subprocess.run(argv, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return f"[error: hermes exited {result.returncode}] {result.stderr.strip()}"
    return result.stdout.strip()


def merge_report(
    persona_outputs: dict[str, str], severities: list[str] | None = None
) -> str:
    """Triage + merge per-persona outputs into one severity-sorted report.

    Mirrors an inbox triage: every line carrying a known severity tag is
    grouped under that severity (highest first); untagged lines follow.
    """
    if severities is None:
        severities = DEFAULT_SEVERITIES
    if not persona_outputs:
        return ""

    # Collect every non-empty line across personas, with its source label.
    all_lines: list[tuple[str, str]] = []  # (line, persona)
    for persona, output in persona_outputs.items():
        for line in output.splitlines():
            line = line.strip()
            if line:
                all_lines.append((line, persona))

    # Bucket each line by the FIRST severity tag it contains (case-insensitive).
    buckets: dict[str, list[tuple[str, str]]] = {sev: [] for sev in severities}
    unclassified: list[tuple[str, str]] = []
    for line, persona in all_lines:
        lowered = line.lower()
        placed = False
        for sev in severities:
            if sev in lowered:
                buckets[sev].append((line, persona))
                placed = True
                break
        if not placed:
            unclassified.append((line, persona))

    # Emit each severity section in order, then unclassified.
    sections: list[str] = []
    for sev in severities:
        entries = buckets[sev]
        if not entries:
            continue
        sections.append(f"## {sev.upper()} ({len(entries)})")
        for line, persona in entries:
            sections.append(f"- [{persona}] {line}")
    if unclassified:
        sections.append(f"## OTHER ({len(unclassified)})")
        for line, persona in unclassified:
            sections.append(f"- [{persona}] {line}")

    return "\n".join(sections)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__.splitlines()[1] if __doc__ else "Persona orchestrator.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--task", required=True,
        help="The task/question to pass to every persona.",
    )
    ap.add_argument(
        "--personas",
        help="Comma-separated persona names (default: read from lifecycle-config.json).",
    )
    ap.add_argument(
        "--config",
        default=str(Path(__file__).parent / "lifecycle-config.json"),
        help="Path to lifecycle-config.json (used when --personas is not given).",
    )
    ap.add_argument(
        "--sleep", type=int, default=DEFAULT_SLEEP_S,
        help=f"Seconds between persona calls (default: {DEFAULT_SLEEP_S}; "
             f"respects free-tier 15-30 RPM).",
    )
    ap.add_argument(
        "--apply", action="store_true",
        help="Run the plan for real (default: dry-run, print plan as JSON).",
    )
    ap.add_argument(
        "--json", action="store_true",
        help="In --apply mode, emit the final report as JSON.",
    )
    a = ap.parse_args()

    personas = (
        [p.strip() for p in a.personas.split(",") if p.strip()]
        if a.personas
        else load_personas(a.config)
    )
    if not personas:
        print(
            "🚨 No personas to run. Provide --personas or ensure "
            "lifecycle-config.json has personas.parallel_fan_out.",
            file=sys.stderr,
        )
        return 1

    plan = build_plan(personas, a.task, sleep_s=a.sleep)

    if not a.apply:
        # Dry-run: print the plan, exit 0. No Hermes call.
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        print(
            f"\n[dry-run] {len(plan['calls'])} persona call(s) planned, "
            f"{len(plan['sleeps'])} inter-call sleep(s) of {a.sleep}s. "
            "Re-run with --apply to execute.",
            file=sys.stderr,
        )
        return 0

    report = run(plan)
    if a.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(report["merged"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
