# PWQ Sale-ready Mock Build Preflight

> [verified 2026-06-05] Release checklist for a sellable Sunday Invest Moon mock/read-only build. This does not approve a live finance feed, provider key handling, order execution, or legal/compliance claims.

## Scope

Use this runbook when packaging `pixel-wealth-quest` as a public/demo/sales artifact.

The release artifact may include:

- Cozy financial life-sim gameplay.
- Mock portfolio/dashboard values.
- Read-only Debt Dungeon and Sea/Tide & Tally bridge panels.
- Static/read-only News Bird briefings.
- Read-only feed contract shell and scanner.

The release artifact must not include:

- Client API keys, provider tokens, exchange/broker credentials, or OpenRouter/Gemini secrets.
- Live provider calls from the Vite/browser client.
- Order, trade, buy, sell, submit, execute, withdraw, or cancel paths.
- Claims that the app gives financial, legal, or investment advice.
- Raw/private files from A-Wiki `drive/`, `raw/`, journal, customer data, or local secrets.

## Product Preflight

From `sunday-estate-webapp/pixel-wealth-quest/`:

```bash
npm run feed:scan
npm test -- --run
npm run typecheck
npm run build
npx react-doctor@latest --verbose --diff
```

Expected result:

| Check | Pass condition |
|---|---|
| `feed:scan` | `feed-boundary scan clean` |
| tests | all Vitest files pass |
| typecheck | `tsc -b --noEmit` exits 0 |
| build | Vite build exits 0; Phaser chunk warning is acceptable until code-splitting ticket exists |
| React Doctor | 100/100 with no issue, or documented false positive with evidence |

## Runtime Evidence

Capture fresh screenshots before packaging:

| Flow | Evidence |
|---|---|
| Title -> Room | Title branding and HUD visible |
| Portfolio HUD | `snapshot.source=mock` or explicit read-only label |
| Debt Dungeon | desktop + mobile panel, forbidden buttons=0, no overflow |
| Sea Bridge | desktop + mobile panel, forbidden buttons=0, no overflow |
| Farm marker | real canvas click opens `sea-bridge` only |
| News Bird | if static briefing is included, letter opens read-only with source/confidence metadata |

For automation, use the existing Playwright CLI session pattern and save files under the product `.playwright-cli/` folder or a dated `output/playwright/` subfolder.

## A-Wiki Preflight

From `A-Wiki/` after any roadmap/HANDOFF/wiki edit:

```bash
python3 scripts/game/sync_sunday_invest_moon_roadmap.py --sync
python3 scripts/game/sync_sunday_invest_moon_roadmap.py
python3 scripts/gen-index.py
python3 scripts/gen-index.py --check
python3 -m pytest tests/test_sync_sunday_invest_moon_roadmap.py -v
python3 scripts/check-privacy.py
```

Expected result:

| Check | Pass condition |
|---|---|
| roadmap sync | canonical roadmap and product mirror match exactly |
| gen-index | wiki context/index/graph/canvas regenerate cleanly |
| sync tests | 3 tests pass |
| privacy scan | no secrets, personal paths, or private data in public-safe artifacts |

## Release Gate

Before tagging or sharing a build:

- Confirm `docs/protocols/pwq-read-only-feed-contract.md` is still true.
- Confirm `docs/protocols/bot-trading-iron-law.md` still applies.
- Confirm `HANDOFF.md` and `ROADMAP.md` state current test count and latest screenshots.
- Confirm `public/briefings/latest.json` is safe read-only copy.
- Confirm no `.env`, `drive/`, `raw/`, `log.md`, local journal, or secret material is copied into the release artifact.
- Confirm any sales copy says "visualization/reward layer" and "not financial advice".

## Fail Closed

If any check fails:

1. Do not package the build.
2. Fix the smallest cause.
3. Rerun the failed check and the adjacent guardrail check.
4. Update `HANDOFF.md`, `ROADMAP.md`, and `wiki/context/session-memory.md` with the result.
