"""tests/test_skill_registry_ports.py — contract suite for ADR-0012 slice A3.

Same shape as test_ports_contract.py: runs identical assertions against every
adapter of SkillRegistryPort + SkillRegistryWriterPort. Catches prod/mock
divergence (R10 mitigation) and proves each port is a real seam.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

from ports import SkillRegistryPort, SkillRegistryWriterPort  # noqa: E402
from adapters.skill_registry import (  # noqa: E402
    FileSkillRegistryAdapter, InMemorySkillRegistryAdapter,
    AtomicSkillRegistryWriterAdapter, InMemorySkillRegistryWriterAdapter,
)


# ── Structural: both adapters satisfy their port ───────────────────────
def test_adapters_satisfy_port_protocols():
    assert isinstance(FileSkillRegistryAdapter(), SkillRegistryPort)
    assert isinstance(InMemorySkillRegistryAdapter(), SkillRegistryPort)
    store = InMemorySkillRegistryAdapter()
    assert isinstance(AtomicSkillRegistryWriterAdapter(), SkillRegistryWriterPort)
    assert isinstance(InMemorySkillRegistryWriterAdapter(store), SkillRegistryWriterPort)


# ── SkillRegistryPort contract ──────────────────────────────────────────
def test_registry_get_returns_dict_for_existing_skill():
    """The real registry must resolve a known skill name."""
    adapter = FileSkillRegistryAdapter()
    # 'a-think' is canonical + stable across registry refreshes
    skill = adapter.get("a-think")
    assert skill is not None
    assert isinstance(skill, dict)
    assert skill.get("name") == "a-think"


def test_registry_get_returns_none_for_missing():
    adapter = FileSkillRegistryAdapter()
    assert adapter.get("does-not-exist-zzz") is None


def test_inmemory_registry_roundtrip():
    """The mock must resolve names it was seeded with, including via alias."""
    adapter = InMemorySkillRegistryAdapter(skills=[
        {"name": "demo", "aliases": ["old-name"], "category": "test"},
    ])
    assert adapter.get("demo") is not None
    assert adapter.get("demo").get("category") == "test"
    # alias resolution
    assert adapter.get("old-name") is not None
    assert adapter.get("missing") is None


def test_inmemory_registry_load_returns_shim_with_get():
    """load() must return an object whose .get() works (matches Registry shape)."""
    adapter = InMemorySkillRegistryAdapter(skills=[{"name": "x"}])
    reg = adapter.load()
    assert reg.get("x") is not None
    assert reg.get("y") is None


# ── SkillRegistryWriterPort contract — validation parity ───────────────
# These are the Liskov checks: prod and mock MUST reject the same bad inputs
# with the same shape. R10 mitigation.
def _seeded_mock_store():
    return InMemorySkillRegistryAdapter(skills=[
        {"name": "demo", "category": "test", "status": "canonical"},
    ])


def test_writer_rejects_non_editable_field_both_adapters():
    """field not in EDITABLE_FIELDS → {ok:False} on BOTH adapters."""
    # Mock
    mock = InMemorySkillRegistryWriterAdapter(_seeded_mock_store())
    r = mock.update_field("demo", "name", "hacker")  # 'name' is structural, not editable
    assert r["ok"] is False
    assert "allowlist" in r["error"]
    # Prod — use a clearly-structural field
    prod = AtomicSkillRegistryWriterAdapter()
    r2 = prod.update_field("a-think", "name", "whatever")
    assert r2["ok"] is False
    assert "allowlist" in r2["error"]


def test_writer_rejects_oversize_value_mock():
    """value > _EDIT_MAX_LEN → {ok:False}."""
    mock = InMemorySkillRegistryWriterAdapter(_seeded_mock_store())
    # th_description is editable; feed a giant string
    huge = "x" * (mock._EDIT_MAX_LEN + 1)
    r = mock.update_field("demo", "th_description", huge)
    assert r["ok"] is False
    assert "too long" in r["error"]


def test_writer_rejects_invalid_bool_mock():
    """bool field with non-bool value → {ok:False}."""
    mock = InMemorySkillRegistryWriterAdapter(_seeded_mock_store())
    # Find a bool field to test (status: canonical is a string; use a known
    # bool field from the registry schema if present, else skip gracefully)
    bool_fields = list(mock._BOOL_FIELDS)
    if not bool_fields:
        pytest.skip("no _BOOL_FIELDS defined")
    field = bool_fields[0]
    r = mock.update_field("demo", field, "not-a-bool")
    assert r["ok"] is False
    assert "bool" in r["error"].lower()


def test_writer_rejects_missing_skill_mock():
    """skill not found → {ok:False}."""
    mock = InMemorySkillRegistryWriterAdapter(_seeded_mock_store())
    r = mock.update_field("ghost", "th_description", "x")
    assert r["ok"] is False
    assert "not found" in r["error"]


def test_writer_success_returns_ok_dict_mock():
    """Happy path returns {ok:True, field, name, length} — the frozen shape."""
    mock = InMemorySkillRegistryWriterAdapter(_seeded_mock_store())
    r = mock.update_field("demo", "th_description", "hello")
    assert r["ok"] is True
    assert r["field"] == "th_description"
    assert r["name"] == "demo"
    assert r["length"] == 5
    # And the store must reflect the change
    assert mock._store.get("demo").get("th_description") == "hello"


def test_writer_returns_canonical_name_not_alias_input_mock():
    """Council 2026-08-03 BLOCK-fix (R10): writing via an ALIAS must return
    the canonical name, not the raw input. Prod does this at
    skills_service.py:894; the mock must mirror it exactly. Before the fix
    the mock returned the raw alias — a Liskov divergence the contract
    suite was supposed to catch."""
    store = InMemorySkillRegistryAdapter(skills=[
        {"name": "demo", "aliases": ["old-name"], "th_description": ""},
    ])
    mock = InMemorySkillRegistryWriterAdapter(store)
    r = mock.update_field("old-name", "th_description", "via-alias")
    assert r["ok"] is True, f"expected ok, got: {r}"
    # The returned name must be CANONICAL, not the alias we passed in.
    assert r["name"] == "demo", \
        f"mock returned raw alias {r['name']!r}, expected canonical 'demo'"
    # And the mutation must have landed on the canonical skill
    assert store.get("demo").get("th_description") == "via-alias"


def test_writer_alias_through_write_parity_prod_and_mock():
    """The R10 cross-check: prod and mock must agree on the returned name
    when writing via an alias. This is the test that would have caught the
    BLOCK finding on its own."""
    # Pick a real skill with a known alias from the live registry.
    prod_read = FileSkillRegistryAdapter()
    prod_skill = prod_read.get("a-think")
    aliases = prod_skill.get("aliases") or [] if prod_skill else []
    if not aliases:
        pytest.skip("a-think has no aliases in the live registry; cannot test alias-through-write parity")
    alias = aliases[0]
    # Mock path: seed with the same skill, write via alias
    mock_store = InMemorySkillRegistryAdapter(skills=[prod_skill])
    mock = InMemorySkillRegistryWriterAdapter(mock_store)
    mock_r = mock.update_field(alias, "th_description", "parity-check-discard")
    # We do NOT call prod.update_field here (it would mutate the real registry).
    # Instead we assert the mock's contract matches prod's DOCUMENTED behaviour
    # (skills_service.py:894 returns canonical_name). This keeps the test
    # non-destructive while still pinning the shape.
    assert mock_r["ok"] is True
    assert mock_r["name"] == "a-think", \
        f"mock diverged from prod canonical-name contract: {mock_r['name']!r}"
