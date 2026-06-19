#!/usr/bin/env python3
"""
Daily Cron Audit — Cost & Delegation Pattern Summary
=====================================================
Reads .tmp/live-events.jsonl and produces a daily cost/delegation audit.
Output: .tmp/cost-audit-YYYY-MM-DD.json

Usage:
  python3 scripts/cron-audit.sh  (runs daily via cron)
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EVENTS_LOG = REPO_ROOT / ".tmp" / "live-events.jsonl"
AUDIT_DIR = REPO_ROOT / ".tmp"
AUDIT_FILE = AUDIT_DIR / f"cost-audit-{datetime.now().strftime('%Y-%m-%d')}.json"

# Estimated cost per 1K tokens (USD)
COST_PER_1K = {
    "gemini-2.5-flash": 0.00015,
    "deepseek-chat": 0.00027,
    "claude-haiku-4-5": 0.00080,
    "llama-3.3-70b": 0.00000,  # free via Groq
    "default": 0.00100,
}


def estimate_cost(model_id, chars):
    """Rough cost estimate from character count."""
    tokens = chars / 3.5  # rough chars→tokens
    rate = COST_PER_1K.get(model_id, COST_PER_1K["default"])
    return round(tokens / 1000 * rate, 6)


def main():
    if not EVENTS_LOG.exists():
        print(f"No events log at {EVENTS_LOG}")
        return

    cutoff = (datetime.now() - timedelta(hours=24)).timestamp()
    events = []
    with open(EVENTS_LOG, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                evt = json.loads(line)
                if evt.get("ts", 0) >= cutoff:
                    events.append(evt)
            except json.JSONDecodeError:
                continue

    if not events:
        print("No events in last 24 hours")
        return

    # Analyze patterns
    tool_counts = Counter()
    hook_blocks = 0
    delegation_count = 0
    read_chars = 0
    write_chars = 0
    error_events = 0

    for evt in events:
        etype = evt.get("type", "")

        if etype == "hook_check":
            if evt.get("result") == "block":
                hook_blocks += 1

        elif etype == "tool_use":
            tool_counts[evt.get("tool", "unknown")] += 1
            chars = len(json.dumps(evt))
            if evt.get("tool") in ("Read", "Glob", "Grep", "read_file", "search_files"):
                read_chars += chars
            else:
                write_chars += chars

        elif etype in ("delegate_spawn", "agent_spawn"):
            delegation_count += 1

        elif etype in ("error", "block", "fail"):
            error_events += 1

    # Read streak from waste state
    waste_state_file = REPO_ROOT / ".tmp" / "token_waste_state.json"
    read_streak = 0
    total_lines = 0
    if waste_state_file.exists():
        try:
            ws = json.loads(waste_state_file.read_text())
            read_streak = ws.get("read_streak", 0)
            total_lines = ws.get("total_lines_read", 0)
        except Exception:
            pass

    # Estimate costs
    total_chars = read_chars + write_chars
    est_cost = estimate_cost("default", total_chars)
    read_ratio = read_chars / max(total_chars, 1)

    audit = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "generated_at": datetime.now().isoformat(),
        "event_count": len(events),
        "tool_usage": dict(tool_counts.most_common(20)),
        "read_write_ratio": round(read_ratio, 3),
        "estimated_cost_usd": est_cost,
        "read_streak": read_streak,
        "total_lines_read": total_lines,
        "delegation_count": delegation_count,
        "hook_blocks": hook_blocks,
        "error_events": error_events,
        "warnings": [],
    }

    # Generate warnings
    if read_ratio > 0.85:
        audit["warnings"].append(
            f"High read ratio ({read_ratio:.0%}) — consider delegating read-heavy tasks"
        )
    if read_streak > 10:
        audit["warnings"].append(
            f"Read streak at {read_streak} without Write — context may be bloated"
        )
    if delegation_count == 0 and len(events) > 100:
        audit["warnings"].append(
            "No delegation in high-volume session — consider swarm for cost savings"
        )

    # Write audit
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_FILE, "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"📊 Daily cost audit → {AUDIT_FILE}")
    print(f"   Events: {len(events)} | Delegations: {delegation_count}")
    print(f"   Read/Write ratio: {read_ratio:.1%} | Est. cost: ${est_cost:.4f}")
    print(f"   Top tools: {dict(tool_counts.most_common(5))}")
    if audit["warnings"]:
        print(f"   ⚠️  Warnings:")
        for w in audit["warnings"]:
            print(f"      - {w}")


if __name__ == "__main__":
    main()
