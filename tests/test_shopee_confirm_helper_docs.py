from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read_doc(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_confirm_helper_runbook_declares_manual_confirm_scope():
    text = read_doc("docs/runbooks/shopee-confirm-helper-tampermonkey.md")

    required_phrases = [
        "[verified 2026-06-05]",
        "manual-confirm",
        "Tampermonkey",
        "MacBook Pro M1",
        "Asia/Bangkok",
        "30330278/50007410508",
        "66 THB",
        "drive/private-tools/shopee-buyer-assistant/",
        "docs/protocols/shopee-automation-safety.md",
        "docs/runbooks/shopee-sale-buyer-assistant.md",
    ]

    for phrase in required_phrases:
        assert phrase in text, f"missing required phrase: {phrase}"


def test_confirm_helper_runbook_prohibits_auto_purchase_and_evasion():
    text = read_doc("docs/runbooks/shopee-confirm-helper-tampermonkey.md")

    prohibitions = [
        "No auto add-to-cart",
        "No auto checkout",
        "No auto payment",
        "No auto-click",
        "No CAPTCHA",
        "No OTP automation",
        "No anti-bot",
    ]

    for phrase in prohibitions:
        assert phrase in text, f"missing prohibition statement: {phrase}"


def test_confirm_helper_runbook_documents_schedule_and_stop_conditions():
    text = read_doc("docs/runbooks/shopee-confirm-helper-tampermonkey.md")

    schedule_phrases = [
        "KEEPALIVE",
        "ARMED",
        "TRIGGERED",
        "STOPPED",
        "15 minute",
        "11:59",
        "12:05",
        "1.5 second",
    ]

    for phrase in schedule_phrases:
        assert phrase in text, f"missing schedule phrase: {phrase}"

    stop_phrases = [
        "STOP on login",
        "STOP on CAPTCHA",
        "STOP button",
        "after 12:05",
    ]

    for phrase in stop_phrases:
        assert phrase in text, f"missing STOP condition: {phrase}"


def test_confirm_helper_runbook_documents_privacy_guarantees():
    text = read_doc("docs/runbooks/shopee-confirm-helper-tampermonkey.md")

    privacy_phrases = [
        "No fetch",
        "No XMLHttpRequest",
        "No cookie",
        "No payment data",
        "gitignored",
    ]

    for phrase in privacy_phrases:
        assert phrase in text, f"missing privacy phrase: {phrase}"
