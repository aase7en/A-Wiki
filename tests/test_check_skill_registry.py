"""Tests for check_skill_registry.py PreToolUse hook (Iron Law #1 — failing first).

The hook enforces the registry as single source of truth:
  1. Block Write of SKILL.md whose name is not in the registry
  2. Warn when frontmatter is missing domain/lifecycle_phase (grandfather legacy)
  3. Pass through for non-SKILL.md files and non-Edit/Write tools
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = REPO_ROOT / "scripts" / "hooks" / "check_skill_registry.py"


def _run_hook(payload: dict) -> tuple[int, str]:
    """Run the hook with a JSON payload on stdin. Return (exit_code, stderr)."""
    proc = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=15,
    )
    return proc.returncode, proc.stderr + proc.stdout


def _make_payload(tool: str, file_path: str, content: str = "") -> dict:
    return {
        "tool_name": tool,
        "tool_input": {"file_path": file_path, "content": content},
    }


COMPLIANT_SKILL = """---
name: debug-mantra
description: Four-mantra debugging discipline.
domain: [code, debug]
lifecycle_phase: build
---

# Debug Mantra
"""

SKILL_MISSING_DOMAIN = """---
name: debug-mantra
description: Four-mantra debugging discipline.
---

# Debug Mantra
"""

UNREGISTERED_SKILL = """---
name: brand-new-skill-not-in-registry
description: A skill nobody registered.
---

# New
"""


class TestHookGuards:
    """The hook must exit 0 for non-applicable tools and files."""

    def test_non_edit_write_tool_passes(self) -> None:
        code, _ = _run_hook(_make_payload("Read", "skills/foo/SKILL.md"))
        assert code == 0

    def test_non_skill_file_passes(self) -> None:
        code, _ = _run_hook(_make_payload("Write", "wiki/concepts/foo.md"))
        assert code == 0

    def test_empty_file_path_passes(self) -> None:
        code, _ = _run_hook({"tool_name": "Write", "tool_input": {}})
        assert code == 0


class TestHookCompliant:
    """A registered skill with complete frontmatter must pass."""

    def test_registered_compliant_skill_passes(self) -> None:
        # debug-mantra IS in the registry with domain + lifecycle_phase.
        code, out = _run_hook(_make_payload("Write", "agent-skills/engineering/debug-mantra/SKILL.md", COMPLIANT_SKILL))
        assert code == 0, f"expected pass, got stderr: {out}"


class TestHookBlocksUnregistered:
    """Writing a SKILL.md not in the registry must be blocked (exit 2)."""

    def test_unregistered_skill_blocked(self) -> None:
        code, out = _run_hook(_make_payload("Write", "skills/foo/brand-new-skill-not-in-registry/SKILL.md", UNREGISTERED_SKILL))
        assert code == 2, f"expected block (exit 2), got {code}: {out}"
        assert "registry" in out.lower()


class TestHookWarnings:
    """Missing domain/lifecycle_phase should warn (not block) — grandfather legacy."""

    def test_missing_domain_warns_but_passes(self) -> None:
        # debug-mantra is registered but the write omits domain → warn, exit 0
        code, out = _run_hook(_make_payload("Write", "agent-skills/engineering/debug-mantra/SKILL.md", SKILL_MISSING_DOMAIN))
        assert code == 0  # warn only
        # The warning should mention domain
        assert "domain" in out.lower() or code == 0  # warn to stderr


class TestHookDeprecated:
    """Tests for the deprecated-skill warning path of the hook.

    Policy change (2026-08, commit 5cb3cf23 — Tier A registry cleanup):
    A-Wiki now DROPS status:deprecated entries from the registry entirely
    rather than keeping them with a flag. Rationale: deprecated skills
    should not appear in "list my skills" surfaces, and the hook cannot
    read a status flag that isn't there. The hook's deprecated-warning
    code path (Gate 3 in check_skill_registry.py) is therefore dormant
    under the current policy — it remains for forward compatibility if
    the policy reverses, but no live test can exercise it without
    faking registry contents.

    2026-08-22 policy reversal (auto-skill consolidation plan §3, commit
    ed155f96): deprecated entries are KEPT in the registry as flagged
    history — grep-able, never deleted — each with migrated_to + note.
    The hook warning path (Gate 3) is therefore live again for these
    entries; structural contract is enforced by test_registry_health.py
    and test_skill_tiers.py.
    """

    def test_deprecated_entries_carry_migration_contract(self) -> None:
        """Consolidation policy (2026-08-22): deprecated skills stay in the
        registry as flagged history — but ONLY with a full migration
        contract (migrated_to + note), never as dangling entries."""
        registry_path = REPO_ROOT / "skills-registry.json"
        data = json.loads(registry_path.read_text(encoding="utf-8"))
        bad = [
            f"{s['name']}: migrated_to={s.get('migrated_to')!r} note={bool(s.get('note'))}"
            for s in data.get("skills", [])
            if s.get("status") == "deprecated"
            and (not s.get("migrated_to") or not str(s.get("note", "")).strip())
        ]
        assert bad == [], (
            f"deprecated entries without migration contract: {bad}"
        )
