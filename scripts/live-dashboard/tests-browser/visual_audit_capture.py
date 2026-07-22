"""Capture screenshots of all 13 dashboard views for visual audit (design-system Mode 2).
Saves PNGs to /tmp/dash-shots/ — analyzed via vision tool."""
import os, time
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://localhost:7790/"
OUT = Path("/tmp/dash-shots")
OUT.mkdir(exist_ok=True, parents=True)

VIEWS = ["summary", "flow", "timeline", "graph", "skills", "coverage",
         "analytics", "subagents", "eval", "cost", "race", "chat", "council"]

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1440, "height": 900},
                              device_scale_factor=1)
    page = ctx.new_page()
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_selector("#timeline-panel", state="attached", timeout=20000)
    time.sleep(2.0)

    # Default state
    page.screenshot(path=str(OUT / "00-boot.png"), full_page=False)
    print(f"✓ 00-boot")

    for i, v in enumerate(VIEWS, 1):
        try:
            btn = page.locator(f"[onclick*=\"setView('{v}'\"]").first
            if btn.count():
                btn.click(timeout=2000)
                time.sleep(1.2)  # let animations settle
                page.screenshot(path=str(OUT / f"{i:02d}-{v}.png"), full_page=False)
                print(f"✓ {i:02d}-{v}")
        except Exception as e:
            print(f"✗ {v}: {e}")

    # Settings open
    try:
        page.locator("[onclick*=\"openSettings()\"]").first.click(timeout=2000)
        time.sleep(0.8)
        page.screenshot(path=str(OUT / "99-settings.png"), full_page=False)
        print(f"✓ 99-settings")
    except Exception as e:
        print(f"✗ settings: {e}")

    browser.close()
print(f"\nScreenshots: {OUT}")
