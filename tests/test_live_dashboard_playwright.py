"""Wrapper that runs the Playwright browser smoke tests (v10 CHUNK D10).

Playwright is an optional dependency — most dev machines only run the Python
contract tests. This wrapper:

  - Skips gracefully if `@playwright/test` or the chromium browser is missing
    (so `pytest` stays green on minimal installs).
  - Otherwise shells out to `npx playwright test --reporter=line` in the
    dashboard directory and surfaces failures as pytest failures.

To install Playwright (optional):
    cd scripts/live-dashboard
    npm install
    npx playwright install chromium

To run just these tests:
    pytest tests/test_live_dashboard_playwright.py -v
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_DIR = REPO_ROOT / "scripts" / "live-dashboard"
PLAYWRIGHT_CONFIG = DASHBOARD_DIR / "playwright.config.mjs"


def _playwright_available() -> bool:
    """True iff npx + playwright config + @playwright/test are installed."""
    if not PLAYWRIGHT_CONFIG.is_file():
        return False
    if shutil.which("npx") is None:
        return False
    node_modules = DASHBOARD_DIR / "node_modules" / "@playwright" / "test"
    return node_modules.is_dir()


@pytest.mark.skipif(
    not _playwright_available(),
    reason="Playwright not installed — run `npm i && npx playwright install chromium` in scripts/live-dashboard/",
)
def test_playwright_smoke_suite():
    """Run the 5 browser smoke specs (boot, tab switch, skills, keyboard, theme)."""
    result = subprocess.run(
        ["npx", "playwright", "test", "tests-browser/smoke.spec.mjs", "--reporter=line"],
        cwd=str(DASHBOARD_DIR),
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        pytest.fail(
            "Playwright smoke suite failed:\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )
