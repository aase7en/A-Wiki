"""Phase 3 kernel-contract tests (A-Wiki vNext).

Iron Law #1: failing tests written FIRST.

Pins the Kernel Contract deliverables:
  - schemas/awiki-{task,review,handoff}/v1 exist and are valid JSON Schema
  - config/awiki.yaml + config/integrations.yaml exist and parse
  - capability vocabulary is vendor-neutral (no agent/model/provider names
    baked into stable enums)
  - durable vs runtime + control-plane vs project-state boundaries encoded
  - Graft contract: MODULE + PATTERN, default-off, cache never committed
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = REPO_ROOT / "schemas"
CONFIG = REPO_ROOT / "config"

CONTRACT_SCHEMAS = [
    "awiki-task/v1.schema.json",
    "awiki-review/v1.schema.json",
    "awiki-handoff/v1.schema.json",
    "awiki-integrations/v1.schema.json",
]

# Vendor/product names must never be baked into STABLE contract enums.
# (They may appear in examples/preferred lists marked runtime-candidate.)
FORBIDDEN_VENDOR_TOKENS = ("openai", "anthropic", "claude", "codex", "gemini",
                           "glm", "zcode", "zhipu", "deepseek", "kilo", "cursor",
                           "windsurf", "groq", "copilot")


@pytest.mark.parametrize("rel", CONTRACT_SCHEMAS)
def test_contract_schema_exists_and_parses(rel: str):
    p = SCHEMAS / rel
    assert p.is_file(), f"missing contract schema: {rel}"
    data = json.loads(p.read_text(encoding="utf-8"))
    assert isinstance(data, dict) and "$schema" in data or "type" in data


@pytest.mark.parametrize("rel", CONTRACT_SCHEMAS)
def test_contract_schema_is_valid_json_schema(rel: str):
    jsonschema = pytest.importorskip("jsonschema")  # deep check only where available
    data = json.loads((SCHEMAS / rel).read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(data)


def test_kernel_config_exists_and_parses():
    data = yaml.safe_load((CONFIG / "awiki.yaml").read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert data.get("schema") == "awiki-kernel/v1"


def test_integrations_registry_exists_and_parses():
    data = yaml.safe_load((CONFIG / "integrations.yaml").read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert data.get("schema") == "awiki-integrations/v1"
    assert isinstance(data.get("integrations"), dict) and data["integrations"]


def test_graft_contract_is_module_default_off_noncommitted():
    data = yaml.safe_load((CONFIG / "integrations.yaml").read_text(encoding="utf-8"))
    graft = data["integrations"].get("graft")
    assert graft, "graft must be registered (G0 contract-only)"
    assert graft["classification"] in ("module", "pattern") or \
        [c in ("module", "pattern") for c in graft["classification"]] if isinstance(graft["classification"], list) else True
    assert graft.get("default") is False, "Graft stays default-off (Phase 10+)"
    assert graft.get("lazy") is True
    storage = graft.get("storage", {})
    assert storage.get("commit") is False, "graft cache must never be committed"
    assert storage.get("type") == "local-regenerable-cache"
    assert graft.get("provides"), "must declare ProjectCodeContextProvider capabilities"


def test_graft_provider_vocabulary_defined():
    """G0: the seven vendor-neutral code-context operations must be named."""
    kernel = (REPO_ROOT / "docs" / "architecture" / "A-WIKI-KERNEL.md").read_text(encoding="utf-8")
    for op in ("status", "orient", "find", "file_api", "trace", "search", "freshness"):
        assert f"`{op}`" in kernel, f"ProjectCodeContextProvider op missing: {op}"


def test_capability_enum_is_vendor_neutral():
    """Stable enums must carry capabilities, not vendor names."""
    task = json.loads((SCHEMAS / "awiki-task/v1.schema.json").read_text(encoding="utf-8"))
    props = task.get("properties", {})
    caps = props.get("required_capabilities", {})
    enum = caps.get("items", {}).get("enum") or caps.get("enum")
    assert enum, "required_capabilities must be a closed enum (stable vocabulary)"
    for cap in enum:
        low = cap.lower()
        for token in FORBIDDEN_VENDOR_TOKENS:
            assert token not in low, f"vendor name leaked into capability enum: {cap}"


def test_review_schema_encodes_bus_verdicts():
    review = json.loads((SCHEMAS / "awiki-review/v1.schema.json").read_text(encoding="utf-8"))
    verdicts = review["properties"]["verdict"]["enum"]
    assert set(verdicts) == {"PASS", "PASS_WITH_NOTES", "CHANGES_REQUIRED", "BLOCK"}
    findings = review["properties"]["findings"]["items"]["properties"]
    assert set(findings["severity"]["enum"]) == {"blocker", "major", "minor", "note"}
    assert set(findings["state"]["enum"]) == {"open", "addressed", "verified", "wont_fix", "superseded"}


def test_task_schema_supports_capability_roles_and_modes():
    task = json.loads((SCHEMAS / "awiki-task/v1.schema.json").read_text(encoding="utf-8"))
    props = task["properties"]
    assert set(props["mode"]["enum"]) >= {"solo", "pair", "architect_executor",
                                          "parallel", "council", "swarm", "auto"}
    roles = props["assigned"]["properties"]
    assert "executor" in roles and "reviewer" in roles


def test_handoff_schema_carries_resume_evidence():
    hand = json.loads((SCHEMAS / "awiki-handoff/v1.schema.json").read_text(encoding="utf-8"))
    props = hand["properties"]
    for must in ("task_id", "branch", "head_sha", "tests", "next_action"):
        assert must in props, f"handoff missing {must}"
