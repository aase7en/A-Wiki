"""_repo_root.py — workspace-vs-brain root seam (Slice A: awiki adopt).

Two roots exist once the brain serves FOREIGN repos:

  workspace root — the repo the agent is editing RIGHT NOW. Provider
    payloads carry `cwd` (Claude Code / ZCode / Codex hook contract);
    that is the truth for workspace guards (raw/, provenance, paths).

  brain root — this A-Wiki checkout (parent of scripts/). Brain-state
    consumers (skill registry, memory ledger, live log) always use it.

Resolution rule: payload `cwd` wins for the workspace; anything absent
falls back to the brain so every pre-adopt behavior is unchanged.
"""
from __future__ import annotations

import os
from pathlib import Path


def brain_root() -> str:
    """This A-Wiki checkout (scripts/hooks/../..)."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def resolve_repo_root(input_data: dict) -> str:
    """Workspace root from the hook payload; brain root as legacy fallback."""
    cwd = input_data.get("cwd") if isinstance(input_data, dict) else None
    if isinstance(cwd, str) and cwd.strip():
        return os.path.abspath(cwd)
    return brain_root()
