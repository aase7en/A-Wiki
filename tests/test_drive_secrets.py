"""Tests for scripts/lib/drive_secrets.py env-var fallback.

Root problem: remote/cloud containers often have API keys as real env vars
(OPENROUTER_API_KEY, GROQ_API_KEY, ...) but no drive/.secrets file — every
fetch_secret() call used to fail there. The fallback must never apply to
WIKI_UNLOCK (or any future NEVER_CACHE entry): that value is compared against
an independently-read env var by check_claudemd_lock.py, and if fetch_secret
also fell back to the same env var, the "expected" and "provided" passwords
would always match trivially, disabling the lock.
"""
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import drive_secrets  # noqa: E402


def test_fetch_secret_falls_back_to_env_var_when_no_file(monkeypatch):
    monkeypatch.setattr(drive_secrets, "find_secrets_file", lambda: None)
    monkeypatch.setenv("SOME_TEST_API_KEY", "env-value-123")
    assert drive_secrets.fetch_secret("SOME_TEST_API_KEY") == "env-value-123"


def test_fetch_secret_prefers_file_over_env(monkeypatch, tmp_path):
    secrets_file = tmp_path / ".secrets"
    secrets_file.write_text("SOME_TEST_API_KEY=file-value\n", encoding="utf-8")
    monkeypatch.setattr(drive_secrets, "find_secrets_file", lambda: secrets_file)
    monkeypatch.setenv("SOME_TEST_API_KEY", "env-value-should-not-win")
    assert drive_secrets.fetch_secret("SOME_TEST_API_KEY") == "file-value"


def test_wiki_unlock_never_falls_back_to_env(monkeypatch):
    """Security-critical: WIKI_UNLOCK must NEVER be satisfied by os.environ,
    or check_claudemd_lock.py's expected-vs-provided comparison becomes a
    trivial self-match and the CLAUDE.md lock is disabled."""
    monkeypatch.setattr(drive_secrets, "find_secrets_file", lambda: None)
    monkeypatch.setenv("WIKI_UNLOCK", "some-value-set-by-user-shell")
    assert drive_secrets.fetch_secret("WIKI_UNLOCK") is None


def test_never_cache_set_contains_wiki_unlock():
    assert "WIKI_UNLOCK" in drive_secrets.NEVER_CACHE


def test_list_secret_names_unaffected_by_env(monkeypatch, tmp_path):
    """list_secret_names() must stay file-only — enumerating env vars would
    leak unrelated environment variable *names* into --list output."""
    secrets_file = tmp_path / ".secrets"
    secrets_file.write_text("FILE_KEY=x\n", encoding="utf-8")
    monkeypatch.setattr(drive_secrets, "find_secrets_file", lambda: secrets_file)
    monkeypatch.setenv("UNRELATED_ENV_VAR", "should-not-appear")
    assert drive_secrets.list_secret_names() == ["FILE_KEY"]
