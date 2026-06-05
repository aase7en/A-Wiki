# Shopee Sale Handoff Checklist

> [verified 2026-06-05] Checklist for handing the Shopee buyer assistant work to another AI agent. Keep all account, payment, API, cookie, and permission evidence outside tracked git.

## Completed Context

- [x] Read A-Wiki session context from `agent-skills/README.md`, `wiki/context/wiki-overview.md`, and session memory fallback.
- [x] Run preflight with `python scripts/agent-preflight.py`.
- [x] Identify existing dirty working tree paths:
  - `scripts/userscripts/waste-form-ocr-fill.user.js`
  - `wiki/context/ocr-learning-log.md`
  - `wiki/synthesis/garbage-report-ocr.md`
  - `scripts/telegram-bot/`
  - `tests/test_waste_ocr_userscript.py`
- [x] Confirm A-Wiki policy: commit directly to `main`, no branch, no PR.
- [x] Confirm live background purchase must fail closed without written permission and official API scope.

## Remaining Work

- [ ] Re-check Shopee Thailand Terms on the implementation date.
- [ ] Re-check Shopee Open Platform docs for an official buyer checkout/payment path.
- [ ] Confirm written permission or official API scope for buyer-side automated purchase.
- [ ] Store permission evidence privately under `drive/private-tools/shopee-buyer-assistant/evidence/`.
- [ ] Build private runtime outside tracked git.
- [ ] Configure macOS Keychain or gitignored private config for secrets.
- [ ] Add a local `STOP_SHOPEE_BOT` kill switch.
- [ ] Run mock fixture tests.
- [ ] Run real cheap-item rehearsal after the user supplies a test link.
- [ ] Verify sanitized audit logs contain no secret or personal data.
- [ ] Run full A-Wiki verification.
- [ ] Stage only Shopee docs/runtime tests.
- [ ] Commit with `docs(shopee): add buyer assistant safety runbook`.
- [ ] Push with `git push origin main`.

## Agent Handoff Notes

- Do not touch unrelated OCR or Telegram work unless the user explicitly redirects.
- Do not create a branch or PR.
- Do not commit `drive/`, `raw/`, `.env`, cookies, API keys, screenshots with personal data, or raw payment logs.
- Do not implement live purchase with browser automation unless it is explicitly permitted by Shopee or the seller and complies with the safety protocol.
- If permission is missing, implement only manual-confirm mode.

## Verification Commands

```bash
python scripts/agent-preflight.py
python -m pytest tests/test_shopee_buyer_assistant_docs.py -v
python -m pytest tests/
python scripts/check-privacy.py
python scripts/gen-index.py --check
git status --short
git add docs/protocols/shopee-automation-safety.md docs/runbooks/shopee-sale-buyer-assistant.md docs/runbooks/shopee-sale-handoff-checklist.md tests/test_shopee_buyer_assistant_docs.py
git commit -m "docs(shopee): add buyer assistant safety runbook"
git push origin main
```
