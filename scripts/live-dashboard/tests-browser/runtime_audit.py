"""Integration audit (debug-mantra step 1: reproduce).

Loads the running dashboard at http://localhost:7790/ with Playwright,
drives every view + settings pane, and prints console errors / pageerrors /
failed requests. Pure diagnostic — no pytest assertions, just a human
report. The accompanying regression test in tests/test_live_dashboard_*.py
asserts on the JSON output written by this script.

Usage:
    python tests-browser/runtime_audit.py [--out report.json]
"""
import argparse
import json
import sys
import time
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("ERROR: playwright not installed. Run: pip install playwright && python -m playwright install chromium", file=sys.stderr)
    sys.exit(2)


URL = "http://localhost:7790/"
VIEWS = ["summary", "flow", "skills", "subagents", "analytics", "graph", "coverage", "chat"]
SETTINGS = ["general", "keybinds", "about", "help", "theme", "backup", "tour", "health"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="tests-browser/audit-report.json")
    ap.add_argument("--timeout", type=int, default=60000)
    args = ap.parse_args()

    errors, warnings, pageerrors, reqfails = [], [], [], []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context()
        page = ctx.new_page()

        page.on("console", lambda m: (
            errors.append(m.text) if m.type == "error"
            else warnings.append(m.text) if m.type == "warning" else None
        ))
        page.on("pageerror", lambda e: pageerrors.append(str(e)))
        page.on("requestfailed", lambda r: reqfails.append({
            "url": r.url, "err": r.failure and r.failure.errorText
        }))

        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=args.timeout)
            # Wait for app.min.js to execute boot() — dashboard-app-ready is
            # set when boot() completes (we don't have a signal today, so we
            # wait for the skills panel to render).
            page.wait_for_selector("#skills-panel, #view-summary", timeout=20000)
        except Exception as e:
            print(f"FATAL: goto failed: {e}", file=sys.stderr)
            browser.close()
            sys.exit(3)

        # SSE connect window
        time.sleep(2.0)

        # Switch through every view
        for v in VIEWS:
            try:
                btn = page.locator(f"[onclick*=\"setView('{v}'\"]").first
                if btn.count():
                    btn.click(timeout=2000)
                    time.sleep(0.4)
            except Exception as e:
                errors.append(f"view-click {v}: {e}")

        # Open settings + walk panes
        try:
            page.locator("[onclick*=\"openSettings()\"]").first.click(timeout=2000)
            time.sleep(0.3)
        except Exception as e:
            errors.append(f"openSettings: {e}")

        for s in SETTINGS:
            try:
                btn = page.locator(f"[onclick*=\"'{s}'\"]").first
                if btn.count():
                    btn.click(timeout=2000)
                    time.sleep(0.2)
            except Exception as e:
                errors.append(f"settings-click {s}: {e}")

        try:
            page.locator("[onclick*=\"closeSettings()\"]").first.click(timeout=2000)
        except Exception:
            pass

        # Final wait for any async render errors
        time.sleep(1.0)

        # Capture DOM stats + localStorage snapshot
        dom_stats = page.evaluate("""() => ({
            nodes: document.querySelectorAll('*').length,
            activeBtn: (document.querySelector('.view-btn.active')||{}).id || null,
            panelsVisible: Array.from(document.querySelectorAll('[id$="-panel"],[id^="view-"],[id="graph-vis"]'))
                .filter(e => getComputedStyle(e).display !== 'none')
                .map(e => e.id),
            openModal: !!document.querySelector('.modal:not([hidden])'),
            lsKeys: Object.keys(localStorage).filter(k => k.startsWith('awiki-')),
            eventLogLen: (window._eventLog||[]).length,
            timelineRows: document.querySelectorAll('#timeline-list .ev-row').length,
        })""")

        browser.close()

    report = {
        "errors": errors,
        "pageerrors": pageerrors,
        "request_failures": reqfails,
        "warning_count": len(warnings),
        "warning_samples": warnings[:8],
        "dom": dom_stats,
    }
    out = Path(args.out)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"=== {len(errors)} errors / {len(pageerrors)} pageerrors / {len(reqfails)} req fails / {len(warnings)} warnings ===")
    for e in errors[:20]:
        print(f"  ERR: {e[:240]}")
    for pe in pageerrors[:20]:
        print(f"  PAGEERR: {pe[:240]}")
    for rf in reqfails[:10]:
        print(f"  REQFAIL: {rf}")
    print(f"\nDOM: {dom_stats}")
    print(f"\nReport: {out}")


if __name__ == "__main__":
    main()
