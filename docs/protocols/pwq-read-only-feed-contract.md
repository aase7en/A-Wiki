# PWQ Read-only Feed Contract

> [verified 2026-06-05] Sunday Invest Moon may display real portfolio snapshots only through a backend-owned read-only contract. The Vite/browser client must remain a visualization surface with no provider secrets and no execution path.

## Decision

`pixel-wealth-quest/src/adapters/portfolioFeed.ts` is the only approved client seam for portfolio snapshots.

Allowed client surface:

- `PortfolioFeed.getSnapshot()` reads a sanitized `PortfolioSnapshot`.
- `PortfolioFeed.subscribe(onSnapshot)` receives sanitized snapshot updates.
- `createPortfolioFeed()` defaults to the mock feed.
- `createLiveReadOnlyFeed()` is a fail-closed shell until a backend contract exists.

The client may show balances, allocation, and day-change values. It must not hold credentials, submit financial actions, or decide that any financial action is safe.

## Required Backend Shape

Any future live portfolio feed must be backend-owned:

| Concern | Required behavior |
|---|---|
| Authentication | Use an authenticated server session. Do not pass provider credentials to the client. |
| Secret storage | Store provider keys/tokens only server-side, outside git and outside Vite env. |
| Provider calls | Backend calls read-only provider endpoints; browser calls only the product backend. |
| Response shape | Return sanitized `PortfolioSnapshot` data only: holdings, values, source, `asOf`, and derived display fields. |
| Permissions | Use least-privilege read-only provider permissions where available. |
| Caching | Cache/smooth snapshots server-side to avoid provider spam and UI jitter. |
| Auditability | Log backend source, timestamp, user/session id, and sanitization result without logging secrets. |
| Failure mode | Fail closed to mock/cached display. Never silently escalate into executable behavior. |

## Client Prohibitions

Reject any change that adds one of these to `pixel-wealth-quest/src/`:

1. API keys, provider tokens, exchange credentials, broker secrets, passphrases, private keys, seed phrases, or signed requests.
2. Direct browser calls to a provider, broker, exchange, or OpenRouter/Gemini-style generation endpoint for portfolio data.
3. Methods or UI that order, trade, buy, sell, submit, execute, withdraw, or cancel a financial operation.
4. Storage of secrets in `import.meta.env`, `window`, local/session storage, IndexedDB, URLs, source maps, errors, analytics, or telemetry.
5. A flag path that silently switches from mock to live without the explicit compliance gate and backend contract review.

## Feature Flag Rule

Both client flags are required, and both are still insufficient by themselves:

| Flag | Meaning |
|---|---|
| `VITE_PWQ_LIVE_READ_ONLY_FEED=1` | The app is allowed to try the live read-only selector. |
| `VITE_PWQ_COMPLIANCE_APPROVED=1` | Compliance review has approved the backend contract for this environment. |

Even with both flags, `createLiveReadOnlyFeed()` must remain fail-closed until the backend implementation exists and is reviewed.

## Repeatable Verification

From `pixel-wealth-quest/`:

```bash
npm run feed:scan
npm test -- --run src/adapters/portfolioFeed.test.ts tools/scan-feed-boundary.test.mjs
npm test -- --run
npm run typecheck
npm run build
npx react-doctor@latest --verbose --diff
```

> **Roadmap moved (2026-07-12)**: the single canonical roadmap now lives in the
> product repo at `pixel-wealth-quest/ROADMAP.md` — the A-Wiki mirror and
> `sync_sunday_invest_moon_roadmap.py` (+ its test) are retired. Edit the
> roadmap in the product repo directly; no sync step needed.

## Agent Checklist

- Confirm `createPortfolioFeed()` still returns mock by default.
- Confirm `createLiveReadOnlyFeed()` still fails closed without a backend contract.
- Run `npm run feed:scan` before marking any feed-related ticket done.
- If legal/compliance specifics are needed, verify against current official sources before writing them. This protocol is an engineering safety contract, not legal advice.
