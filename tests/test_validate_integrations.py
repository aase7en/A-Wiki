"""Phase 3 — deterministic integration-registry validation tests.

Iron Law #1: failing tests written FIRST.

`scripts/health/validate_integrations.py` must be fully deterministic
(no network, no side effects) so wiki_health + CI can enforce registry
invariants on every platform. Invariants from D-CTX-005 + graft plan:
  - schema key present and exact
  - classification in CORE|MODULE|PATTERN|REFERENCE|REJECT
  - external modules: default off + lazy
  - cache storage: commit=false
  - provides/requires declared as lists
  - references must not point at nonexistent files (when file refs given)
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "health"))

import validate_integrations as vi  # noqa: E402 -- module under test


GOOD = """\
schema: awiki-integrations/v1
integrations:
  graft:
    classification: module
    domain: project-code-context
    default: false
    lazy: true
    runtime: local
    provides: [symbol-search]
    requires: [node>=20]
    storage: {type: local-regenerable-cache, commit: false}
"""


def _write(tmp_path, text):
    p = tmp_path / "integrations.yaml"
    p.write_text(text, encoding="utf-8")
    return p


def test_valid_registry_passes(tmp_path):
    result = vi.validate(_write(tmp_path, GOOD))
    assert result.errors == [], result.errors
    assert result.exit_code() == 0


def test_missing_schema_key_fails(tmp_path):
    text = GOOD.replace("schema: awiki-integrations/v1", "schema: something-else/v9")
    result = vi.validate(_write(tmp_path, text))
    assert result.exit_code() == 1
    assert any("schema" in e.lower() for e in result.errors)


def test_unknown_classification_fails(tmp_path):
    text = GOOD.replace("classification: module", "classification: mega")
    result = vi.validate(_write(tmp_path, text))
    assert any("classification" in e.lower() for e in result.errors)


def test_external_module_default_on_fails(tmp_path):
    text = GOOD.replace("default: false", "default: true")
    result = vi.validate(_write(tmp_path, text))
    assert any("default" in e.lower() for e in result.errors)


def test_cache_storage_committed_fails(tmp_path):
    text = GOOD.replace("commit: false", "commit: true")
    result = vi.validate(_write(tmp_path, text))
    assert any("commit" in e.lower() for e in result.errors)


def test_broken_yaml_fails_cleanly(tmp_path):
    p = tmp_path / "integrations.yaml"
    p.write_text("integrations: [unclosed", encoding="utf-8")
    result = vi.validate(p)
    assert result.exit_code() == 1
    assert any("parse" in e.lower() or "yaml" in e.lower() for e in result.errors)


def test_real_repo_registry_validates():
    result = vi.validate(REPO_ROOT / "config" / "integrations.yaml")
    assert result.errors == [], result.errors
    assert result.exit_code() == 0


def test_dangling_file_reference_fails(tmp_path):
    text = GOOD + "\n  ref-doc: docs/does-not-exist.md\n"
    text = text.replace("integrations:\n  graft:", "integrations:\n  graft:")
    # attach ref to graft by inserting under it
    text = text.replace("    storage: {type: local-regenerable-cache, commit: false}\n",
                        "    storage: {type: local-regenerable-cache, commit: false}\n    reference: docs/does-not-exist.md\n")
    result = vi.validate(_write(tmp_path, text))
    assert any("reference" in e.lower() for e in result.errors)


# ---------------------------------------------------------------------------
# R-P3-002 — one authoritative path: JSON Schema + duplicate keys + semantics
# ---------------------------------------------------------------------------
def test_unknown_field_rejected_by_schema(tmp_path):
    text = GOOD.replace("    lazy: true\n", "    lazy: true\n    last_seen: 2026-08-18T00:00:00Z\n")
    result = vi.validate(_write(tmp_path, text))
    assert result.exit_code() == 1
    assert any("last_seen" in e or "additional" in e.lower() for e in result.errors)


def test_duplicate_yaml_key_rejected(tmp_path):
    dup = GOOD + "    lazy: false\n"  # second 'lazy' under graft
    result = vi.validate(_write(tmp_path, dup))
    assert result.exit_code() == 1
    assert any("duplicate" in e.lower() for e in result.errors)


def test_module_without_storage_rejected(tmp_path):
    text = GOOD.replace("    storage: {type: local-regenerable-cache, commit: false}\n", "")
    result = vi.validate(_write(tmp_path, text))
    assert any("storage" in e.lower() for e in result.errors)


def test_module_without_capabilities_rejected(tmp_path):
    text = GOOD.replace("    provides: [symbol-search]\n", "")
    result = vi.validate(_write(tmp_path, text))
    assert any("provides" in e.lower() for e in result.errors)


def test_contradictory_classification_rejected(tmp_path):
    text = GOOD.replace("classification: module", "classification: [module, reject]")
    result = vi.validate(_write(tmp_path, text))
    assert any("reject" in e.lower() and "combine" in e.lower() for e in result.errors)


def test_runtime_telemetry_field_rejected(tmp_path):
    text = GOOD.replace("    lazy: true\n", "    lazy: true\n    quota_state: exhausted\n")
    result = vi.validate(_write(tmp_path, text))
    assert result.exit_code() == 1
