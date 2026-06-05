# Shopee Confirm Helper — Tampermonkey (manual-confirm)

> [verified 2026-06-05] Runbook for a manual-confirm Tampermonkey userscript that helps a human buyer act fast at the 2026-06-06 12:00 Asia/Bangkok sale window for Shopee item `30330278/50007410508` at the 66 THB target. The userscript never clicks buy/checkout/payment by itself. This runbook lives in tracked git; the userscript file itself lives gitignored under `drive/private-tools/shopee-buyer-assistant/`.

## Scope

This is a **manual-confirm** helper. The script:

- Keeps the product page session warm during the morning.
- Refreshes the page faster during the armed window.
- Detects the 66 THB target price on the rendered page.
- Alerts the human with overlay + sound + highlight on the buy button.
- Auto-stops on login, CAPTCHA, OTP, or post-deadline.

The human user clicks `ซื้อเลย`, `ใส่รถเข็น`, and any checkout / payment buttons themselves. The script does not click them.

Parent safety contract: `docs/protocols/shopee-automation-safety.md` ("Allowed Modes" → manual-confirm). Sale window context and timeline: `docs/runbooks/shopee-sale-buyer-assistant.md`.

## Prohibited Behavior

The userscript must not implement any of the following, and any future edit that tries to add them must be rejected:

- **No auto add-to-cart.** The script may highlight the cart button; it does not call `.click()` on it.
- **No auto checkout.** The script may surface the checkout button; it does not press it.
- **No auto payment.** The script does not touch wallet, QR, card, OTP entry, or address fields.
- **No auto-click.** The script does not synthesize click, touch, or keyboard events against Shopee UI.
- **No CAPTCHA bypass or solver.** If a CAPTCHA appears, the script stops and shows it to the human.
- **No OTP automation.** The script never reads, fills, or forwards OTP codes.
- **No anti-bot evasion.** No fingerprint spoofing, no stealth UA, no rate-limit games, no headless tricks.

If any of these is needed in the future, the safety protocol requires written permission from Shopee or the seller plus an official API path, not a userscript.

## Runtime Layout

| Path | Tracked | Purpose |
|---|---|---|
| `docs/runbooks/shopee-confirm-helper-tampermonkey.md` | yes | This runbook |
| `tests/test_shopee_confirm_helper_docs.py` | yes | Doc-shape test (no live network) |
| `drive/private-tools/shopee-buyer-assistant/shopee-confirm-helper.user.js` | **no, gitignored** | The userscript itself |
| `drive/private-tools/shopee-buyer-assistant/evidence/` | **no, gitignored** | Future permission evidence if any |

`drive/` is a per-user symlink to private cloud storage; it is gitignored. The userscript ships through that path so it syncs between the user's Windows desktop and MacBook Pro M1 without ever touching tracked git.

## Install on MacBook Pro M1

1. Install Tampermonkey for Chrome from the Chrome Web Store.
2. Ensure `drive/` symlink is healthy: `bash scripts/setup-cloud-link.sh --status`.
3. Open Tampermonkey dashboard → **Utilities** → **Import from file** → select `drive/private-tools/shopee-buyer-assistant/shopee-confirm-helper.user.js`.
4. Confirm install. The userscript appears in the dashboard and is enabled.
5. Log into `https://shopee.co.th` in the same Chrome profile.
6. Visit `https://shopee.co.th/product/30330278/50007410508` once before sale day to confirm the overlay appears at top-right.

The script does not prompt for any secret. There is no API key, no token, no cookie copy step.

## Schedule (Asia/Bangkok local time)

The script reads Asia/Bangkok wall-clock time via `Intl.DateTimeFormat('en-CA', {timeZone: 'Asia/Bangkok'})` so it works even if the Mac is set to a different timezone.

| Window | State | Behavior |
|---|---|---|
| Before 11:59 | KEEPALIVE | `location.reload()` every 15 minutes to keep the Shopee session warm |
| 11:59-12:05 | ARMED | `location.reload()` every 1.5 second with ±250 ms jitter; check price after each load |
| Price = 66 THB while ARMED | TRIGGERED | Stop all timers, raise overlay, sound alert, scroll buy button into view, highlight it |
| After 12:05 | STOPPED | All timers cleared; overlay shows final state; no further reloads |

The 15 minute KEEPALIVE interval is conservative on purpose. Shopee tolerates a casual logged-in tab better than a fast poller; the goal of KEEPALIVE is only to avoid session expiry, not to scout for early price changes.

The 1.5 second ARMED interval matches normal user-driven refresh-spamming behavior and stays inside Shopee's normal rate window for an authenticated tab. The jitter avoids a perfectly periodic pattern.

## STOP Conditions (auto, no click)

The script transitions to STOPPED without clicking anything when any of these are observed:

- **STOP on login.** Current URL matches `/buyer/login` or `/login`. Indicates the session expired.
- **STOP on CAPTCHA.** DOM text contains `CAPTCHA`, `ยืนยันตัวตน`, `รหัสยืนยัน`, `verify`, or a known Shopee challenge marker.
- **STOP on OTP.** DOM text contains `OTP`, `รหัส OTP`, or an OTP input is focused.
- **STOP button.** The overlay STOP button clears all timers and freezes state.
- **STOP after 12:05.** The local Asia/Bangkok clock crossed the sale window deadline.
- **Hidden tab guard.** If the tab is `document.hidden` while ARMED, the trigger is suppressed (avoids false positives on a price flash the human cannot react to anyway).

