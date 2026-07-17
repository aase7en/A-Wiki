"""blackboard.py — async messaging channel between A-Wiki agents.

Neural Spine primitive #3 (built on atomic_json).

Blackboard คือช่องคุยระหว่าง agent ของสมอง A-Wiki. ทำให้ Claude Code,
Codex, Gemini CLI, Cline (และ agent อนาคต) สามารถ:
  - ถาม/ตอบกัน (question/answer)
  - @mention เพื่อส่งตรง
  - broadcast ('*') สำหรับข้อความทั่วไป
  - เก็บเป็น thread (เหมือน forum) โดยใช้ thread_id

Schema (JSONL, 1 บรรทัดต่อ message):
  {
    "ts": float,
    "id": str,           # unique per message, monotonic-ish
    "from": str,         # claude|codex|gemini|cline|user|<custom>
    "to": str,           # claude|codex|gemini|cline|user|*  (broadcast)
    "type": str,         # msg|question|proposal|answer
    "body": str,
    "thread_id": str|null,  # link to root message of the thread
  }

API:
  Blackboard(path).post(frm, to, body, msg_type='msg', thread_id=None)
  .reply(thread_id, frm, body, msg_type='answer')
  .read(since_ts=0, thread_id=None, to_filter=None)
  .extract_mentions(body)  # helper for @mention UI highlighting

Reuses atomic_json.atomic_append_jsonl (chunk 1) — concurrent-safe.
The Live Dashboard will render these messages in scripts/live-dashboard/src/chat.js
(which already exists as an empty UI shell).
"""
from __future__ import annotations

import json
import re
import sys
import time
import uuid
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import atomic_json  # noqa: E402 -- sibling primitive (chunk 1)

VALID_TYPES = {"msg", "question", "proposal", "answer"}
VALID_AGENTS = {"claude", "codex", "gemini", "cline", "user"}  # not enforced — just convention
MENTION_RE = re.compile(r"@([a-zA-Z][a-zA-Z0-9_\-]*)")


class Blackboard:
    """Async message channel between agents. Append-only, lock-protected."""

    def __init__(self, path: Path | str):
        self.path = Path(path)

    def post(
        self,
        *,
        frm: str,
        to: str,
        body: str,
        msg_type: str = "msg",
        thread_id: str | None = None,
    ) -> str:
        """Post one message. Returns the new message's id.

        Validates msg_type. Generates a unique id. Appends atomically.
        """
        if msg_type not in VALID_TYPES:
            raise ValueError(
                f"invalid msg_type {msg_type!r}; must be one of {sorted(VALID_TYPES)}"
            )
        if not frm or not isinstance(frm, str):
            raise ValueError("frm (sender) is required")
        if not to or not isinstance(to, str):
            raise ValueError("to (recipient or '*') is required")
        ts = time.time()
        msg_id = f"m{int(ts * 1000)}-{uuid.uuid4().hex[:6]}"
        # If this is a thread root (no thread_id given), make it its own thread_id.
        # This makes read(thread_id=X) return the root + all replies uniformly.
        effective_thread_id = thread_id if thread_id is not None else msg_id
        entry: dict[str, Any] = {
            "ts": ts,
            "id": msg_id,
            "from": frm,
            "to": to,
            "type": msg_type,
            "body": body or "",
            "thread_id": effective_thread_id,
        }
        atomic_json.atomic_append_jsonl(self.path, entry)
        return msg_id

    def reply(
        self,
        *,
        thread_id: str,
        frm: str,
        body: str,
        msg_type: str = "answer",
    ) -> str:
        """Reply to a thread. Same as post() but msg_type defaults to 'answer'
        and thread_id is forced to the parent thread.

        Robust to the thread_id not existing (agent may reply after a restart
        that lost the original thread id) — still writes the reply.
        """
        return self.post(
            frm=frm,
            to="*",  # reply is broadcast within the thread by default
            body=body,
            msg_type=msg_type,
            thread_id=thread_id,
        )

    def read(
        self,
        *,
        since_ts: float = 0.0,
        thread_id: str | None = None,
        to_filter: str | None = None,
        limit: int = 200,
    ) -> list[dict]:
        """Read messages, oldest-first, with optional filters.

        - since_ts:   only messages with ts >= this
        - thread_id:  only messages in this thread
        - to_filter:  only messages where 'to' == this agent OR 'to' == '*'
        - limit:      cap on returned messages (newest N)
        """
        if not self.path.is_file():
            return []
        out: list[dict] = []
        for line in self.path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            if since_ts and msg.get("ts", 0) < since_ts:
                continue
            if thread_id is not None and msg.get("thread_id") != thread_id:
                continue
            if to_filter is not None:
                msg_to = msg.get("to", "")
                if msg_to != to_filter and msg_to != "*":
                    continue
            out.append(msg)
        if limit > 0 and len(out) > limit:
            out = out[-limit:]
        return out

    @staticmethod
    def extract_mentions(body: str) -> list[str]:
        """Return list of agent names mentioned via @name in the body.

        Helper for the chat UI to highlight mentions. Pure function — no I/O.
        """
        if not body:
            return []
        return [m.lower() for m in MENTION_RE.findall(body)]
