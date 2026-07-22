"""v19 deep audit (debug-mantra step 1: reproduce).

Surfaces v19-specific risks:
  1. SVG sprite injection timing — does #icon-sprite exist when DOM is ready?
  2. <use href='#icon-X'> resolution — do icons actually render (visible)?
  3. icon() helper availability — typeof check at every call site
  4. brand-mark inline SVG — renders + sizing correct
  5. evIcon path — every event row shows a visible icon (not text fallback)
  6. Cmd+K palette icon rendering — rows have visible SVG children
  7. Emoji residuals — count leftover emoji chars per panel
"""
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://localhost:7790/"
OUT = Path("A:/GitHub/A-Wiki/scripts/live-dashboard/tests-browser/v19-deep-audit.json")

VIEWS = ["summary", "flow", "timeline", "graph", "skills", "coverage",
         "analytics", "subagents", "eval", "cost", "race", "chat", "council"]


def main():
    report = {"icons": {}, "emoji_residuals": {}, "dom": {}, "console": []}

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()

        page.on("console", lambda m: report["console"].append({
            "type": m.type, "text": m.text[:240]
        }) if m.type == "error" else None)
        page.on("pageerror", lambda e: report["console"].append({
            "type": "pageerror", "text": str(e)[:240]
        }))

        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_selector("#timeline-panel", state="attached", timeout=20000)
        time.sleep(2.5)

        # === 1. Sprite injection check ===
        report["icons"]["sprite_injected"] = page.evaluate("""() => {
            const s = document.getElementById('icon-sprite');
            if (!s) return {ok: false, reason: 'no #icon-sprite element'};
            const syms = s.querySelectorAll('symbol');
            return {ok: syms.length > 0, symbol_count: syms.length};
        }""")

        # === 2. icon() helper global ===
        report["icons"]["helper_global"] = page.evaluate("""() => ({
            icon: typeof window.icon,
            defined: typeof window.icon === 'function',
        })""")

        # === 3. Header icons render (have visible svg children) ===
        report["icons"]["header_icon_visible"] = page.evaluate("""() => {
            const btns = document.querySelectorAll('#header button');
            const out = [];
            btns.forEach(b => {
                const use = b.querySelector('use');
                out.push({
                    label: b.getAttribute('aria-label') || b.title || '?',
                    has_use: !!use,
                    href: use ? use.getAttribute('href') : null,
                });
            });
            return out;
        }""")

        # === 4. View-tab icons render ===
        report["icons"]["view_tab_use_refs"] = page.evaluate("""() => {
            const btns = document.querySelectorAll('.view-toggle-bar button');
            const out = [];
            btns.forEach(b => {
                const use = b.querySelector('use');
                out.push({
                    id: b.id,
                    text: (b.textContent || '').trim().slice(0, 24),
                    has_use: !!use,
                    href: use ? use.getAttribute('href') : null,
                });
            });
            return out;
        }""")

        # === 5. wf-tab icons ===
        report["icons"]["wf_tab_use_refs"] = page.evaluate("""() => {
            const tabs = document.querySelectorAll('#wf-tabs .wf-tab');
            const out = [];
            tabs.forEach(t => {
                const use = t.querySelector('use');
                out.push({
                    id: t.id,
                    text: (t.textContent || '').trim().slice(0, 24),
                    has_use: !!use,
                    href: use ? use.getAttribute('href') : null,
                });
            });
            return out;
        }""")

        # === 6. brand mark ===
        report["icons"]["brand_mark"] = page.evaluate("""() => {
            const brand = document.querySelector('#header .brand');
            if (!brand) return {ok: false, reason: 'no .brand element'};
            const svg = brand.querySelector('svg');
            const text = brand.textContent || '';
            return {
                ok: !!svg,
                has_svg: !!svg,
                svg_viewBox: svg ? svg.getAttribute('viewBox') : null,
                text: text.trim().slice(0, 60),
            };
        }""")

        # === 7. Cmd+K palette icons (open palette) ===
        try:
            page.keyboard.press("Control+k")
            time.sleep(0.6)
            report["icons"]["palette_rows"] = page.evaluate("""() => {
                const rows = document.querySelectorAll('.palette-row');
                const out = [];
                rows.forEach(r => {
                    const use = r.querySelector('use');
                    out.push({
                        text: (r.textContent || '').trim().slice(0, 50),
                        has_use: !!use,
                        href: use ? use.getAttribute('href') : null,
                    });
                });
                return out.slice(0, 5);
            }""")
            page.keyboard.press("Escape")
            time.sleep(0.3)
        except Exception as e:
            report["icons"]["palette_rows_error"] = str(e)

        # === 8. Event timeline icons ===
        report["icons"]["timeline_icons"] = page.evaluate("""() => {
            // Switch to timeline to populate
            const rows = document.querySelectorAll('#timeline-list .ev-row');
            const sample = [];
            for (let i = 0; i < Math.min(rows.length, 5); i++) {
                const use = rows[i].querySelector('use');
                const tx = rows[i].querySelector('.ev-tx');
                sample.push({
                    has_use: !!use,
                    href: use ? use.getAttribute('href') : null,
                    text: tx ? tx.textContent.trim().slice(0, 40) : '',
                });
            }
            return sample;
        }""")

        # === 9. Emoji residuals per view ===
        for v in VIEWS:
            try:
                btn = page.locator(f"[onclick*=\"setView('{v}'\"]").first
                if btn.count():
                    btn.click(timeout=1500)
                    time.sleep(0.4)
                    counts = page.evaluate("""(view) => {
                        const root = document.querySelector('.view-panel:not([style*="display: none"])') || document.body;
                        const txt = root.textContent || '';
                        let emojis = 0;
                        for (const ch of txt) {
                            const c = ch.codePointAt(0);
                            if ((c >= 0x1F300 && c <= 0x1FAFF) || (c >= 0x2600 && c <= 0x27BF)) emojis++;
                        }
                        return emojis;
                    }""", v)
                    report["emoji_residuals"][v] = counts
            except Exception:
                report["emoji_residuals"][v] = "skip"

        # === 10. DOM stats ===
        report["dom"] = page.evaluate("""() => ({
            nodes: document.querySelectorAll('*').length,
            use_refs: document.querySelectorAll('use').length,
            sprite_symbols: document.querySelectorAll('#icon-sprite symbol').length,
        })""")

        browser.close()

    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    # Summary
    print(f"=== ICON AUDIT ===")
    print(f"  sprite_injected: {report['icons']['sprite_injected']}")
    print(f"  helper_global:   {report['icons']['helper_global']}")
    print(f"  brand_mark:      {report['icons']['brand_mark']}")
    print(f"\n=== HEADER BUTTONS ({len(report['icons']['header_icon_visible'])}) ===")
    for h in report["icons"]["header_icon_visible"]:
        flag = "OK" if h["has_use"] else "MISS"
        print(f"  [{flag}] {h['label']:30}  href={h['href']}")
    print(f"\n=== VIEW TABS ({len(report['icons']['view_tab_use_refs'])}) ===")
    for v in report["icons"]["view_tab_use_refs"]:
        flag = "OK" if v["has_use"] else "MISS"
        print(f"  [{flag}] {v['id']:18}  text={v['text']:20}  href={v['href']}")
    print(f"\n=== WF TABS ({len(report['icons']['wf_tab_use_refs'])}) ===")
    for w in report["icons"]["wf_tab_use_refs"]:
        flag = "OK" if w["has_use"] else "MISS"
        print(f"  [{flag}] {w['id']:18}  text={w['text']:20}  href={w['href']}")
    print(f"\n=== TIMELINE ICONS ({len(report['icons']['timeline_icons'])}) ===")
    for t in report["icons"]["timeline_icons"]:
        flag = "OK" if t["has_use"] else "MISS"
        print(f"  [{flag}] href={t['href']}  text={t['text']}")
    print(f"\n=== PALETTE ROWS ===")
    if "palette_rows" in report["icons"]:
        for r in report["icons"]["palette_rows"]:
            flag = "OK" if r["has_use"] else "MISS"
            print(f"  [{flag}] href={r['href']}  text={r['text']}")
    print(f"\n=== EMOJI RESIDUALS ===")
    for v, c in report["emoji_residuals"].items():
        print(f"  {v}: {c}")
    print(f"\n=== DOM ===")
    print(f"  {report['dom']}")
    print(f"\n=== CONSOLE ERRORS ({len(report['console'])}) ===")
    for e in report["console"][:5]:
        print(f"  {e['type']}: {e['text']}")
    print(f"\nReport: {OUT}")


if __name__ == "__main__":
    main()
