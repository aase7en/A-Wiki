// A-Wiki Live Dashboard — Playwright config (v10 CHUNK D10).
//
// Runs browser smoke + perf tests against a running dashboard server on
// http://localhost:7790. The server must be started separately — these tests
// do not bootstrap it (the dashboard is normally always-on via dashboard-ensure.sh).
//
// Install once:  npm i && npx playwright install chromium
// Run:           npm test                      # all specs
//                npm run test:smoke            # just smoke.spec.mjs
//
// Skip on machines without Playwright installed: pytest wrapper auto-skips.
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests-browser",
  fullyParallel: false, // dashboard is single-instance — avoid SSE contention
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1, // serial: the dashboard shares global state across tabs
  reporter: [["line"]],
  timeout: 20_000,
  use: {
    baseURL: "http://localhost:7790",
    trace: "on-first-retry",
    actionTimeout: 5_000,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
