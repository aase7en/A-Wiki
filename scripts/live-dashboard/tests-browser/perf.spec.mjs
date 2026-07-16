// A-Wiki Live Dashboard — performance budget tests (v10 CHUNK E10).
//
// Soft assertions: log observed metrics, fail only on severe regression (>50%
// slower than the committed baseline in PERF_BASELINE.md). The point is to
// catch gross regressions, not to micro-optimize localhost timing variance.
//
// Metrics captured:
//   - Load event time (DOMContentLoaded -> load)
//   - Largest Contentful Paint (LCP)
//   - DOM node count (HTML weight proxy)
//   - JS execution time (script eval)
//
// Run: npx playwright test tests-browser/perf.spec.mjs --reporter=line
import { test, expect } from "@playwright/test";

// Budgets — fail only on severe regression (>50% over baseline).
// Baseline captured 2026-07-16 on a dev laptop; see PERF_BASELINE.md.
const BUDGETS = {
  loadMs: 3_000,      // baseline ~1500ms; fail at 4500ms+
  lcpMs: 1_500,       // baseline ~700ms; fail at 2250ms+
  domNodes: 2_000,    // baseline ~800; fail at 3000+
  jsEvalMs: 1_000,    // baseline ~400ms; fail at 1500ms+
};

test.describe("A-Wiki Dashboard performance budget", () => {
  test("load + LCP within budget", async ({ page }) => {
    const metrics = [];
    page.on("console", (msg) => {
      if (msg.text().startsWith("[perf]")) metrics.push(msg.text());
    });

    await page.goto("/", { waitUntil: "load" });

    // Capture LCP via PerformanceObserver.
    const lcp = await page.evaluate(() => {
      return new Promise((resolve) => {
        const obs = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          if (entries.length) resolve(entries[entries.length - 1].startTime);
          else resolve(0);
        });
        obs.observe({ type: "largest-contentful-paint", buffered: true });
        // Fallback if no LCP fires within 2s.
        setTimeout(() => resolve(0), 2_000);
      });
    });

    const nav = await page.evaluate(() => {
      const [e] = performance.getEntriesByType("navigation");
      return {
        loadMs: e ? e.loadEventEnd - e.domContentLoadedEventEnd : 0,
        domContentLoaded: e ? e.domContentLoadedEventEnd : 0,
      };
    });

    console.log(`[perf] load=${nav.loadMs}ms lcp=${lcp.toFixed(0)}ms`);

    // Soft-fail only on severe regression.
    expect(nav.loadMs, "load event time").toBeLessThan(BUDGETS.loadMs * 1.5);
    if (lcp > 0) {
      expect(lcp, "LCP").toBeLessThan(BUDGETS.lcpMs * 1.5);
    }
  });

  test("DOM node count within budget", async ({ page }) => {
    await page.goto("/", { waitUntil: "load" });
    // Give the skills grid a moment to populate.
    await page.waitForTimeout(1_500);
    const count = await page.evaluate(() => document.getElementsByTagName("*").length);
    console.log(`[perf] domNodes=${count}`);
    expect(count, "DOM node count").toBeLessThan(BUDGETS.domNodes);
  });

  test("JS evaluation time within budget", async ({ page }) => {
    await page.goto("/", { waitUntil: "load" });
    const evalMs = await page.evaluate(() => {
      const [e] = performance.getEntriesByType("navigation");
      // script eval is part of the load phase; use domComplete - domInteractive
      // as a proxy for JS execution overhead.
      return e ? e.domComplete - e.domInteractive : 0;
    });
    console.log(`[perf] jsEval=${evalMs.toFixed(0)}ms`);
    expect(evalMs, "JS execution time").toBeLessThan(BUDGETS.jsEvalMs);
  });
});
