"""self_audit.py — Tier 2 #7 self-audit Stop hook.

Checks open council threads at session Stop:
  - If any council has_critical → block ship + record findings to ledger
  - Otherwise → pass (no-op)

Hook does NOT invoke personas itself (those run before Stop, e.g. via
/A-Council or Hermes parallel_fan_out). It only enforces the gate based
on council state already on disk.

ALWAYS exits 0 — it WARNS about critical findings, never hard-kills the
session. The "block" is advisory: agent/user sees the warning + recorded
failure entries and decides.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HOOKS_DIR.parent.parent
LIB_DIR = REPO_ROOT / "scripts" / "lib"

sys.path.insert(0, str(LIB_DIR))
sys.path.insert(0, str(HOOKS_DIR))

import council_persistent  # noqa: E402
import memory_ledger  # noqa: E402

DEFAULT_BB_PATH = REPO_ROOT / ".tmp" / "blackboard.jsonl"
DEFAULT_LEDGER_PATH = REPO_ROOT / ".tmp" / "memory-ledger.jsonl"


def check_open_councils(bb_path: Path | str = DEFAULT_BB_PATH) -> list[dict]:
    """Find council threads that have at least one perspective.

    Returns list of {thread_id, topic, summary} for councils with findings.
    """
    bb = council_persistent.blackboard.Blackboard(bb_path)
    if not Path(bb_path).is_file():
        return []
    # Council openers are type=proposal with tags containing 'council'
    all_msgs = bb.read(limit=10000)
    council_openers = {}
    for m in all_msgs:
        tags = m.get("tags", [])
        if m.get("type") == "proposal" and "council" in tags:
            council_openers[m["thread_id"]] = {
                "thread_id": m["thread_id"],
                "topic": m.get("topic", m.get("body", "")[:60]),
            }
    # Only return councils that have at least one perspective
    result = []
    for tid, info in council_openers.items():
        thread_msgs = bb.read(thread_id=tid)
        has_perspective = any(
            m.get("type") == "answer" and "severity" in m
            for m in thread_msgs
        )
        if has_perspective:
            result.append(info)
    return result


def evaluate_ship_gate(bb_path: Path | str = DEFAULT_BB_PATH) -> dict:
    """Check all open councils for critical findings.

    Returns {block: bool, critical_count: int, councils: [...]}.
    block=True if ANY council has a critical finding.
    """
    councils = check_open_councils(bb_path)
    council_obj = council_persistent.Council(bb_path)
    total_critical = 0
    detailed = []
    for c in councils:
        summary = council_obj.summarize(c["thread_id"])
        if summary["critical"] > 0:
            total_critical += summary["critical"]
            detailed.append({
                "thread_id": c["thread_id"],
                "topic": c["topic"],
                "critical": summary["critical"],
                "important": summary["important"],
                "minor": summary["minor"],
            })
    return {
        "block": total_critical > 0,
        "critical_count": total_critical,
        "councils": detailed,
    }


def record_findings_to_ledger(
    ledger_path: Path | str,
    bb_path: Path | str,
    gate: dict,
) -> int:
    """Write critical findings to the ledger as type=failure entries.

    Returns count of entries written. Only writes critical findings
    (minor/important are advisory, not failures).
    """
    if not gate["block"]:
        return 0
    ledger = memory_ledger.MemoryLedger(ledger_path)
    council_obj = council_persistent.Council(bb_path)
    written = 0
    for c in gate["councils"]:
        perspectives = council_obj._perspectives(c["thread_id"])
        for p in perspectives:
            if p["severity"] != "critical":
                continue
            ledger.append(
                session_id="self-audit",
                type="failure",
                summary=(
                    f"[self-audit BLOCK] {p['persona']}: {p['finding']} "
                    f"(council: {c['topic'][:50]})"
                ),
                tags=["self-audit", "critical", p["persona"]],
            )
            written += 1
    return written


def main() -> int:
    """Stop hook entry. Exits 0 always. Warns on critical."""
    if os.environ.get("HOOK_SKIP") == "self_audit":
        return 0
    try:
        gate = evaluate_ship_gate(DEFAULT_BB_PATH)
        if gate["block"]:
            n = record_findings_to_ledger(DEFAULT_LEDGER_PATH, DEFAULT_BB_PATH, gate)
            sys.stderr.write(
                f"⛔ [self-audit] BLOCK SHIP — {gate['critical_count']} critical "
                f"finding(s) across {len(gate['councils'])} council(s). "
                f"Recorded {n} failure(s) to ledger.\n"
            )
            for c in gate["councils"]:
                sys.stderr.write(
                    f"   council '{c['topic'][:50]}': "
                    f"{c['critical']} critical, {c['important']} important, "
                    f"{c['minor']} minor\n"
                )
        else:
            # Quiet pass — only emit if there were councils at all
            councils = check_open_councils(DEFAULT_BB_PATH)
            if councils:
                sys.stderr.write(
                    f"✅ [self-audit] {len(councils)} council(s) reviewed, "
                    f"no critical findings. Safe to ship.\n"
                )
    except Exception as e:
        sys.stderr.write(f"[self-audit] error: {e}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
