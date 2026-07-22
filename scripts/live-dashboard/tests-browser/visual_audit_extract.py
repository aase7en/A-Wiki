"""Extract actual design tokens + AI-slop heuristics from rendered dashboard.
No vision needed — uses getComputedStyle + DOM metrics to score the 10 dimensions."""
import json, re
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://localhost:7790/"
OUT = Path("A:/GitHub/A-Wiki/scripts/live-dashboard/tests-browser/visual-audit.json")

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_selector("#timeline-panel", state="attached", timeout=20000)
    page.wait_for_timeout(2000)

    audit = page.evaluate("""() => {
      const root = getComputedStyle(document.documentElement);
      const body = getComputedStyle(document.body);
      const get = (n) => root.getPropertyValue(n).trim();

      // 1) Color palette extraction
      const palette = {
        accent: get('--accent-brand'),
        warm: get('--accent-warm'),
        cool: get('--accent-cool'),
        violet: get('--accent-violet'),
        success: get('--accent-success'),
        danger: get('--accent-danger'),
        bg0: get('--elev-0'),
        bg1: get('--elev-1'),
        bg2: get('--elev-2'),
        bg3: get('--elev-3'),
        textPri: get('--text-primary'),
        textSec: get('--text-secondary'),
        textTer: get('--text-tertiary'),
        border1: get('--border'),
        border2: get('--border2'),
      };

      // 2) Typography
      const typo = {
        font: body.fontFamily,
        baseFs: body.fontSize,
        fsXs: get('--fs-xs'),
        fsSm: get('--fs-sm'),
        fsMd: get('--fs-md'),
        fsLg: get('--fs-lg'),
        fsXl: get('--fs-xl'),
        fs2xl: get('--fs-2xl'),
      };

      // 3) Spacing scale
      const spacing = {
        rSm: get('--r-sm'),
        rMd: get('--r-md'),
        rLg: get('--r-lg'),
        rXl: get('--r-xl'),
      };

      // 4) Gradients in CSS (count occurrences)
      const allCSS = Array.from(document.styleSheets).flatMap(s => {
        try { return Array.from(s.cssRules).map(r => r.cssText); }
        catch (_) { return []; }
      }).join('\\n');
      const gradientCount = (allCSS.match(/linear-gradient|radial-gradient|conic-gradient/g) || []).length;
      const glassCount = (allCSS.match(/backdrop-filter:\\s*blur/g) || []).length;
      const shadowCount = (allCSS.match(/box-shadow:/g) || []).length;
      const transitionCount = (allCSS.match(/transition:/g) || []).length;
      const animationCount = (allCSS.match(/animation:/g) || []).length;
      const borderRadiusCount = (allCSS.match(/border-radius:/g) || []).length;
      const purpleBluePat = (allCSS.match(/#[0-9a-f]{3,8}|rgba?\\(/gi) || []);

      // 5) DOM density
      const totalNodes = document.querySelectorAll('*').length;
      const buttons = document.querySelectorAll('button').length;
      const inputs = document.querySelectorAll('input,textarea,select').length;
      const visibleText = (document.body.innerText || '').length;

      // 6) Heading hierarchy
      const headings = Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,h6'))
        .map(h => ({tag: h.tagName, text: (h.textContent||'').trim().slice(0,60)}));

      return {
        palette, typo, spacing,
        css_features: {gradientCount, glassCount, shadowCount, transitionCount, animationCount, borderRadiusCount},
        dom: {totalNodes, buttons, inputs, visibleTextChars: visibleText, headings: headings.slice(0,12)},
        bodyBg: body.backgroundColor,
        bodyColor: body.color,
      };
    }""")

    browser.close()

OUT.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(audit, indent=2, ensure_ascii=False))
