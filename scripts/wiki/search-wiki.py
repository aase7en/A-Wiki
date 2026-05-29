#!/usr/bin/env python3
"""Compatibility wrapper for `scripts/search-wiki.py`."""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

TARGET = Path(__file__).resolve().parents[1] / "search-wiki.py"

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    runpy.run_path(str(TARGET), run_name="__main__")
