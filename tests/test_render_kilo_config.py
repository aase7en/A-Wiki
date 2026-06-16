"""
Tests for the portable global Kilo config renderer (render_kilo_config.py).

Verifies: template hygiene (no real secrets, valid JSON, no .kilocode),
placeholder resolution, missing-secret provider drop, AI-config preservation,
MCP targets personal/ (never .secrets), Windows backslash path handling,
idempotent re-render, and command copying.

Iron Law #1: these tests precede/fail before implementation is correct.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import render_kilo_config as rkc  # noqa: E402

BUNDLED_TEMPLATE = REPO_ROOT / "scripts" / "lib" / "kilo.jsonc.template"

REAL_KEY_PATTERNS = [
    r"sk-or-v1-",        # OpenRouter
    r"AIzaSy[A-Za-z0-9_\-]{20,}",  # Google API key
    r"gsk_[A-Za-z0-9]{30,}",       # Groq
    r"sk-[a-f0-9]{32}",            # DeepSeek-ish
]


# ── Template hygiene ──────────────────────────────────────────────────────

def test_bundled_template_exists():
    assert BUNDLED_TEMPLATE.is_file(), "scripts/lib/kilo.jsonc.template must exist"


def test_template_parses_as_json():
    text = BUNDLED_TEMPLATE.read_text(encoding="utf-8")
    json.loads(text)  # strict JSON — raises if invalid / has comments


def test_template_has_no_real_secrets():
    text = BUNDLED_TEMPLATE.read_text(encoding="utf-8")
    for pat in REAL_KEY_PATTERNS:
        assert not re.search(pat, text), f"Template leaks secret matching {pat}"


def test_template_has_no_kilocode_reference():
    text = BUNDLED_TEMPLATE.read_text(encoding="utf-8")
    assert ".kilocode" not in text, "Template still references stale .kilocode path"


def test_template_uses_secret_placeholders():
    """Provider keys must be placeholders (__SECRET_*__), not absent or literal."""
    text = BUNDLED_TEMPLATE.read_text(encoding="utf-8")
    config = json.loads(text)
    providers = config.get("provider", {})
    assert providers, "Template should define a provider block"
    placeholders = []
    for prov in providers.values():
        ak = (prov.get("options") or {}).get("apiKey", "")
        if isinstance(ak, str) and ak.startswith("__SECRET_"):
            placeholders.append(ak)
    assert placeholders, "No __SECRET_*__ apiKey placeholders found in providers"


# ── Rendering: resolution + provider drop ─────────────────────────────────

def _render(template_text, drive_data, secrets):
    return rkc.render_config(template_text, drive_data, REPO_ROOT, secrets)


def test_placeholders_resolved_in_output(tmp_path):
    secrets = {"GEMINI_API_KEY": "fake-gemini", "OPENROUTER_API_KEY": "fake-or"}
    out = _render(BUNDLED_TEMPLATE.read_text(encoding="utf-8"), tmp_path, secrets)
    assert "__DRIVE_DATA__" not in out
    assert "__DRIVE_PERSONAL__" not in out
    assert "__DRIVE_SKILLS__" not in out
    assert "__REPO_ROOT__" not in out
    assert "__SECRET_" not in out


def test_missing_secret_drops_provider(tmp_path):
    # Only GEMINI present → google kept, every other secret-based provider dropped
    secrets = {"GEMINI_API_KEY": "fake-gemini"}
    out = _render(BUNDLED_TEMPLATE.read_text(encoding="utf-8"), tmp_path, secrets)
    config = json.loads(out)
    providers = config.get("provider", {})
    assert "google" in providers, "google (key present) must remain"
    assert (providers["google"].get("options") or {}).get("apiKey") == "fake-gemini"
    for missing in ("openrouter", "anthropic", "groq", "deepseek"):
        assert missing not in providers, f"{missing} (no key) must be dropped"


def test_default_model_and_agents_unchanged(tmp_path):
    tpl = json.loads(BUNDLED_TEMPLATE.read_text(encoding="utf-8"))
    out = _render(BUNDLED_TEMPLATE.read_text(encoding="utf-8"), tmp_path, {})
    rendered = json.loads(out)
    # Top-level AI defaults preserved verbatim
    for key in ("model", "small_model", "subagent_model", "default_agent"):
        assert rendered.get(key) == tpl.get(key), f"{key} changed by render"
    # Each agent's model preserved
    for name, agent in (tpl.get("agent") or {}).items():
        if "model" in agent:
            assert rendered["agent"][name]["model"] == agent["model"], \
                f"agent {name} model changed"


def test_mcp_targets_personal_not_secrets(tmp_path):
    out = _render(BUNDLED_TEMPLATE.read_text(encoding="utf-8"), tmp_path, {})
    config = json.loads(out)
    drive_mcp = config.get("mcp", {}).get("drive-files", {})
    args = " ".join(drive_mcp.get("command", []) + [str(a) for a in drive_mcp.get("args", [])])
    assert "personal" in args, "drive-files MCP must target personal/"
    assert ".secrets" not in args, "drive-files MCP must NOT expose .secrets"


# ── Cross-platform + idempotency ──────────────────────────────────────────

def test_windows_backslash_path_produces_valid_json(tmp_path):
    # A Windows-style drive root with backslashes must survive json.dumps escaping
    win_drive = Path("C:/Users/work/Google Drive/A-Wiki-Data")
    out = rkc.render_config(
        BUNDLED_TEMPLATE.read_text(encoding="utf-8"), win_drive, REPO_ROOT, {}
    )
    again = json.loads(out)  # must re-parse → no broken escaping
    cmd = (again.get("mcp", {}).get("drive-files", {}).get("command", []))
    joined = " ".join(str(c) for c in cmd)
    assert "personal" in joined


def test_idempotent_rerender(tmp_path):
    secrets = {"GEMINI_API_KEY": "k1"}
    text = BUNDLED_TEMPLATE.read_text(encoding="utf-8")
    a = rkc.render_config(text, tmp_path, REPO_ROOT, secrets)
    b = rkc.render_config(text, tmp_path, REPO_ROOT, secrets)
    assert a == b, "Re-rendering the same inputs must be byte-identical"


# ── Command copying ───────────────────────────────────────────────────────

def test_copy_commands_copies_md_files(tmp_path):
    src = tmp_path / "src"
    dest = tmp_path / "dest"
    src.mkdir()
    (src / "drive.md").write_text("---\ndescription: x\n---\nbody", encoding="utf-8")
    (src / "journal.md").write_text("hi", encoding="utf-8")
    (src / "README.txt").write_text("ignore me", encoding="utf-8")  # non-md
    copied = rkc.copy_commands(src, dest)
    assert (dest / "drive.md").is_file()
    assert (dest / "journal.md").is_file()
    assert not (dest / "README.txt").exists()
    assert len(copied) == 2


# ── Drive detection (env override path) ───────────────────────────────────

def test_detect_drive_via_env_override(tmp_path, monkeypatch):
    fake = tmp_path / "A-Wiki-Data"
    fake.mkdir()
    (fake / ".secrets").write_text("GEMINI_API_KEY=x\n", encoding="utf-8")
    monkeypatch.setenv("A_WIKI_DRIVE_PATH", str(fake))
    found = rkc.detect_drive_data_root()
    assert found == fake
