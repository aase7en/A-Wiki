from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read_doc(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_shopee_safety_protocol_has_required_live_purchase_gates():
    text = read_doc("docs/protocols/shopee-automation-safety.md")

    required_phrases = [
        "[verified 2026-06-05]",
        "written permission",
        "official API",
        "buyer-side automated purchase",
        "manual-confirm mode",
        "fail closed",
        "CAPTCHA",
        "anti-bot",
        "macOS Keychain",
        "drive/",
        "STOP_SHOPEE_BOT",
        "5 units",
        "330 THB",
        "idempotency key",
        "sanitized audit log",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_shopee_runbook_is_actionable_for_mac_m1_sale_window():
    text = read_doc("docs/runbooks/shopee-sale-buyer-assistant.md")

    required_phrases = [
        "MacBook Pro M1",
        "Asia/Bangkok",
        "2026-06-06",
        "11:45",
        "12:00",
        "12:15",
        "30330278/50007410508",
        "66 THB",
        "Permission Gate",
        "Dry-run",
        "Live Run",
        "Rollback",
        "launchd",
        "caffeinate",
        "python scripts/agent-preflight.py",
        "python -m pytest tests/",
        "python scripts/check-privacy.py",
        "python scripts/gen-index.py --check",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_shopee_handoff_checklist_tracks_done_and_remaining_work():
    text = read_doc("docs/runbooks/shopee-sale-handoff-checklist.md")

    required_phrases = [
        "[x] Read A-Wiki session context",
        "[x] Run preflight",
        "[x] Identify existing dirty working tree paths",
        "[ ] Re-check Shopee Thailand Terms",
        "[ ] Confirm written permission or official API scope",
        "[ ] Build private runtime outside tracked git",
        "[ ] Run mock fixture tests",
        "[ ] Run real cheap-item rehearsal",
        "[ ] Stage only Shopee docs/runtime tests",
        "git push origin main",
    ]

    for phrase in required_phrases:
        assert phrase in text
