"""Live runtime check for A16 (subagent_invoke handler).
Injects a synthetic event via the same global handleEvent() the SSE handler
uses, then verifies the model KPI counter bumps and a thought is spawned.
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

        before = page.evaluate("""() => ({
            models: document.querySelector('#s-models')?.textContent,
            par: document.querySelector('#par-count')?.textContent,
            evCount: document.querySelector('#event-count')?.textContent,
        })""")
        print(f"BEFORE: {before}")

        result = page.evaluate("""() => {
            try {
                // Switch to summary view so the KPI tiles are visible
                setView('summary');
                handleEvent({
                    type: 'subagent_invoke',
                    ts: Math.floor(Date.now()/1000),
                    subagent_type: 'Explore',
                    model: 'deepseek-v4-flash',
                    bucket: 'deepseek',
                    result: 'pass',
                    latency_ms: 1234,
                    tokens_in: 100,
                    tokens_out: 5,
                });
                return {ok: true};
            } catch (e) { return {err: String(e)}; }
        }""")
        print(f"INJECT: {result}")
        time.sleep(0.6)

        after = page.evaluate("""() => ({
            models: document.querySelector('#s-models')?.textContent,
            par: document.querySelector('#par-count')?.textContent,
            evCount: document.querySelector('#event-count')?.textContent,
            // First timeline row should contain the subagent_type token
            firstRow: document.querySelector('#timeline-list .ev-row')?.textContent?.slice(0,90),
        })""")
        print(f"AFTER : {json.dumps(after, indent=2)}")
        browser.close()


if __name__ == "__main__":
    main()
