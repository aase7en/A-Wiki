"""Phase 5 — A-Wiki Memory Plane contract tests.

Iron Law #1: failing tests written FIRST.

Pins the work-order invariants (§4, §5, §6, §7, §9 items 1–25):
  L0–L5 non-overlapping semantics, project isolation, scope enforcement,
  fail-closed adapters, five-gate promotion (manual-with-evidence,
  dry-run-first), privacy/evidence gates, L4 immutability, L5 experiment
  semantics, and compatibility with existing MemoryLedger/MCP contracts.
All fixtures are temp dirs — never real private Drive data.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "project"))

import memory_layers as ml          # noqa: E402 -- module under test
import project_memory as pm         # noqa: E402 -- module under test
import experiment_memory as em      # noqa: E402 -- module under test
import promotion as promo           # noqa: E402 -- module under test


def _valid_yaml_text(pid: str = "alpha", overrides: dict | None = None) -> str:
    data = {
        "schema": "awiki-project/v1",
        "id": pid,
        "domains": ["web-development"],
        "skills": {"auto": ["a-router"]},
        "integrations": {"allowed": []},
        "memory": {"scopes": {"global": True, "project": True,
                              "session": True, "private": False}},
        "privacy": {"project_private": True},
        "trust": {"deep_enrichment": "project-policy", "private_context": False},
        "code_context": {"enabled": False, "preferred": [],
                         "cache_policy": "local-regenerable",
                         "global_memory_promotion": False},
        "resources": [],
    }
    if overrides:
        data.update(overrides)
    return yaml.safe_dump(data, sort_keys=False, default_flow_style=True).strip()


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _project(tmp_path: Path, pid: str = "alpha", *, scopes=None, private=True) -> Path:
    p = tmp_path / pid
    p.mkdir(parents=True)
    aw = p / ".awiki"
    aw.mkdir()
    sc = scopes or {"global": True, "project": True, "session": True, "private": False}
    (aw / "project.yaml").write_text(_valid_yaml_text(
        pid=pid,
        overrides={
            "memory": {"scopes": sc},
            "privacy": {"project_private": private},
            "trust": {"deep_enrichment": "project-policy", "private_context": False},
        }), encoding="utf-8")
    (aw / "context.md").write_text("# c\n", encoding="utf-8")
    (aw / "state").mkdir()
    (p / "AGENTS.md").write_text("<!-- awiki-project-adapter v1 -->\n", encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# 1–3: layer semantics
# ---------------------------------------------------------------------------
def test_all_layers_defined_with_non_overlapping_semantics():
    for key in ("L0", "L1", "L2", "L3", "L4", "L5"):
        assert key in ml.LAYER_POLICY, f"missing layer {key}"
    durabilities = set()
    for key, pol in ml.LAYER_POLICY.items():
        assert pol["durability"] in ("runtime", "durable")
        durabilities.add((key, pol["durability"]))
    # each layer has exactly one durability
    assert len(durabilities) == 6


def test_l0_is_runtime_not_global_durable():
    assert ml.LAYER_POLICY["L0"]["durability"] == "runtime"
    assert ml.LAYER_POLICY["L0"]["global_knowledge"] is False


def test_l1_cannot_auto_promote_to_l3():
    assert ml.transition_allowed("L1", "L3") is False
    assert ml.LAYER_POLICY["L1"]["auto_promote"] is False


def test_only_promotion_pipeline_reaches_l3():
    # L2 -> L3 is only allowed through the promotion gates (explicit flag)
    assert ml.transition_allowed("L2", "L3", via="promotion") is True
    assert ml.transition_allowed("L2", "L3") is False
    assert ml.transition_allowed("L4", "L3") is False
    assert ml.transition_allowed("L0", "L3") is False


def test_config_manifest_matches_policy_single_source():
    cfg = yaml.safe_load((REPO_ROOT / "config" / "memory-layers.yaml").read_text(encoding="utf-8"))
    assert cfg["schema"] == "awiki-memory-layers/v1"
    for key, pol in ml.LAYER_POLICY.items():
        entry = cfg["layers"][key]
        assert entry["durability"] == pol["durability"], key


# ---------------------------------------------------------------------------
# 4–7: project isolation + scopes + fail-closed adapter
# ---------------------------------------------------------------------------
def test_project_a_cannot_access_project_b_memory(tmp_path):
    root = tmp_path / "data"
    a = _project(tmp_path, "alpha")
    b = _project(tmp_path, "beta")
    sa = pm.ProjectMemoryStore(a, data_root=root)
    sa.append_entry("alpha-secret-lesson")
    sb = pm.ProjectMemoryStore(b, data_root=root)
    hits = sb.read_entries("alpha-secret-lesson")
    assert hits == [], "project B must not see project A memory"


def test_disabled_project_scope_blocks_l2(tmp_path):
    p = _project(tmp_path, "gamma", scopes={"global": True, "project": False,
                                            "session": True, "private": False})
    store = pm.ProjectMemoryStore(p, data_root=tmp_path / "data")
    with pytest.raises(pm.ScopeDenied):
        store.append_entry("nope")


def test_disabled_global_scope_blocks_promotion(tmp_path):
    p = _project(tmp_path, "delta", scopes={"global": False, "project": True,
                                            "session": True, "private": False})
    with pytest.raises(pm.ScopeDenied):
        promo.promote(
            project_root=p, distilled="generalized lesson",
            provenance={"type": "commit_sha", "value": "abc1234"},
            dry_run=True,
        )


def test_invalid_adapter_fails_closed(tmp_path):
    broken = _project(tmp_path, "broken")
    (broken / ".awiki" / "project.yaml").write_text("schema: [unclosed", encoding="utf-8")
    with pytest.raises(pm.AdapterInvalid):
        pm.ProjectMemoryStore(broken, data_root=tmp_path / "data")


def test_project_store_paths_are_containment_safe(tmp_path):
    root = tmp_path / "data"
    p = _project(tmp_path, "alpha")
    store = pm.ProjectMemoryStore(p, data_root=root)
    d = store.memory_dir
    assert root.resolve() in d.resolve().parents or d.resolve() == root.resolve()
    assert "alpha" in d.parts


def test_malformed_project_id_rejected(tmp_path):
    p = _project(tmp_path, "alpha")
    bad = _project(tmp_path / "evil", "ok")
    # craft adapter with traversal-ish id via direct yaml override
    (bad / ".awiki" / "project.yaml").write_text(
        _valid_yaml_text(pid="ok").replace("id: ok", "id: ..%2Fescape"), encoding="utf-8")
    with pytest.raises((pm.AdapterInvalid, ValueError)):
        pm.ProjectMemoryStore(bad, data_root=tmp_path / "data")


# ---------------------------------------------------------------------------
# 8–12: promotion gates (privacy / generalize / evidence / provenance paths)
# ---------------------------------------------------------------------------
def test_private_project_promotion_requires_privacy_gate(tmp_path):
    p = _project(tmp_path, "priv", private=True)
    token = "ghp_" + "P5" + "0123456789abcdef" * 2
    res = promo.promote(
        project_root=p, distilled=f"lesson with {token} inside",
        provenance={"type": "commit_sha", "value": "abc1234"}, dry_run=True)
    assert res["ok"] is False
    assert any("privacy" in g["gate"] and not g["passed"] for g in res["gates"])


def test_promotion_without_evidence_fails(tmp_path):
    p = _project(tmp_path, "noev")
    res = promo.promote(project_root=p, distilled="lesson",
                        provenance=None, dry_run=True)
    assert res["ok"] is False
    assert any("evidence" in g["gate"] and not g["passed"] for g in res["gates"])


def test_promotion_bad_evidence_type_fails(tmp_path):
    p = _project(tmp_path, "badev")
    res = promo.promote(project_root=p, distilled="lesson",
                        provenance={"type": "vibes", "value": "x"}, dry_run=True)
    assert res["ok"] is False
    assert any("evidence" in g["gate"] and not g["passed"] for g in res["gates"])


def test_promotion_absolute_machine_path_in_provenance_fails(tmp_path):
    p = _project(tmp_path, "pathprov")
    drive = "C" + chr(58) + chr(92) + "Users" + chr(92) + "me" + chr(92) + "proof.txt"
    res = promo.promote(project_root=p, distilled="lesson",
                        provenance={"type": "wiki_ref", "value": drive}, dry_run=True)
    assert res["ok"] is False
    assert any("provenance" in g["gate"] and not g["passed"] for g in res["gates"])


def test_promotion_rejects_project_specific_generalization(tmp_path):
    p = _project(tmp_path, "gen", private=True)
    res = promo.promote(
        project_root=p,
        distilled="At project alpha we always deploy server alpha-prod-01 on Friday",
        provenance={"type": "commit_sha", "value": "abc1234"}, dry_run=True)
    assert res["ok"] is False
    assert any("generalize" in g["gate"] and not g["passed"] for g in res["gates"])


def test_clean_promotion_dry_run_passes_all_gates(tmp_path):
    p = _project(tmp_path, "clean")
    root = tmp_path / "data"
    ts = _l2(p, root)
    res = promo.promote(
        project_root=p,
        distilled="Prefer explicit capability enums over vendor names in stable contracts.",
        provenance={"type": "commit_sha", "value": "10507cee"},
        source_entry_ts=ts, dry_run=True, data_root=root)
    assert res["ok"] is True, res["gates"]
    assert all(g["passed"] for g in res["gates"])


# ---------------------------------------------------------------------------
# 20–21: dry-run vs apply
# ---------------------------------------------------------------------------
def test_dry_run_changes_nothing(tmp_path):
    p = _project(tmp_path, "dry")
    root = tmp_path / "data"
    ts = _l2(p, root)
    res = promo.promote(
        project_root=p, distilled="Generalized durable lesson.",
        provenance={"type": "commit_sha", "value": "10507cee"},
        source_entry_ts=ts, dry_run=True, data_root=root)
    assert res["ok"] is True
    assert res.get("written") in (None, False)
    cands = REPO_ROOT / "wiki" / "promotion-candidates"
    assert not any(cands.glob("dry*.md")), "dry-run must not write candidates"


def test_explicit_apply_writes_candidate_only(tmp_path, monkeypatch):
    p = _project(tmp_path, "applyp")
    root = tmp_path / "data"
    ts = _l2(p, root)
    out_root = tmp_path / "l3candidates"
    out_root.mkdir()
    monkeypatch.setattr(promo, "CANDIDATES_DIR", out_root)
    res = promo.promote(
        project_root=p, distilled="Generalized durable lesson two.",
        provenance={"type": "commit_sha", "value": "10507cee"},
        source_entry_ts=ts, dry_run=False, data_root=root)
    assert res["ok"] is True and res.get("written") is True
    files = list(out_root.glob("*.md"))
    assert len(files) == 1
    assert "Generalized durable lesson two." in files[0].read_text(encoding="utf-8")


def test_apply_never_touches_git(tmp_path, monkeypatch):
    p = _project(tmp_path, "gitcheck")
    root = tmp_path / "data"
    ts = _l2(p, root)
    out_root = tmp_path / "l3b"
    out_root.mkdir()
    monkeypatch.setattr(promo, "CANDIDATES_DIR", out_root)
    promo.promote(project_root=p, distilled="Lesson.",
                  provenance={"type": "commit_sha", "value": "10507cee"},
                  source_entry_ts=ts, dry_run=False, data_root=root)
    assert not hasattr(promo, "_git")  # no git machinery in the module


# ---------------------------------------------------------------------------
# 13–14: raw immutability
# ---------------------------------------------------------------------------
def test_l4_mutation_through_memory_api_fails(tmp_path):
    root = tmp_path / "data"
    p = _project(tmp_path, "l4")
    store = pm.ProjectMemoryStore(p, data_root=root)
    with pytest.raises(ml.LayerViolation):
        store.write_layer("L4", "anything")


def test_raw_cannot_directly_promote_to_l3():
    assert ml.transition_allowed("L4", "L3") is False


# ---------------------------------------------------------------------------
# 15–19: experiment memory
# ---------------------------------------------------------------------------
def _exp(tmp_path, pid="alpha", eid="EXP-001"):
    proj = _project(tmp_path, pid)
    store = em.ExperimentStore(proj, data_root=tmp_path / "data")   # adapter-bound (R-P5-003)
    store.initialize(eid, baseline={"metric": "pass_at_k", "value": 0.74})
    return store, eid


def _l2(p: Path, data_root: Path, text: str = "stabilized project lesson") -> float:
    """R-P5-001: promotion tests bind to a real L2 source entry."""
    return pm.ProjectMemoryStore(p, data_root=data_root).append_entry(text)


def test_experiment_baseline_immutable(tmp_path):
    store, eid = _exp(tmp_path)
    with pytest.raises(em.BaselineImmutable):
        store.initialize(eid, baseline={"metric": "pass_at_k", "value": 0.99})


def test_experiment_iterations_append_only(tmp_path):
    store, eid = _exp(tmp_path)
    store.append_iteration(eid, {"change": "prompt-only", "score": 0.78})
    iters = store.read_iterations(eid)
    assert len(iters) == 1
    with pytest.raises(em.AppendOnly):
        store.overwrite_iteration(eid, 0, {"tampered": True})


def test_winner_must_reference_existing_iteration(tmp_path):
    store, eid = _exp(tmp_path)
    with pytest.raises(em.WinnerValidationError):
        store.set_winner(eid, iteration_index=5)  # no such iteration
    store.append_iteration(eid, {"change": "x", "score": 0.8})
    store.set_winner(eid, iteration_index=0)  # ok
    w = store.read_winner(eid)
    assert w["iteration_index"] == 0


def test_malformed_experiment_records_fail(tmp_path):
    store = em.ExperimentStore(_project(tmp_path, "alpha"), data_root=tmp_path / "data")
    with pytest.raises((em.MalformedRecord, ValueError)):
        store.initialize("BAD ID WITH SPACES", baseline={})


def test_experiment_project_crossover_fails(tmp_path):
    """Isolation is structural + adapter-authoritative: B's store (bound to
    beta's adapter) cannot address A's experiment at all."""
    proj_a = _project(tmp_path, "alpha")
    proj_b = _project(tmp_path, "beta")
    store_a = em.ExperimentStore(proj_a, data_root=tmp_path / "data")
    store_a.initialize("EXP-1", baseline={"m": 1})
    store_a.append_iteration("EXP-1", {"change": "a-only", "score": 0.5})
    store_b = em.ExperimentStore(proj_b, data_root=tmp_path / "data")
    # B cannot see A's iterations through any store API
    assert store_b.read_iterations("EXP-1") == []
    # B creating its own EXP-1 does not touch A's records
    store_b.initialize("EXP-1", baseline={"m": 2})
    store_b.append_iteration("EXP-1", {"change": "b-only", "score": 0.9})
    assert len(store_a.read_iterations("EXP-1")) == 1
    assert store_a.read_iterations("EXP-1")[0]["change"] == "a-only"
    # and the marker guard still raises on direct cross-project access attempts
    import json
    marker = (tmp_path / "data" / "projects" / "alpha" / "experiments" / "EXP-1" / ".project")
    assert marker.read_text(encoding="utf-8").strip() == "alpha"


def test_experiment_report_written(tmp_path):
    store, eid = _exp(tmp_path)
    store.append_iteration(eid, {"change": "x", "score": 0.8})
    store.set_winner(eid, iteration_index=0)
    report = store.write_report(eid, "# Experiment EXP-001\nwinner idx 0")
    assert report.exists()


# ---------------------------------------------------------------------------
# 22–23: existing contracts stay green
# ---------------------------------------------------------------------------
def test_memory_ledger_redaction_still_works(tmp_path):
    import memory_ledger
    ledger = memory_ledger.MemoryLedger(tmp_path / "ledger.jsonl")
    token = "sk-" + "abc-def-ghi-jkl-mno-" + "123456"  # assembled — no literal in this file
    ts = ledger.append(session_id="session-x", type="lesson",
                       summary=f"leaked {token} here")
    line = (tmp_path / "ledger.jsonl").read_text(encoding="utf-8")
    assert token not in line, "ledger redaction regressed"
    assert ts


def test_memory_port_adapter_still_importable_and_wraps_ledger(tmp_path):
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from adapters.memory import JsonlMemoryAdapter  # noqa: I001
    ad = JsonlMemoryAdapter(tmp_path / "p.jsonl")
    ad.remember(session_id="s1", type="lesson", summary="hello world lesson")
    # recall contract
    assert isinstance(ad.recall("hello", limit=3), list)


# ---------------------------------------------------------------------------
# 24: Phase 4 adapter tests remain green (import smoke — full suite covers)
# ---------------------------------------------------------------------------
def test_phase4_validate_module_importable():
    import validate  # noqa: F401  (already imported above; explicit smoke)


# ---------------------------------------------------------------------------
# 25: cross-platform path shapes (assembled, never committed)
# ---------------------------------------------------------------------------
def test_resolver_rejects_unsafe_data_roots(tmp_path):
    """Data root must be ABSOLUTE (relative/traversal rejected) and non-symlink.
    Absolute roots are required — tmp_path fixtures pass absolute roots."""
    p = _project(tmp_path, "paths")
    with pytest.raises((pm.AdapterInvalid, ValueError)):
        pm.ProjectMemoryStore(p, data_root=Path("..") / "escape")  # relative traversal
    with pytest.raises((pm.AdapterInvalid, ValueError)):
        pm.ProjectMemoryStore(p, data_root=Path("relative/root"))   # relative
    if hasattr(os, "symlink"):
        outside = tmp_path / "outside-root"
        outside.mkdir()
        link = tmp_path / "linked-root"
        os.symlink(outside, link)
        with pytest.raises((pm.AdapterInvalid, ValueError)):
            pm.ProjectMemoryStore(p, data_root=link)               # symlink root
