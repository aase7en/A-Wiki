#!/usr/bin/env python3
"""CLI entry point for scripts/detect-agent.sh.

Prints the detected agent name (claude/codex/zcode/...) to stdout, or empty
string if no fingerprint matched. Always exits 0.

This file exists as a thin wrapper so the shell caller doesn't need to
construct a Python -c one-liner with platform-specific path escaping
(MSYS /a/... vs Windows A:/...). It resolves its own __file__ to find
agent_detect.py in the same directory.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Make sibling agent_detect.py importable regardless of cwd.
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

try:
    from agent_detect import detect_agent  # type: ignore[import-not-found]
    name = detect_agent() or ""
    sys.stdout.write(name)
except Exception:
    # Fail-soft: detection must never crash the caller. Empty output
    # signals "no agent detected", which dashboard-ensure.sh handles by
    # opening the dashboard without ?agent= (shows all skills).
    pass
