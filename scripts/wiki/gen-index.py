#!/usr/bin/env python3
"""Compatibility wrapper for `scripts/gen-index.py`.

The root script is executed into this module namespace so tests and callers
that monkeypatch module globals (for example `WIKI_DIR`) keep working.
"""
from __future__ import annotations

from pathlib import Path

TARGET = Path(__file__).resolve().parents[1] / "gen-index.py"
globals()["__file__"] = str(TARGET)

code = compile(TARGET.read_text(encoding="utf-8"), str(TARGET), "exec")
exec(code, globals())

if __name__ == "__main__":
    raise SystemExit(main())
