"""Quick runtime check: does Cmd+K actually open the palette?"""
import json, time
from playwright.sync_api import sync_playwright

URL = "http://localhost:7790/"

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context()
    page = ctx.new_page()
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_selector("#timeline-panel", state="attached", timeout=20000)
    time.sleep(2.0)

    # Is palette element defined?
    pal = page.evaluate("""() => ({
        backdrop: !!document.getElementById('palette-backdrop'),
        modal: !!document.getElementById('palette-modal'),
        input: !!document.getElementById('palette-input'),
        visibleBefore: document.getElementById('palette-modal')?.style?.display,
    })""")
    print(f"PALETTE DOM: {pal}")

    # Try Cmd+K (Control+k on Win/Linux in Chromium)
    page.keyboard.press("Control+k")
    time.sleep(0.6)
    pal2 = page.evaluate("""() => ({
        visibleAfter: document.getElementById('palette-modal')?.style?.display,
        rowCount: document.querySelectorAll('.palette-row').length,
        inputFocused: document.activeElement?.id,
    })""")
    print(f"AFTER Cmd+K: {pal2}")
    browser.close()
