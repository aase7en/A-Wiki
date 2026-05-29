#!/usr/bin/env python3
"""Compatibility wrapper for `scripts/hooks_runner.py`."""
from __future__ import annotations

import runpy
from pathlib import Path

TARGET = Path(__file__).resolve().parents[1] / "hooks_runner.py"

if __name__ == "__main__":
    runpy.run_path(str(TARGET), run_name="__main__")
