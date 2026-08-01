"""Shared pytest fixtures for tests/platforms/.

Puts scripts/lib on sys.path so tests can import `from platforms.X import Y`,
matching the Shape B test convention documented in scripts/lib/ conventions.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LIB_DIR = REPO_ROOT / "scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
