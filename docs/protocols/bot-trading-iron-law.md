# Bot Trading Iron Law

> [verified 2026-06-05] Sunday Invest Moon's game client is a simulation and visualization surface only. It must never possess trading credentials or execute real orders.

## Decision

The client-side `BotFeed` seam may configure and display deterministic mock bot results. The default must remain `MockBotFeed`. `RemoteBotFeed` must remain unavailable until a separately reviewed backend implements the contract below.

Current product seam:

- `pixel-wealth-quest/src/feeds/tradingBotFeed.ts`
- `BotFeed.getStatus(deviceId)` reads sanitized bot status.
- `BotFeed.setStrategy(deviceId, config)` changes simulation configuration.
- Planned mock endpoint shape: `GET/PUT /api/sim/bots/:deviceId`.

Changing the default from `MockBotFeed` to a remote implementation requires an explicit security review. A one-line adapter swap is not permission to bypass this protocol.

## Client Prohibitions

Every agent must reject any client-side implementation that:

1. Stores, reads, displays, logs, or transmits exchange/broker API keys, secrets, passphrases, private keys, seed phrases, cookies, withdrawal credentials, or signed requests.
2. Connects directly from the browser/game client to an exchange or broker.
3. Creates, modifies, cancels, or submits real orders or withdrawals.
4. Signs exchange/broker requests in the client.
5. Exposes secrets through `import.meta.env`, `window`, local/session storage, IndexedDB, URLs, source maps, errors, analytics, or telemetry.
6. Lets an LLM output become an executable order without deterministic server-side validation and risk controls.
7. Silently falls back from mock mode to live trading.

## Future Backend Contract

A future remote adapter is allowed only when a separate backend owns all sensitive and executable behavior:

| Concern | Required backend behavior |
|---|---|
| Authentication | Use an authenticated server session; never return provider credentials to the client. |
| Secret storage | Keep credentials in a server-side secret manager or equivalent encrypted store. |
| Request signing | Sign provider requests on the server only, after authorization and validation. |
| Idempotency | Require an idempotency key for every state-changing request and safely replay the prior result. |
| Replay protection | Validate timestamp/nonce and reject stale or duplicate signed operations. |
| Risk controls | Enforce allowlisted instruments, position/exposure limits, drawdown stops, and a kill switch before execution. |
| Permissions | Use least-privilege credentials with withdrawals disabled. |
| Auditability | Record actor, intent, validation result, idempotency key, provider result, and timestamp in an append-only audit trail. |
| Responses | Return only sanitized configuration, status, equity, P&L, drawdown, and risk state. |
| Failure mode | Fail closed; rate-limit requests and stop execution when validation, provider, or audit dependencies fail. |

The game client remains a control/status UI. It may request an operation from the backend, but it cannot decide that the operation is safe or perform it itself.

## Agent Checklist

Before changing any trading-related client or adapter:

- Confirm `MockBotFeed` is still the default.
- Confirm remote/live paths cannot execute.
- Scan client code and build output for secret-looking environment variables and credentials.
- Verify no real exchange/broker network call is reachable from the client.
- Add a failing test first for any production-code change.
- Stop and request a security review before enabling a remote or live adapter.

## Verification

```bash
# Product
npm --prefix ../sunday-estate-webapp/pixel-wealth-quest test -- --run
npm --prefix ../sunday-estate-webapp/pixel-wealth-quest run typecheck

# A-Wiki
python3 scripts/check-privacy.py
python3 scripts/verify-cross-platform.py
python3 scripts/gen-index.py --check
```

