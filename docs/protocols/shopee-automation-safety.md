# Shopee Automation Safety

> [verified 2026-06-05] Safety contract for any A-Wiki work that plans, documents, tests, or builds Shopee buyer assistance. Re-check Shopee Thailand Terms and Shopee Open Platform docs before any live run because platform rules and API scopes can change.

## Decision

A-Wiki may document and test a Shopee buyer assistant only when the default behavior is safe and non-executing. Any live background order flow must have written permission from Shopee or the seller plus an official API scope that explicitly permits buyer-side automated purchase and payment.

If written permission or official API support is missing, the system must use manual-confirm mode: it may open the item, monitor public price information, notify the user, and prepare a user-visible flow, but the user must personally confirm checkout and payment.

## Allowed Modes

| Mode | Allowed behavior | Live order? |
|---|---|---|
| Planning/docs | Runbooks, protocols, checklists, mock tests | No |
| Mock fixture | Deterministic local page/API fixtures | No |
| Manual-confirm mode | User-visible browser session, alerting, cart preparation where allowed | User confirms manually |
| Permissioned API mode | Official API only, with proof of allowed buyer checkout/payment scope | Yes, only within limits |

## Prohibitions

Every agent must reject or redesign any request that includes:

- CAPTCHA bypass, OTP automation, anti-bot evasion, stealth fingerprinting, device spoofing, unofficial mobile app access, or rate-limit bypass.
- Scraping private account data beyond what the user has explicitly authorized and what the platform permits.
- Storing Shopee cookies, session tokens, API keys, payment data, delivery address, phone number, OTP, QR payment data, or wallet balances in tracked git.
- Abnormal purchasing behavior outside the declared cap of 5 units and 330 THB base product spend.
- Silent fallback from permissioned API mode to browser automation.
- Any flow that proceeds after a permission, price, item identity, stock, payment, or audit check fails.

## Live Purchase Gate

Live background purchase is blocked unless all gates pass:

1. Permission evidence exists outside tracked git, preferably under `drive/private-tools/shopee-buyer-assistant/evidence/`.
2. The evidence names the target item or seller campaign and allows automated purchase/payment.
3. The selected official API supports buyer-side automated purchase for this account and market, not only seller order management.
4. Secrets are loaded from macOS Keychain or a gitignored file under `drive/`; never from tracked docs, tests, or source.
5. The configured item id matches `30330278/50007410508`.
6. The observed price is exactly 66 THB before each attempt.
7. The remaining unit cap is greater than zero, with an absolute maximum of 5 units.
8. The remaining base spend cap is enough, with an absolute maximum of 330 THB unless the user explicitly changes it in private config.
9. Each state-changing attempt has an idempotency key.
10. A sanitized audit log can be written before and after the attempt.

If any gate fails, fail closed and switch to manual-confirm mode or stop entirely.

## Runtime Safety

- Use a private runtime outside tracked git, such as `drive/private-tools/shopee-buyer-assistant/`, or a separate private repo.
- Use macOS Keychain for long-lived credentials when possible.
- Use a local kill switch named `STOP_SHOPEE_BOT`; if the file appears, stop before the next network or purchase action.
- Keep logs sanitized: timestamp, state, item id, observed price, attempt number, idempotency key hash, and result are acceptable.
- Do not log cookies, bearer tokens, API secrets, account identifiers, address, phone, payment instrument, OTP, QR code, wallet balance, or raw API payloads.
- Keep the system deterministic. An LLM may summarize status but must not decide whether to place a live order.

## Operational Limits

| Limit | Default |
|---|---|
| Sale window | 2026-06-06 12:00-12:15 Asia/Bangkok |
| Warm-up window | 2026-06-06 11:45-12:00 Asia/Bangkok |
| Target price | 66 THB |
| Quantity | 1 unit per attempt |
| Maximum quantity | 5 units |
| Maximum base product spend | 330 THB |
| Retry behavior | bounded retries with the same idempotency key for the same logical attempt |

## Required Evidence

Before live mode, store these private artifacts outside git:

- Permission note or written approval.
- API app id/scope screenshot or export with secrets redacted.
- Dry-run result against mock fixtures.
- Real cheap-item rehearsal result if the user provides a test item.
- Final config showing caps, sale window, target item id, and notification route.

## Verification

Run from A-Wiki before committing any tracked docs or tests:

```bash
python scripts/agent-preflight.py
python -m pytest tests/
python scripts/check-privacy.py
python scripts/gen-index.py --check
```

## References

- Shopee Thailand Terms of Service: https://help.shopee.co.th/portal/4/article/77241
- Shopee Open Platform: https://open.shopee.com/
