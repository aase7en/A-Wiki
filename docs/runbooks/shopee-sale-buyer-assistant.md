# Shopee Sale Buyer Assistant Runbook

> [verified 2026-06-05] Runbook for a MacBook Pro M1 buyer assistant targeting the 2026-06-06 12:00 Asia/Bangkok sale window. This document does not authorize live background purchase unless `docs/protocols/shopee-automation-safety.md` passes.

## Goal

Prepare a safe, handoff-ready workflow for the Shopee item `30330278/50007410508`:

```text
https://shopee.co.th/product/30330278/50007410508
```

The desired sale condition is 66 THB at 12:00 Thailand time on 2026-06-06. The hard cap is 5 units, one unit per attempt, and 330 THB base product spend unless the user privately changes the cap.

## Safety Boundary

Default to manual-confirm mode. Permissioned live mode is allowed only when:

- Shopee or the seller provides written permission for this buyer-side automated purchase.
- An official API supports buyer checkout/payment for this account and market.
- Secrets are stored outside tracked git in macOS Keychain or `drive/`.
- The kill switch, caps, price gate, item gate, and sanitized audit log are active.

Never implement CAPTCHA bypass, anti-bot evasion, stealth fingerprinting, OTP automation, unofficial app access, or rate-limit bypass.

## Permission Gate

Before building a live runtime:

1. Re-check Shopee Thailand Terms and Shopee Open Platform docs on the implementation date.
2. Save permission evidence under `drive/private-tools/shopee-buyer-assistant/evidence/`.
3. Confirm the API scope says buyer-side automated purchase or equivalent explicit language.
4. Confirm the target account is allowed to use that API path.
5. Record the pass/fail result in a private run log.

Fail closed if any item is unclear. Use manual-confirm mode instead.

## MacBook Pro M1 Setup

Target runtime:

- Hardware: MacBook Pro M1 at home.
- Timezone: Asia/Bangkok.
- Keep awake: use `caffeinate` during rehearsal and live windows.
- Scheduler: use `launchd` for the 11:45 start if a private runtime is later built.
- Secrets: use macOS Keychain first, or gitignored files under `drive/private-tools/shopee-buyer-assistant/`.
- Notifications: macOS notification is the default; Telegram is optional if token storage is private.

Private runtime location:

```text
drive/private-tools/shopee-buyer-assistant/
```

Do not place cookies, API keys, payment data, delivery data, screenshots with personal data, or raw logs in tracked A-Wiki files.

## Timeline

| Time Asia/Bangkok | State | Action |
|---|---|---|
| 2026-06-06 11:45 | Warm-up | Start private runtime with `caffeinate`; verify network, clock, login/API health, notification route |
| 2026-06-06 11:50 | Health check | Confirm target item id, caps, kill switch path, audit log path |
| 2026-06-06 11:58 | Armed | Poll only within allowed limits; do not purchase before the sale window |
| 2026-06-06 12:00 | Live gate | Proceed only if price is 66 THB and permission/API gates pass |
| 2026-06-06 12:00-12:15 | Live Run | Attempt one unit at a time; stop at 5 units, spend cap, permission failure, price mismatch, payment error, or kill switch |
| 2026-06-06 12:15 | Stop | Stop all purchase attempts and write final sanitized summary |

## Sale Logic

Each attempt must:

1. Check `STOP_SHOPEE_BOT`.
2. Confirm current time is inside 12:00-12:15 Asia/Bangkok.
3. Confirm item id is `30330278/50007410508`.
4. Confirm observed price is 66 THB.
5. Confirm remaining quantity cap and spend cap.
6. Generate or reuse the correct idempotency key.
7. Execute only through the permissioned official API.
8. Write sanitized audit events before and after the attempt.
9. Stop on success count 5, cap reached, stock unavailable, payment error, or any unexpected response.

In manual-confirm mode, step 7 becomes a user-visible prompt and the user performs checkout/payment manually.

## Dry-run

Run these before any live sale day:

- Mock fixture: deterministic product state with price not 66 THB, price exactly 66 THB, wrong item id, cap reached, payment failure, and duplicate retry.
- Cheap-item rehearsal: when the user supplies a real test link, run manual-confirm mode first, then permissioned API mode only if the Permission Gate passes.
- Log review: verify logs contain no cookies, tokens, address, phone, OTP, QR, wallet balance, or raw payment data.

## Live Run

Before 11:45:

- MacBook is plugged in.
- Wi-Fi or Ethernet is stable.
- Shopee account/wallet/payment readiness is checked by the user.
- Private runtime has current config and no tracked secrets.
- `STOP_SHOPEE_BOT` path is known and easy to create.

During 12:00-12:15:

- Do not edit tracked repo files.
- Watch sanitized notifications only.
- If anything looks wrong, create `STOP_SHOPEE_BOT`.

After 12:15:

- Stop the private runtime.
- Save a sanitized result summary.
- Keep raw private evidence outside git.

## Rollback

If the bot misbehaves or the platform flags the account:

1. Create `STOP_SHOPEE_BOT`.
2. Stop the `launchd` job or terminal process.
3. Remove private session state from the runtime folder.
4. Review sanitized audit logs.
5. Do not retry live purchase until the root cause is written down and the Permission Gate is rechecked.

## A-Wiki Verification

Run before committing tracked docs/tests:

```bash
python scripts/agent-preflight.py
python -m pytest tests/
python scripts/check-privacy.py
python scripts/gen-index.py --check
```

Stage only Shopee-related docs/tests. Leave unrelated dirty paths alone.

## References

- Safety protocol: `docs/protocols/shopee-automation-safety.md`
- Handoff checklist: `docs/runbooks/shopee-sale-handoff-checklist.md`
- Shopee Thailand Terms: https://help.shopee.co.th/portal/4/article/77241
- Shopee Open Platform: https://open.shopee.com/
