"""A-Wiki Memory Plane — L0–L5 layer semantics (Phase 5).

Single source of layer policy, mirrored by config/memory-layers.yaml
(a consistency test keeps them in lockstep). Layer semantics (work order §4):

  L0 Working Context  — runtime (.tmp), never global knowledge, never promoted
  L1 Session/Operational — MemoryLedger substrate, no auto-promotion to L3
  L2 Project Memory   — durable, exactly one attached project (Phase-4 id)
  L3 Global Knowledge — wiki/ remains canonical; reachable ONLY via the
                        five-gate promotion pipeline
  L4 Raw Evidence     — immutable from memory write paths; no direct L4→L3
  L5 Experiment Memory— baseline immutable / iterations append-only /
                        winner must reference recorded evidence
"""
from __future__ import annotations


class LayerViolation(Exception):
    """Raised when an operation violates layer semantics."""


LAYER_POLICY: dict[str, dict] = {
    "L0": {
        "name": "working-context",
        "durability": "runtime",
        "store": ".tmp/ (or equivalent runtime store)",
        "global_knowledge": False,
        "auto_promote": False,
        "writable_via_memory_api": True,
    },
    "L1": {
        "name": "session-operational",
        "durability": "durable",
        "store": "memory ledger (scripts/lib/memory_ledger.py — JSONL)",
        "global_knowledge": False,
        "auto_promote": False,
        "writable_via_memory_api": True,
    },
    "L2": {
        "name": "project",
        "durability": "durable",
        "store": "projects/<project-id>/memory/ under the A-Wiki data root",
        "global_knowledge": False,
        "auto_promote": False,
        "writable_via_memory_api": True,
    },
    "L3": {
        "name": "global-knowledge",
        "durability": "durable",
        "store": "wiki/ (canonical global plane — unchanged)",
        "global_knowledge": True,
        "auto_promote": False,
        "writable_via_memory_api": False,  # only via promotion gates
    },
    "L4": {
        "name": "raw-evidence",
        "durability": "durable",
        "store": "raw/ (immutable)",
        "global_knowledge": False,
        "auto_promote": False,
        "writable_via_memory_api": False,  # never mutated by memory ops
    },
    "L5": {
        "name": "experiment",
        "durability": "durable",
        "store": "projects/<project-id>/experiments/<exp-id>/ under the data root",
        "global_knowledge": False,
        "auto_promote": False,
        "writable_via_memory_api": True,  # through ExperimentStore semantics
    },
}

# The only sanctioned edge into L3.
_PROMOTION_EDGE = ("L2", "L3")


def transition_allowed(source: str, target: str, *, via: str | None = None) -> bool:
    """Layer transition gate. The ONLY path into L3 is L2 via='promotion'
    (the five-gate pipeline). L0/L1/L4 can never transition to L3."""
    if target == "L3":
        if source == "L2" and via == "promotion":
            return True
        return False
    # same-layer and non-L3 transitions are policy-neutral in Phase 5
    return source == target
