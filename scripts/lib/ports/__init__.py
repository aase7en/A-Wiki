"""ports — outbound port interfaces for the Neural Spine MCP application.

ADR-0012 slice A4 (2026-08-01): the FIRST hexagonal extraction in A-Wiki.
This module is the canonical reference for how ports are declared in this
repo — every future slice (A1, A2, ...) should mirror this shape.

What is a port?
    A purpose-driven contract (NOT technology-named) between the application
    core (the MCP tool wrappers in neural_spine_mcp.py) and the external
    primitives it depends on. Per Cockburn: "ports model capabilities, not
    technologies."

Dependency direction (the Iron Rule of hexagonal architecture):
    adapters ──▶ ports ──▶ application
    Domain/ports NEVER import an adapter or a concrete technology.

Why these 6 ports?
    neural_spine_mcp.py delegates to 6 distinct primitives today:
    MemoryLedger, Blackboard, TaskBoard, agent_claims, a_flow_state-shaped
    focus files, and the skills routing module. Each becomes one port so the
    underlying store can be swapped (prod JSON file ↔ in-memory mock) without
    touching the tool wrappers.

Naming convention (binding for all future slices):
    - Port interfaces are `Protocol` classes named `<Capability>Port`.
    - Methods describe the capability verb, never the storage technology.
      (e.g. `recall`, not `search_jsonl`; `post`, not `append_line`.)
    - Ports return plain data (dict / list / scalar) — never file handles,
      sqlite rows, or ORM objects.

See:
    - wiki/concepts/ai-tools/hexagonal-architecture.md
    - decisions/0012-adopt-hexagonal-architecture.md
    - skills: /hexagonal-architecture
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


# ── 1. MemoryPort — long-term cross-session ledger of decisions/lessons ──
@runtime_checkable
class MemoryPort(Protocol):
    """Recall and persist entries in the Memory Ledger."""

    def recall(self, query: str, limit: int = 10) -> list[dict]:
        """Substring search over summary + tags."""
        ...

    def semantic_recall(self, query: str, limit: int = 10) -> list[dict]:
        """Ranked (BM25) search; may fall back to substring."""
        ...

    def remember(self, *, session_id: str, type: str, summary: str,
                 files: list[str] | None = None,
                 tags: list[str] | None = None) -> float:
        """Append an entry; return its timestamp (ts)."""
        ...


# ── 2. BlackboardPort — async message channel between agents ─────────────
@runtime_checkable
class BlackboardPort(Protocol):
    def post(self, *, frm: str, to: str, body: str,
             msg_type: str = "msg", thread_id: str | None = None) -> str:
        """Start or continue a thread; return the new message id."""
        ...

    def read(self, *, since_ts: float = 0.0,
             thread_id: str | None = None,
             to_filter: str | None = None,
             limit: int = 200) -> list[dict]:
        ...

    def reply(self, *, thread_id: str, frm: str, body: str,
              msg_type: str = "answer") -> str:
        ...


# ── 3. TaskBoardPort — decompose / claim / advance shared work ───────────
@runtime_checkable
class TaskBoardPort(Protocol):
    def add(self, *, goal: str, files: list[str] | None = None,
            parent_goal_id: str | None = None,
            lease_minutes: int = 30) -> str:
        ...

    def claim(self, task_id: str, *, claimant: str,
              lease_minutes: int = 30) -> bool:
        ...

    def release(self, task_id: str) -> bool:
        ...

    def update(self, task_id: str, *, status: str,
               note: str | None = None) -> bool:
        ...

    def list(self, *, status: str | None = None) -> list[dict]:
        ...


# ── 4. ClaimStorePort — Iron Law #11 coordination primitives ─────────────
@runtime_checkable
class ClaimStorePort(Protocol):
    def acquire(self, *, agent: str, scope: list[str], goal: str,
                phase: str = "ask", session_id: str = "") -> dict:
        ...

    def live(self) -> list[dict]:
        ...

    def describe(self, claims: list[dict]) -> str:
        ...

    def release(self, claim_id: str) -> bool:
        ...

    def release_session(self, session_id: str) -> int:
        """Return the count released (NOT a bool — pinned by char-test)."""
        ...

    def advance(self, claim_id: str, phase: str) -> dict:
        ...


# ── 5. FocusStorePort — per-session A-Flow stage gate ────────────────────
@runtime_checkable
class FocusStorePort(Protocol):
    """Read/write the focus state file. Dual-key interop with a_flow_state
    (phases_done ↔ completed_phases) is the store's responsibility, not the
    application's."""

    def read(self) -> dict | None:
        ...

    def write(self, state: dict) -> dict:
        ...

    def clear(self) -> bool:
        """Return True if a file existed and was removed."""
        ...


# ── 6. RoutingPort — A-Suite skill matching ──────────────────────────────
@runtime_checkable
class RoutingPort(Protocol):
    """Rank A-Suite skills against free text. Read-only over the registry."""

    def route(self, text: str, *, limit: int = 3) -> list[tuple[str, float]]:
        """Return (skill_name, score) pairs, ranked."""
        ...

    def get_skill(self, name: str) -> dict:
        ...


__all__ = [
    "MemoryPort", "BlackboardPort", "TaskBoardPort",
    "ClaimStorePort", "FocusStorePort", "RoutingPort",
]
