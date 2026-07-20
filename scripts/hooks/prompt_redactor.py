#!/usr/bin/env python3
"""
prompt_redactor.py — Privacy redaction for prompt logging (Y1).

แทนที่ secrets + machine paths + emails + codenames ด้วย *** ก่อนเก็บ prompt
ลง .tmp/prompts/ (opt-in via AWIKI_LOG_PROMPTS=1, local-only, gitignored).

Reuse patterns from:
  - check_secret_leak.py: SECRET_PATTERNS (API keys, tokens, JWT)
  - check-privacy.py: HOME_PATH_PATTERNS, CLOUDSTORAGE_PATTERNS, EMAIL_PATTERN

redact(text) is a PURE function — no I/O, no side effects.
"""
from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Patterns (reuse from sibling modules — single source of truth)
# ---------------------------------------------------------------------------
# Secrets: API keys, tokens, JWT (from check_secret_leak.py SECRET_PATTERNS)
_SECRET_REGEXES = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{24,}\b"),           # OpenAI/Anthropic/OpenRouter
    re.compile(r"\bsk-or-v1-[A-Za-z0-9_-]{24,}\b"),      # OpenRouter v1
    re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b"),            # Google API key
    re.compile(r"\bgsk_[0-9A-Za-z]{24,}\b"),              # Groq
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{30,}\b"),       # GitHub classic
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{40,}\b"),      # GitHub fine-grained
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),                  # AWS access key
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),     # Slack token
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),  # JWT
]

# Machine paths (from check-privacy.py HOME_PATH_PATTERNS)
_PATH_REGEXES = [
    re.compile(r"/Users/[A-Za-z0-9._-]+/"),               # macOS
    re.compile(r"/home/[A-Za-z0-9._-]+/"),                # Linux
    re.compile(r"C:\\\\Users\\\\[A-Za-z0-9._-]+\\\\"),    # Windows escaped
    re.compile(r"C:/Users/[A-Za-z0-9._-]+/"),             # Windows forward-slash
]

# Cloud storage paths with account names
_CLOUDSTORAGE_REGEXES = [
    re.compile(r"GoogleDrive-[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    re.compile(r"OneDrive-[A-Za-z0-9._-]+(?!\*)"),
    re.compile(r"Dropbox-[A-Za-z0-9._-]+(?!\*)"),
]

# Email addresses (excluding whitelist domains — reuse from check-privacy)
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_EMAIL_WHITELIST_DOMAINS = {
    "example.com", "example.org", "example.net",
    "a-wiki.local", "test.local",
    "noreply.github.com", "users.noreply.github.com",
    "anthropic.com", "github.com", "gitlab.com",
    "deepseek.com",
}


_REDACT_MARKER = "***"


def redact(text: Any) -> str:
    """แทนที่ secrets + machine paths + emails + cloud storage ด้วย ***.

    Pure function — no I/O. Returns empty string for None/empty input.
    Preserves normal text (English + Thai + technical terms).
    """
    if not text:
        return ""
    result = str(text)

    # Secrets
    for rx in _SECRET_REGEXES:
        result = rx.sub(_REDACT_MARKER, result)

    # Machine paths
    for rx in _PATH_REGEXES:
        result = rx.sub(_REDACT_MARKER, result)

    # Cloud storage
    for rx in _CLOUDSTORAGE_REGEXES:
        result = rx.sub(_REDACT_MARKER, result)

    # Emails (respect whitelist)
    def _email_replacer(m):
        domain = m.group(0).split("@", 1)[-1].lower() if "@" in m.group(0) else ""
        if domain in _EMAIL_WHITELIST_DOMAINS:
            return m.group(0)  # whitelisted domain → keep
        return _REDACT_MARKER
    result = _EMAIL_RE.sub(_email_replacer, result)

    return result


__all__ = ["redact"]
