---
type: synthesis
title: "Premium Auto Trading Capability Hub"
slug: premium-auto-trading-capability-hub
tags: [capability-lane, auto-trading, risk-management, paper-trading, read-only-feed, security]
sources: [freqtrade-pi5, trading-rpg-project-brief-2026-05-30]
created: 2026-06-12
updated: 2026-06-12
---

# Premium Auto Trading Capability Hub

> [verified 2026-06-12] A-Wiki trading lane treats real-money automation as high-risk engineering. Premium means safer architecture, better testing, better auditability, and stronger risk gates, not faster live execution.

## Three Tiers

| Tier | Purpose | Allowed | Blocked |
|---|---|---|---|
| Paper | Strategy learning and UX/game feedback | Backtest, dry-run, mock PnL, simulated bot state | Real orders, real wallet authority |
| Read-only | Portfolio visibility and coaching | Sanitized snapshots, allocation, risk state | Buy/sell/order/cancel/withdraw |
| Live backend | Reviewed execution service | Server-side secrets, risk limits, kill switch, append-only audit | Browser secrets, direct exchange calls, LLM-to-order path |

## Route

| Step | Tooling | Done when |
|---|---|---|
| Research | Local wiki + verified official docs | Strategy/runtime claim has source and date |
| Paper bot | Freqtrade dry-run or sandbox equivalent | Fees, slippage, failed orders, and drawdown are modeled |
| Read-only feed | Backend-owned sanitized snapshots | Client has no provider keys and fails closed |
| Live review | Bot Trading Iron Law + security scan + risk tests | Human explicitly approves backend contract |

## Safety Gate

- No exchange/broker secrets in client, wiki, chat, source maps, logs, or generated assets.
- No unreviewed trading/exchange MCP server in the agent context.
- Live execution requires deterministic backend validation, spend/position/drawdown limits, idempotency, replay protection, and audit logs.

## Related

- [[synthesis/8-bit-trading-rpg-blueprint]]
- [[sources/freqtrade-pi5]]
- `docs/protocols/bot-trading-iron-law.md`
- PWQ feed contract — ย้ายไป product repo แล้ว (2026-07-12): `docs/pwq-read-only-feed-contract.md`
