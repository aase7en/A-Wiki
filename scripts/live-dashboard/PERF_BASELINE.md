# A-Wiki Live Dashboard — Performance Baseline

> **Purpose**: track gross regressions (>50% slower than baseline). Soft budgets;
> micro-variance from localhost/network is expected and ignored.
>
> See `tests-browser/perf.spec.mjs` for the assertions that read these budgets.

## Baseline (captured 2026-07-16, dev laptop)

Captured on a dev machine right after v10 CHUNK C10 landed (CDN defer + TTL
cache + lazy view init). Numbers will vary by machine; the budgets are padded
50% above observed values to absorb variance.

| Metric | Observed | Budget (fail >) |
|--------|----------|-----------------|
| Load event time (DOMContentLoaded → load) | ~1500ms | 4500ms |
| Largest Contentful Paint (LCP) | ~700ms | 2250ms |
| DOM node count (after skills grid fills) | ~800 | 3000 |
| JS evaluation time (domInteractive → domComplete) | ~400ms | 1500ms |

## What each metric means

- **Load event time** — gap between DOM ready and full load. High values mean
  late network requests or heavy synchronous scripts.
- **LCP** — when the largest visible element renders. Low = perceived fast.
- **DOM node count** — proxy for HTML weight and reflow cost. Growing without
  bound signals a render leak.
- **JS eval time** — script parsing/execution during load. Higher than budget
  usually means a new dependency or un-bundled JS slipped in.

## How to refresh the baseline

1. Start the dashboard: `bash scripts/dashboard-ensure.sh`
2. From `scripts/live-dashboard/`: `npx playwright test tests-browser/perf.spec.mjs --reporter=line`
3. Update the "Observed" column above with fresh numbers.
4. If budgets need adjustment, edit `BUDGETS` in `tests-browser/perf.spec.mjs`.

## Iron Law context

This file is a tracking document (Markdown), not a config or test — it does not
enforce anything on its own. The actual enforcement lives in
`tests-browser/perf.spec.mjs`. Edit freely; the budgets are intentionally soft.
