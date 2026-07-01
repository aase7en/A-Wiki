"""Per-agent surface generators — each turns the registry into one agent's view.

Every generator exposes ``render(registry: Registry) -> str`` (the file content)
and ``filename`` (the surface file it owns).  The orchestrator imports them all,
calls render(), writes the files, and runs drift detection.

Adding a NEW agent in the future = add one module here + one line in the
orchestrator's generator list.  Nothing else changes.
"""
from __future__ import annotations
