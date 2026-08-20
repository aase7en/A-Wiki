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

DEFAULT_BB_PATH = Path(
    os.environ.get("AWIKI_BLACKBOARD_PATH", str(REPO_ROOT / ".tmp" / "blackboard.jsonl"))
)
DEFAULT_LEDGER_PATH = Path(
    os.environ.get("AWIKI_MEMORY_LEDGER_PATH", str(REPO_ROOT / ".tmp" / "memory-ledger.jsonl"))
)


def check_unreviewed_councils(bb_path: Path | str = DEFAULT_BB_PATH) -> list[dict]:
    """Find auto-council threads tagged 'needs-review' that have NO perspectives yet.

    These are councils auto-opened by auto_council_trigger.py for sensitive
    edits that the user/agent forgot to actually run personas against.
    Returns list of {thread_id, topic, trigger_file} for un-reviewed councils.
    """
    import blackboard as _bb
    bb_path = Path(bb_path)
    if not bb_path.is_file():
        return []
    bb = _bb.Blackboard(bb_path)
    msgs = bb.read(limit=10000)
    # Find openers tagged needs-review
    openers = {}
    for m in msgs:
        tags = m.get("tags", [])
        if (m.get("type") == "proposal"
                and "needs-review" in tags
                and m.get("thread_id")):
            openers[m["thread_id"]] = {
                "thread_id": m["thread_id"],
                "topic": m.get("topic", m.get("body", "")[:60]),
                "trigger_file": m.get("trigger_file", "?"),
            }
    # Filter to those with zero perspectives
    unreviewed = []
    for tid, info in openers.items():
        thread_msgs = bb.read(thread_id=tid)
        has_perspective = any(
            m.get("type") == "answer" and "severity" in m
            for m in thread_msgs
        )
        if not has_perspective:
            unreviewed.append(info)
    return unreviewed


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


def _utf8_streams() -> None:
    """Force UTF-8. This hook prints ⛔ / ⚠️ / ✅ and had no preamble, so on a
    cp874 console every message raised UnicodeEncodeError inside the try below
    and was swallowed into a bare '[self-audit] error: ...' line."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass


def _emit(text: str) -> None:
    """Write where the user can actually see it.

    This hook is wired DIRECTLY on Stop, not through hooks_runner.py, which
    captures child stdout and re-emits stderr only on exit 2. self_audit always
    returns 0, so every warning it produced through the runner was discarded —
    the ship gate had never spoken to anyone since it landed.
    """
    sys.stdout.write(text)


def main() -> int:
    """Stop hook entry. Exits 0 always. Warns on critical + un-reviewed."""
    _utf8_streams()
    # Substring match, like every other hook. Exact equality meant
    # HOOK_SKIP="self_audit,check_apikey" silently failed to skip this one.
    if "self_audit" in os.environ.get("HOOK_SKIP", ""):
        return 0
    try:
        # Gate 1: critical findings → block
        gate = evaluate_ship_gate(DEFAULT_BB_PATH)
        if gate["block"]:
            n = record_findings_to_ledger(DEFAULT_LEDGER_PATH, DEFAULT_BB_PATH, gate)
            _emit(
                f"⛔ [self-audit] BLOCK SHIP — {gate['critical_count']} critical "
                f"finding(s) across {len(gate['councils'])} council(s). "
                f"Recorded {n} failure(s) to ledger.\n"
            )
            for c in gate["councils"]:
                _emit(
                    f"   council '{c['topic'][:50]}': "
                    f"{c['critical']} critical, {c['important']} important, "
                    f"{c['minor']} minor\n"
                )
            return 0

        # Gate 2: un-reviewed auto-councils → warn (not block)
        unreviewed = check_unreviewed_councils(DEFAULT_BB_PATH)
        if unreviewed:
            _emit(
                f"⚠️ [self-audit] {len(unreviewed)} council(s) need review "
                f"(auto-opened for sensitive edit but no perspectives posted):\n"
            )
            for u in unreviewed[:5]:  # cap output
                _emit(
                    f"   {u['thread_id']}: {u['trigger_file']} — "
                    f"run /A-Council or personas before ship\n"
                )

        # Quiet pass if there were councils that DID get reviewed
        councils = check_open_councils(DEFAULT_BB_PATH)
        if councils and not unreviewed:
            _emit(
                f"✅ [self-audit] {len(councils)} council(s) reviewed, "
                f"no critical findings. Safe to ship.\n"
            )
    except Exception as e:
        _emit(f"[self-audit] error: {e}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