When stopped on login, CAPTCHA, or OTP, the human is shown the screen and asked to handle it manually. The script does not attempt to forward, paste, or fill anything.

## Overlay

A small fixed `<div>` at top-right shows:

- Current state: `KEEPALIVE`, `ARMED`, `TRIGGERED`, `STOPPED`.
- Countdown to the next reload and to the deadline.
- Last observed price.
- A red STOP button.

When TRIGGERED, the overlay grows into a full-screen red banner with the message "ราคา ฿66 — กดซื้อเลย / ใส่รถเข็น เอง". A short audio alert (in-memory data-URI tone, no external download) plays. The buy button is given a thick red outline and scrolled into view. `document.title` flashes between two strings and `window.focus()` is called.

The script never calls `.click()`, `.dispatchEvent()`, `.submit()`, or `KeyboardEvent` on any Shopee element.

## Privacy Guarantees

- **No fetch.** The script does not call `fetch()`.
- **No XMLHttpRequest.** The script does not use `XMLHttpRequest` or `GM_xmlhttpRequest`.
- **No cookie read.** The script does not read `document.cookie` or any storage that would expose session tokens.
- **No payment data.** Wallet balance, card numbers, addresses, phone numbers, QR data, and OTPs are never read, parsed, or stored.
- **Local-only storage.** `GM_setValue` stores only `targetPrice` (default 66) and a boolean `debug` flag. Nothing else.
- **gitignored.** The userscript and any future evidence stay under `drive/private-tools/shopee-buyer-assistant/`, never in tracked git.

A sanitized console log line `[shopee-confirm] state=<STATE> price=<PRICE>` is emitted at state transitions; no identifiers, tokens, or selectors that leak account state are logged.

## Dry-Run

Before sale day, run these on the Mac:

1. Build a mock HTML file under `drive/private-tools/shopee-buyer-assistant/mocks/` containing one `<div>` with `฿120.00` and a placeholder buy button. Temporarily add `// @match file://*` to the script. Open the file in Chrome. Expect: KEEPALIVE state, no trigger.
2. Edit the mock to show `฿66.00`. Reload. Expect: TRIGGERED state, audio, overlay, highlight, no click on the placeholder button.
3. Create a mock with the text `กรอก OTP`. Expect: STOPPED.
4. Create a mock at `file:///.../buyer-login.html` and add it to `@match` for the test. Expect: STOPPED.
5. Remove the temporary `@match file://*` line before going live.

These steps stay entirely on the Mac and never call Shopee.

## Live Day (2026-06-06)

| Time | Action |
|---|---|
| Night before | Plug in MacBook, run `caffeinate -dis` in Terminal, confirm Chrome is logged into Shopee |
| 11:45 | Open `https://shopee.co.th/product/30330278/50007410508` in a Chrome tab. Confirm overlay shows KEEPALIVE. Leave the tab focused |
| 11:58 | Remote into the Mac from wherever you are. Keep the Shopee tab visible and focused |
| 11:59 | Overlay flips to ARMED. Do not switch tabs |
| 12:00 | Sale opens. If price stays high, the script keeps refreshing. If price hits 66 THB, the script enters TRIGGERED and surfaces the button. **You click ซื้อเลย / ใส่รถเข็น yourself** |
| 12:00-12:05 | If a CAPTCHA, OTP, or login challenge appears, the script stops and shows you the screen. Handle it manually |
| 12:05 | Script auto-stops. If you have not bought, accept the outcome — there is no auto-retry |

If anything looks wrong, click the overlay STOP button. The script clears its timers and waits.

## Troubleshoot

| Symptom | Action |
|---|---|
| Overlay not visible | Confirm Tampermonkey is enabled (icon in toolbar). Reload the tab. Check the `@match` URL matches the page exactly |
| Script keeps refreshing past 12:05 | Mac clock is wrong or timezone is off. Verify with `date`. The script trusts the system clock via `Intl.DateTimeFormat` with `Asia/Bangkok` |
| TRIGGERED fires on the wrong price | The DOM price node may have changed. Inspect the price element, copy its text, confirm it matches the regex `/฿\s*66(?:\.\d{1,2})?\b/`. Update the script's price selector if Shopee changed the layout |
| STOP on CAPTCHA does not fire | Add the new challenge marker text to the STOP keyword list in the script. Open Tampermonkey dashboard, edit, save, reload Shopee |
| Audio does not play | Chrome blocks autoplay until the tab has user interaction. Click anywhere in the tab once at 11:58 |
| Buy button not highlighted | Shopee changed the button class. Inspect the buy button, update the selector in the script. Never replace the highlight with an auto-click |

## References

- Safety contract: `docs/protocols/shopee-automation-safety.md`
- Sale-day runbook: `docs/runbooks/shopee-sale-buyer-assistant.md`
- Handoff checklist: `docs/runbooks/shopee-sale-handoff-checklist.md`
- Userscript precedent (waste form): `scripts/userscripts/waste-form-ocr-fill.user.js`
- Shopee Thailand Terms: https://help.shopee.co.th/portal/4/article/77241
- Shopee Open Platform: https://open.shopee.com/
