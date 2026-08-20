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
    classes = {graft["classification"]} if isinstance(graft["classification"], str) \
        else set(graft["classification"] or [])
    assert classes and classes <= {"module", "pattern"}, \
        f"graft classification must be module/pattern only: {classes}"
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
    enum = task["$defs"]["capability"]["enum"]  # canonical def (R-P3-004)
    assert enum, "capability vocabulary must be a closed enum"
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


# ---------------------------------------------------------------------------
# R-P3-001 — awiki-review/v1 must enforce its safety state machine
# ---------------------------------------------------------------------------
def _review_instance(**overrides):
    base = {
        "schema": "awiki-review/v1", "phase": "3", "cycle": 1,
        "executor": "agent-a", "reviewer": "agent-b",
        "status": "REVIEW_REQUESTED", "head_sha": "abc1234",
    }
    base.update(overrides)
    return base


def _validate_review(instance):
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((SCHEMAS / "awiki-review/v1.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(instance)  # raises on invalid


def test_review_ready_requires_reviewer_verdict_and_evidence():
    with pytest.raises(Exception):
        _validate_review(_review_instance(status="READY"))


def test_review_approved_rejects_changes_required_verdict():
    with pytest.raises(Exception):
        _validate_review(_review_instance(status="APPROVED", verdict="CHANGES_REQUIRED"))


def test_review_ready_rejects_open_blocker_finding():
    with pytest.raises(Exception):
        _validate_review(_review_instance(
            status="READY", verdict="PASS",
            findings=[{"id": "R-X-001", "severity": "blocker", "area": "x",
                       "summary": "s", "state": "open"}],
        ))


def test_review_ready_accepts_verified_blocker_and_pass():
    _validate_review(_review_instance(
        status="READY", verdict="PASS_WITH_NOTES",
        findings=[{"id": "R-X-001", "severity": "blocker", "area": "x",
                   "summary": "s", "state": "verified"}],
        required_tests=["python -m pytest tests/ -q"],
        next_action="MARK_READY",
    ))


def test_review_reviewing_requires_reviewer():
    with pytest.raises(Exception):
        _validate_review(_review_instance(status="REVIEWING", reviewer=None))


# ---------------------------------------------------------------------------
# R-P3-003 — task state must stay in the durable + control-plane boundaries
# ---------------------------------------------------------------------------
def test_task_state_is_durable_and_control_plane():
    data = yaml.safe_load((CONFIG / "awiki.yaml").read_text(encoding="utf-8"))
    durable = " ".join(data["state_boundaries"]["durable"]).lower()
    control = " ".join(data["control_plane_vs_project"]["control_plane_holds"]).lower()
    assert "task" in durable, "task state must be listed as durable"
    assert "task" in control, "task state must be listed as control-plane held"
    # and the wording must never re-trigger the sk- secret scanner
    import re
    for bucket in (durable, control):
        assert not re.search(r"sk-[A-Za-z0-9_-]{24,}", bucket)


# ---------------------------------------------------------------------------
# R-P3-004 — one canonical role/capability vocabulary across contracts
# ---------------------------------------------------------------------------
def _task_instance(**overrides):
    base = {
        "schema": "awiki-task/v1", "id": "AW-001", "goal": "g",
        "status": "planned", "mode": "pair",
    }
    base.update(overrides)
    return base


def _validate_task(instance):
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((SCHEMAS / "awiki-task/v1.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(instance)


def test_task_assigned_supports_tester_role():
    task = json.loads((SCHEMAS / "awiki-task/v1.schema.json").read_text(encoding="utf-8"))
    roles = set(task["properties"]["assigned"]["properties"])
    assert {"executor", "reviewer", "architect", "tester"} <= roles, \
        "KERNEL.md lists tester as assignable; schema must match"


def test_task_capability_enum_covers_context_and_memory_capabilities():
    task = json.loads((SCHEMAS / "awiki-task/v1.schema.json").read_text(encoding="utf-8"))
    enum = set(task["$defs"]["capability"]["enum"])
    for cap in ("project-code-context", "symbol-search", "call-graph",
                "blast-radius", "memory-read", "memory-write"):
        assert cap in enum, f"advertised capability not requestable by tasks: {cap}"


def test_task_worktree_rejects_absolute_and_private_paths():
    _validate_task(_task_instance(worktree=".worktrees/AW-001"))  # repo-relative ok
    drive = "C" + chr(58) + chr(92)  # "C:" + backslash, assembled — no literal machine path here
    for bad in (drive + "private" + chr(92) + "wt",
                chr(47) + "home/user/wt", "~" + chr(47) + "wt"):
        with pytest.raises(Exception):
            _validate_task(_task_instance(worktree=bad))


def test_task_has_evidence_field():
    _validate_task(_task_instance(evidence=["python -m pytest tests/ -q", "run/abc.md"]))


def test_handoff_roles_are_subset_of_kernel_roles():
    hand = json.loads((SCHEMAS / "awiki-handoff/v1.schema.json").read_text(encoding="utf-8"))
    task = json.loads((SCHEMAS / "awiki-task/v1.schema.json").read_text(encoding="utf-8"))
    kernel_roles = set(task["properties"]["assigned"]["properties"])
    handoff_roles = set(hand["properties"]["to_role"]["enum"])
    assert handoff_roles - {"any-capable-agent"} <= kernel_roles


def test_provider_capabilities_advertised_in_registry_are_requestable():
    reg = yaml.safe_load((CONFIG / "integrations.yaml").read_text(encoding="utf-8"))
    task = json.loads((SCHEMAS / "awiki-task/v1.schema.json").read_text(encoding="utf-8"))
    enum = set(task["$defs"]["capability"]["enum"])
    context_caps = {"symbol-search", "call-graph", "blast-radius"}
    graft = reg["integrations"]["graft"]["provides"]
    assert context_caps <= set(graft), "graft advertises the context capabilities"
    assert context_caps <= enum, "task enum must be able to request them"


def test_kernel_doc_lists_context_and_memory_capabilities():
    kernel = (REPO_ROOT / "docs" / "architecture" / "A-WIKI-KERNEL.md").read_text(encoding="utf-8")
    for cap in ("project-code-context", "symbol-search", "call-graph",
                "blast-radius", "memory-read", "memory-write"):
        assert cap in kernel, f"KERNEL.md capability list missing {cap}"


# ---------------------------------------------------------------------------
# R-P3-005 — handoff must carry complete resume evidence
# ---------------------------------------------------------------------------
def _handoff_instance(**overrides):
    base = {
        "schema": "awiki-handoff/v1", "task_id": "AW-001", "from": "agent-a",
        "to_role": "executor", "branch": "feature/x", "head_sha": "abc1234",
        "changed_files": ["src/a.py"], "tests": {"passed": ["t1"], "failed": []},
        "open_questions": [], "known_risks": [], "next_action": "test",
    }
    base.update(overrides)
    return base


def _validate_handoff(instance):
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((SCHEMAS / "awiki-handoff/v1.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(instance)


def test_complete_handoff_is_valid():
    _validate_handoff(_handoff_instance())


@pytest.mark.parametrize("missing", [
    "from", "to_role", "tests", "changed_files", "open_questions", "known_risks",
])
def test_incomplete_handoff_is_rejected(missing):
    inst = _handoff_instance()
    inst.pop(missing)
    with pytest.raises(Exception):
        _validate_handoff(inst)


# ---------------------------------------------------------------------------
# R-P3-007 — graft classification test must actually prove MODULE/PATTERN
# ---------------------------------------------------------------------------
def _graft_classification_ok(value):
    classes = {value} if isinstance(value, str) else set(value or [])
    return bool(classes) and classes <= {"module", "pattern"}


def test_graft_classification_check_normalizes_and_proves():
    reg = yaml.safe_load((CONFIG / "integrations.yaml").read_text(encoding="utf-8"))
    graft = reg["integrations"]["graft"]
    assert _graft_classification_ok(graft["classification"]), graft["classification"]
    # negative cases the old truthy-expression accepted by accident
    assert not _graft_classification_ok("reject")
    assert not _graft_classification_ok(["module", "reject"])
    assert not _graft_classification_ok([])
    assert not _graft_classification_ok(None)


# ---------------------------------------------------------------------------
# R-P3-006 — normative contract references must resolve
# ---------------------------------------------------------------------------
def test_normative_reference_paths_resolve():
    # awiki.yaml's classification-gate pointer must exist
    data = yaml.safe_load((CONFIG / "awiki.yaml").read_text(encoding="utf-8"))
    gate = data["integration_registry"]["classification_gate"]
    gate_path = REPO_ROOT / gate.split()[0].rstrip("/")
    assert gate_path.with_suffix(".md").is_file() or gate_path.is_file(), \
        f"normative reference missing: {gate}"
    # every registry reference must exist (validator also enforces; kernel test doubles it)
    reg = yaml.safe_load((CONFIG / "integrations.yaml").read_text(encoding="utf-8"))
    for name, entry in reg["integrations"].items():
        ref = entry.get("reference")
        if ref:
            assert (REPO_ROOT / ref).is_file(), f"{name}: reference missing: {ref}"


def test_graft_freshness_pattern_is_not_marked_merged():
    """R-P3-002 truthfulness: query-path freshness is planned, not implemented."""
    reg = yaml.safe_load((CONFIG / "integrations.yaml").read_text(encoding="utf-8"))
    fp = reg["integrations"]["graft-freshness-pattern"]
    assert fp["status"] != "merged", \
        "wiki-health/scan-repo do not implement Graft query-path freshness/refresh semantics"
    assert not fp.get("implemented_by"), "no implementors exist yet"


# ---------------------------------------------------------------------------
# R-P3-004 (re-review) — ONE canonical capability vocabulary, no bypass
# ---------------------------------------------------------------------------
def test_agentref_requires_uses_canonical_capability_enum():
    task = json.loads((SCHEMAS / "awiki-task/v1.schema.json").read_text(encoding="utf-8"))
    caps = task["$defs"]["capability"]["enum"]
    req_items = task["properties"]["required_capabilities"]["items"]
    assert req_items.get("$ref") == "#/$defs/capability", \
        "required_capabilities must $ref the canonical capability def"
    for role in ("executor", "reviewer", "architect", "tester"):
        role_schema = task["properties"]["assigned"]["properties"][role]
        assert role_schema.get("$ref") == "#/$defs/agentRef", \
            f"assigned.{role} must $ref agentRef (single assignment contract)"
    agent_ref = task["$defs"]["agentRef"]
    assert agent_ref["properties"]["requires"]["items"].get("$ref") == "#/$defs/capability", \
        "agentRef.requires must $ref the canonical capability def (R-P3-004)"


def test_vendor_token_in_assigned_requires_rejected():
    with pytest.raises(Exception):
        _validate_task(_task_instance(assigned={
            "executor": {"requires": ["codex-magic"], "preferred": ["x"]},
        }))


def test_nonexistent_capability_in_assigned_requires_rejected():
    with pytest.raises(Exception):
        _validate_task(_task_instance(assigned={
            "executor": {"requires": ["mind-reading"]},
        }))


def test_real_registry_module_entries_declare_trust():
    reg = yaml.safe_load((CONFIG / "integrations.yaml").read_text(encoding="utf-8"))
    for name, entry in reg["integrations"].items():
        classes = {entry["classification"]} if isinstance(entry["classification"], str) \
            else set(entry["classification"] or [])
        if "module" in classes:
            trust = entry.get("trust")
            assert isinstance(trust, dict), f"{name}: module must declare trust policy"
            assert "private_context" in trust, f"{name}: trust must decide private_context"
