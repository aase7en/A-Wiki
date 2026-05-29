from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DRIVE_SECRETS_PATH = REPO_ROOT / "scripts" / "lib" / "drive_secrets.py"

spec = importlib.util.spec_from_file_location("drive_secrets", DRIVE_SECRETS_PATH)
drive_secrets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(drive_secrets)


def test_parse_secrets_ignores_comments_and_exports(tmp_path):
    path = tmp_path / ".secrets"
    path.write_text(
        "# comment\n"
        "export OPENROUTER_API_KEY='sk-or-v1-example'\n"
        "GEMINI_API_KEY=\"AIza-example\"\n"
        "BAD_LINE\n",
        encoding="utf-8",
    )

    parsed = drive_secrets.parse_secrets_file(path)

    assert parsed == {
        "OPENROUTER_API_KEY": "sk-or-v1-example",
        "GEMINI_API_KEY": "AIza-example",
    }


def test_list_secret_names_does_not_return_values(tmp_path, monkeypatch):
    secrets = tmp_path / ".secrets"
    secrets.write_text("OPENROUTER_API_KEY=sk-or-v1-secret-value\n", encoding="utf-8")

    monkeypatch.setattr(drive_secrets, "find_secrets_file", lambda: secrets)

    assert drive_secrets.list_secret_names() == ["OPENROUTER_API_KEY"]


def test_fetch_secret_returns_requested_value(tmp_path, monkeypatch):
    secrets = tmp_path / ".secrets"
    secrets.write_text("WIKI_UNLOCK=abc123\n", encoding="utf-8")

    monkeypatch.setattr(drive_secrets, "find_secrets_file", lambda: secrets)

    assert drive_secrets.fetch_secret("WIKI_UNLOCK") == "abc123"
    assert drive_secrets.fetch_secret("MISSING") is None
