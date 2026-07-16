// A-Wiki Live Dashboard — browser smoke tests (v10 CHUNK D10).
//
// These 5 specs guard the most common regression paths:
//   1. Dashboard boots and connects to the SSE server within 5s
//   2. All 12 view tabs switch without throwing
//   3. Skills tab renders at least one card
//   4. Keyboard Tab cycles through focusable elements
//   5. Theme toggle flips the data-theme attribute
//
// Preconditions: dashboard running at http://localhost:7790 (bash scripts/dashboard-ensure.sh).
// Run: npm run test:smoke
import { test, expect } from "@playwright/test";

const VIEWS = [
  "summary", "flow", "timeline", "graph", "skills",
  "coverage", "analytics", "subagents", "eval", "cost", "council", "chat",
];

test.describe("A-Wiki Dashboard smoke", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("1. boots and connects to SSE within 5s", async ({ page }) => {
    // The offline overlay must disappear once SSE connects.
    await expect(page.locator("#offline")).toBeHidden({ timeout: 5_000 });
    // The live indicator dot should be "on" once connected.
    await expect(page.locator("#live-dot")).toHaveClass(/on/, { timeout: 5_000 });
  });

  test("2. all 12 view tabs switch without error", async ({ page }) => {
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    for (const v of VIEWS) {
      await page.click(`#btn-${v}`);
      // The corresponding panel should become visible.
      const panel = page.locator(`#view-${v}, #${v}-panel, #${v === "graph" ? "graph-vis" : ""}`).first();
      await expect(panel).toBeVisible({ timeout: 2_000 });
    }
    expect(errors, `JS errors during tab switch: ${errors.join("; ")}`).toEqual([]);
  });

  test("3. skills tab renders at least one card", async ({ page }) => {
    await page.click("#btn-skills");
    // Wait for skills grid to populate (not the "loading" placeholder).
    await expect(page.locator(".skill-card").first()).toBeVisible({ timeout: 5_000 });
    const count = await page.locator(".skill-card").count();
    expect(count).toBeGreaterThan(0);
  });

  test("4. keyboard Tab cycles through focusable elements", async ({ page }) => {
    // Press Tab a few times; focus should move and not get stuck or throw.
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press("Tab");
    }
    const active = await page.evaluate(() => document.activeElement?.tagName || "");
    expect(["BUTTON", "INPUT", "A", "SELECT", "TEXTAREA"]).toContain(active);
  });

  test("5. theme toggle flips data-theme attribute", async ({ page }) => {
    const before = await page.evaluate(() =>
      document.documentElement.getAttribute("data-theme") || ""
    );
    await page.click("#btn-theme");
    const after = await page.evaluate(() =>
      document.documentElement.getAttribute("data-theme") || ""
    );
    // The attribute value must change after toggling (auto -> dark -> green-white cycle).
    expect(after).not.toBe(before);
  });
});
