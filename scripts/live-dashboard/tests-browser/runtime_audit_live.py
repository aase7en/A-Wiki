"""Targeted audit: inject a synthetic SSE event and verify _eventLog + DOM
both receive it. This isolates the pushTimeline ring buffer wiring from
the timing-dependent boot sequence.
"""
import json
import time
from playwright.sync_api import sync_playwright

URL = "http://localhost:7790/"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context()
        page = ctx.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_selector("#timeline-panel", state="attached", timeout=20000)
        time.sleep(2.0)

        # Baseline counts — wait for backlog to settle
        page.wait_for_function("window._lastBacklogComplete", timeout=10000) if False else None
        before = page.evaluate("""() => ({
            ring: (window._eventLog||[]).length,
            rows: document.querySelectorAll('#timeline-list .ev-row').length,
            evCount: document.querySelector('#event-count')?.textContent,
            connected: window.S?.connected,
        })""")
        print(f"BEFORE: {before}")
        # Specifically check: is _eventLog populated after backlog?
        # NOTE: top-level `let _eventLog` in a script does NOT attach to
        # window — only `var` does. We must call the public API
        # (exportEventLog) to inspect the ring buffer's actual contents.
        inject_result = page.evaluate("""() => {
            // Instrument toast() to capture the export path's message
            const origToast = window.toast;
            let toastMsg = null;
            window.toast = (msg) => { toastMsg = msg; };
            window._downloadBlob = (data, fname) => {};
            try {
                // Inject via the SAME global function the SSE handler uses
                handleEvent({type: 'hook_check', ts: Math.floor(Date.now()/1000), hook: 'test_audit', tool: 'Playwright', result: 'pass'});
                // Then call exportEventLog
                exportEventLog();
                return {ok: true, toastMsg};
            } catch (e) { return {err: String(e)}; }
            finally { window.toast = origToast; }
        }""")
        print(f"INJECT: {json.dumps(inject_result, indent=2, default=str)}")
        time.sleep(0.5)

        after = page.evaluate("""() => ({
            rows: document.querySelectorAll('#timeline-list .ev-row').length,
            evCount: document.querySelector('#event-count')?.textContent,
            firstRow: document.querySelector('#timeline-list .ev-row')?.textContent?.slice(0,80),
        })""")
        print(f"AFTER : {json.dumps(after, indent=2, default=str)}")

        browser.close()


if __name__ == "__main__":
    main()
