#!/usr/bin/env python3
"""Open the Live Dashboard at a specific skill's detail view.

Usage:
    python scripts/open-skill.py <skill-name>
    python scripts/open-skill.py debug-mantra
    AWIKI_DASHBOARD_PORT=8080 python scripts/open-skill.py tdd

The script constructs a deep-link URL (?skill=<name>) and opens it in the
OS default browser. The dashboard's applyUrlParams() then opens the detail
drawer automatically after the skills list loads.

Cross-platform: uses webbrowser.open() which delegates to the OS default
browser on Windows (start), macOS (open), and Linux (xdg-open).
"""
from __future__ import annotations

import os
import sys
import urllib.parse
import webbrowser


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/open-skill.py <skill-name>", file=sys.stderr)
        print("Example: python scripts/open-skill.py debug-mantra", file=sys.stderr)
        return 1

    name = sys.argv[1].strip()
    if not name:
        print("❌ skill name cannot be empty", file=sys.stderr)
        return 1

    port = int(os.environ.get("AWIKI_DASHBOARD_PORT", "7790"))
    encoded = urllib.parse.quote(name, safe="")
    url = f"http://localhost:{port}/?skill={encoded}"

    try:
        webbrowser.open(url)
    except webbrowser.Error as e:
        print(f"❌ cannot open browser: {e}", file=sys.stderr)
        print(f"   URL: {url}", file=sys.stderr)
        return 2

    print(f"✅ Opening {name} → {url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
