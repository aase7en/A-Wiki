"""council_persistent.py — blackboard-backed async multi-persona council.

Tier 2 #8. Makes the A-Wiki "council" (multi-perspective review) persistent:
personas (code-reviewer/test-engineer/security-auditor/web-performance-auditor)
post their findings into a blackboard thread that survives across sessions
and renders in the dashboard.

ปัจจุบัน council เป็น ephemeral (ผลหายหลัง session). Persistent version
writes to blackboard.jsonl → cross-session + observable + resumable.

Used by:
  - Tier 2 #7 self-audit hook (Stop → council → block if critical)
  - Manual /A-Council "<topic>" invocation

Schema (extends blackboard message with council-specific fields):
  opener:       {type:proposal, tags:[council], participants:[...], topic}
  perspective:  {type:answer, tags:[council], persona, finding, severity}

Writes directly via atomic_json.atomic_append_jsonl (not bb.post/reply)
so we can attach the extra structured fields (severity, persona, topic,
participants) that the plain blackboard schema doesn't carry.
"""
from __future__ import annotations

import sys
import time
import uuid
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import atomic_json  # noqa: E402 -- chunk 1
import blackboard  # noqa: E402 -- chunk 4 (for read() compatibility)

VALID_SEVERITIES = {"critical", "important", "minor"}


def _new_id() -> str:
    return f"m{int(time.time() * 1000)}-{uuid.uuid4().hex[:6]}"


class Council:
    """Async multi-persona council backed by blackboard.jsonl."""

    def __init__(self, bb_path: Path | str):
        self.bb = blackboard.Blackboard(bb_path)
        self.path = self.bb.path

    def _append(self, entry: dict) -> str:
        """Append a council message with extra fields."""
        atomic_json.atomic_append_jsonl(self.path, entry)
        return entry["id"]

    def open(self, *, topic: str, participants: list[str]) -> str:
        """Open a council thread. Returns thread_id.

        The opener is a 'proposal' message addressed to all participants
        (broadcast) with tags=[council] so it's filterable. Carries the
        topic + participant list as structured fields.
        """
        msg_id = _new_id()
        body = f"COUNCIL TOPIC: {topic}\nParticipants: {', '.join(participants)}"
        entry = {
            "ts": time.time(),
            "id": msg_id,
            "from": "council-orchestrator",
            "to": "*",
            "type": "proposal",
            "body": body,
            "thread_id": msg_id,  # opener is its own thread root
            "tags": ["council"],
            "topic": topic,
            "participants": list(participants),
        }
        return self._append(entry)

    def post_perspective(
        self,
        *,
        thread_id: str,
        persona: str,
        finding: str,
        severity: str,
    ) -> str:
        """A persona adds its finding to the council thread.

        Severity must be one of: critical, important, minor.
        Stored as a blackboard-style answer with extra structured fields
        persona + severity + finding.
        """
        if severity not in VALID_SEVERITIES:
            raise ValueError(
                f"invalid severity {severity!r}; must be one of {sorted(VALID_SEVERITIES)}"
            )
        msg_id = _new_id()
        body = f"[{severity.upper()}] ({persona}) {finding}"
        entry = {
            "ts": time.time(),
            "id": msg_id,
            "from": persona,
            "to": "*",
            "type": "answer",
            "body": body,
            "thread_id": thread_id,
            "tags": ["council"],
            "persona": persona,
            "finding": finding,
            "severity": severity,
        }
        return self._append(entry)

    def _perspectives(self, thread_id: str) -> list[dict]:
        """Extract perspective entries (type=answer with severity field)."""
        msgs = self.bb.read(thread_id=thread_id)
        return [m for m in msgs if m.get("type") == "answer" and "severity" in m]

    def summarize(self, thread_id: str) -> dict[str, Any]:
        """Aggregate findings by severity. Returns count dict."""
        perspectives = self._perspectives(thread_id)
        counts = {"critical": 0, "important": 0, "minor": 0}
        for p in perspectives:
            sev = p["severity"]
            if sev in counts:
                counts[sev] += 1
        counts["total_findings"] = len(perspectives)
        return counts

    def has_critical(self, thread_id: str) -> bool:
        """Quick check: does this council have any critical finding?

        Used by self-audit hook to decide whether to block ship.
        """
        return self.summarize(thread_id)["critical"] > 0
