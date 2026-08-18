"""Phase 5 remediation — R-P5-001..006 (PR #15 review).

Iron Law #1: failing tests written FIRST. Every test here pins a hard
Memory Plane invariant the first implementation missed:

  R-P5-001  promotion is mechanically bound to a verified L2 source entry
  R-P5-002  nested symlink/reparse escapes under the data root are rejected
  R-P5-003  L5 identity is adapter-authoritative, not caller-asserted
  R-P5-004  provenance passes the privacy gate; front matter is YAML-safe
  R-P5-005  memory status is strictly read-only + private-path-safe
  R-P5-006  L2 storage routes through the MemoryLedger seam
"""
from __future__ import annotations

import json
import os
import re
import sys
import threading
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "project"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import memory_layers as ml          # noqa: E402
import project_memory as pm         # noqa: E402
import experiment_memory as em      # noqa: E402
import promotion as promo           # noqa: E402
import memory_ledger                # noqa: E402

import importlib.util as _ilu      # noqa: E402 -- load the CLI script by path
_spec = _ilu.spec_from_file_location(
    "memory_status_cli", REPO_ROOT / "scripts" / "memory" / "status.py")
_mod = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
mem_status = _mod.status


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


def _project(tmp_path: Path, pid: str = "alpha", *, scopes=None) -> Path:
    p = tmp_path / pid
    p.mkdir(parents=True)
    aw = p / ".awiki"
    aw.mkdir()
    sc = scopes or {"global": True, "project": True, "session": True, "private": False}
    (aw / "project.yaml").write_text(_valid_yaml_text(
        pid=pid,
        overrides={
            "memory": {"scopes": sc},
            "privacy": {"project_private": True},
            "trust": {"deep_enrichment": "project-policy", "private_context": False},
        }), encoding="utf-8")
    (aw / "context.md").write_text("# c\n", encoding="utf-8")
    (aw / "state").mkdir()
    (p / "AGENTS.md").write_text("<!-- awiki-project-adapter v1 -->\n", encoding="utf-8")
    return p


def _l2_source(project_root: Path, data_root: Path, text: str = "stabilized project lesson") -> float:
    """Append a real L2 entry and return its identity (ts)."""
    store = pm.ProjectMemoryStore(project_root, data_root=data_root)
    return store.append_entry(text)


def _can_be_symlinked() -> bool:
    return hasattr(os, "symlink")


# ---------------------------------------------------------------------------
# R-P5-001 — promotion is bound to a verified L2 source
# ---------------------------------------------------------------------------
def test_promotion_without_l2_source_entry_fails(tmp_path):
    p = _project(tmp_path, "src1")
    res = promo.promote(
        project_root=p, distilled="Generalized durable lesson.",
        provenance={"type": "commit_sha", "value": "10507cee"},
        source_entry_ts=None, dry_run=True, data_root=tmp_path / "data")
    assert res["ok"] is False
    assert any("l2-source" in g["gate"] and not g["passed"] for g in res["gates"]), res["gates"]


@pytest.mark.parametrize("layer", ["L0", "L1", "L4"])
def test_promotion_rejects_non_l2_source_layers(tmp_path, monkeypatch, layer):
    p = _project(tmp_path, "src2")
    out_root = tmp_path / "l3out"
    out_root.mkdir()
    monkeypatch.setattr(promo, "CANDIDATES_DIR", out_root)
    res = promo.promote(
        project_root=p, distilled="Looks clean and generalized.",
        provenance={"type": "commit_sha", "value": "10507cee"},
        source_layer=layer, source_entry_ts=None,
        dry_run=False, data_root=tmp_path / "data")          # apply attempted
    assert res["ok"] is False
    assert list(out_root.glob("*.md")) == [], f"{layer}-derived text reached candidate write"
    # the transition table is actually consulted on the execution path
    assert ml.transition_allowed(layer, "L3", via="promotion") is False


def test_promotion_unknown_entry_ts_fails_closed(tmp_path, monkeypatch):
    p = _project(tmp_path, "src3")
    out_root = tmp_path / "l3out"
    out_root.mkdir()
    monkeypatch.setattr(promo, "CANDIDATES_DIR", out_root)
    res = promo.promote(
        project_root=p, distilled="Generalized lesson.",
        provenance={"type": "commit_sha", "value": "10507cee"},
        source_entry_ts=123.456,            # not in this project's L2 store
        dry_run=False, data_root=tmp_path / "data")
    assert res["ok"] is False
    assert list(out_root.glob("*.md")) == []


def test_promotion_happy_path_bound_to_real_l2_entry(tmp_path, monkeypatch):
    p = _project(tmp_path, "src4")
    root = tmp_path / "data"
    ts = _l2_source(p, root, "lesson about explicit enums")
    out_root = tmp_path / "l3out"
    out_root.mkdir()
    monkeypatch.setattr(promo, "CANDIDATES_DIR", out_root)
    res = promo.promote(
        project_root=p, distilled="Prefer explicit capability enums in contracts.",
        provenance={"type": "commit_sha", "value": "10507cee"},
        source_entry_ts=ts, dry_run=False, data_root=root)
    assert res["ok"] is True, res["gates"]
    assert res["written"] is True
    assert len(list(out_root.glob("*.md"))) == 1


def test_promotion_source_cannot_come_from_foreign_project(tmp_path):
    """Source entry must belong to THIS project's L2 store."""
    a = _project(tmp_path, "alpha")
    b = _project(tmp_path, "beta")
    root = tmp_path / "data"
    ts_a = _l2_source(a, root, "alpha-only lesson")
    res = promo.promote(
        project_root=b, distilled="Generalized lesson.",
        provenance={"type": "commit_sha", "value": "10507cee"},
        source_entry_ts=ts_a, dry_run=True, data_root=root)
    assert res["ok"] is False, "beta promoted using alpha's L2 entry"
    assert any("l2-source" in g["gate"] and not g["passed"] for g in res["gates"])


# ---------------------------------------------------------------------------
# R-P5-002 — nested symlink escapes under the data root
# ---------------------------------------------------------------------------
@pytest.mark.skipif(not _can_be_symlinked(), reason="os.symlink unavailable")
def test_l2_rejects_symlinked_projects_dir(tmp_path):
    p = _project(tmp_path, "sym1")
    root = tmp_path / "data"
    root.mkdir()
    outside = tmp_path / "outside"
    (outside / "projects").mkdir(parents=True)
    os.symlink(outside / "projects", root / "projects")   # intermediate symlink
    store = pm.ProjectMemoryStore(p, data_root=root)
    with pytest.raises((pm.StorageUnsafe, ValueError)):
        store.append_entry("must not escape")
    assert list((outside / "projects").rglob("*.jsonl")) == []


@pytest.mark.skipif(not _can_be_symlinked(), reason="os.symlink unavailable")
def test_l2_rejects_leaf_symlink_entries_file(tmp_path):
    p = _project(tmp_path, "sym2")
    root = tmp_path / "data"
    store = pm.ProjectMemoryStore(p, data_root=root)
    store.append_entry("real entry")            # creates the store legitimately
    token = "ghp_" + "leaf" + "0123456789abcdef" * 2
    outside = tmp_path / "outside"
    outside.mkdir()
    victim = outside / "victim.jsonl"
    victim.write_text(token, encoding="utf-8")
    entries = store.memory_dir / "entries.jsonl"
    entries.unlink()
    os.symlink(victim, entries)                 # leaf symlink
    with pytest.raises((pm.StorageUnsafe, ValueError)):
        store.read_entries("anything")          # must not follow the link
    with pytest.raises((pm.StorageUnsafe, ValueError)):
        store.append_entry("append through link")
    assert token in victim.read_text(encoding="utf-8")
    assert victim.read_text(encoding="utf-8") == token, "victim mutated through link"


@pytest.mark.skipif(not _can_be_symlinked(), reason="os.symlink unavailable")
def test_l5_rejects_symlinked_experiment_dir(tmp_path):
    p = _project(tmp_path, "sym3")
    root = tmp_path / "data"
    store = em.ExperimentStore(p, data_root=root)
    outside = tmp_path / "outside"
    (outside / "EXP-1").mkdir(parents=True)
    exps = root / "projects" / "sym3" / "experiments"
    exps.mkdir(parents=True)
    os.symlink(outside / "EXP-1", exps / "EXP-1")
    with pytest.raises((em.StorageUnsafe, ValueError)):
        store.initialize("EXP-1", baseline={"m": 1})
    assert list((outside / "EXP-1").iterdir()) == []


@pytest.mark.skipif(not _can_be_symlinked(), reason="os.symlink unavailable")
def test_l5_rejects_symlinked_baseline_leaf(tmp_path):
    p = _project(tmp_path, "sym4")
    root = tmp_path / "data"
    store = em.ExperimentStore(p, data_root=root)
    d = root / "projects" / "sym4" / "experiments" / "EXP-2"
    d.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    victim = outside / "baseline.json"
    victim.write_text('{"evil": true}', encoding="utf-8")
    os.symlink(victim, d / "baseline.json")
    with pytest.raises((em.StorageUnsafe, ValueError)):
        store.initialize("EXP-2", baseline={"m": 1})
    assert victim.read_text(encoding="utf-8") == '{"evil": true}'


# ---------------------------------------------------------------------------
# R-P5-003 — L5 identity is adapter-authoritative
# ---------------------------------------------------------------------------
def test_l5_identity_comes_from_adapter_not_caller(tmp_path):
    beta_root = _project(tmp_path, "beta")
    root = tmp_path / "data"
    with pytest.raises(em.ProjectIsolationError):
        em.ExperimentStore(beta_root, data_root=root, project_id="alpha")
    # failed before any data access: alpha's storage was never touched
    assert not (root / "projects" / "alpha").exists()


def test_l5_requires_valid_adapter(tmp_path):
    broken = tmp_path / "broken"
    broken.mkdir()
    with pytest.raises((em.AdapterInvalid, pm.AdapterInvalid)):
        em.ExperimentStore(broken, data_root=tmp_path / "data")


def test_l5_respects_project_scope_off(tmp_path):
    p = _project(tmp_path, "scoped",
                 scopes={"global": True, "project": False,
                         "session": True, "private": False})
    with pytest.raises((em.ScopeDenied, pm.ScopeDenied)):
        em.ExperimentStore(p, data_root=tmp_path / "data")


def test_l5_adapter_derived_id_writes_correct_marker(tmp_path):
    a = _project(tmp_path, "alpha")
    store = em.ExperimentStore(a, data_root=tmp_path / "data")
    store.initialize("EXP-9", baseline={"m": 1})
    marker = (tmp_path / "data" / "projects" / "alpha" / "experiments" / "EXP-9" / ".project")
    assert marker.read_text(encoding="utf-8").strip() == "alpha"


def test_l5_structural_crossover_still_isolated(tmp_path):
    a = _project(tmp_path, "alpha")
    b = _project(tmp_path, "beta")
    root = tmp_path / "data"
    sa = em.ExperimentStore(a, data_root=root)
    sb = em.ExperimentStore(b, data_root=root)
    sa.initialize("EXP-1", baseline={"m": 1})
    sa.append_iteration("EXP-1", {"change": "a-only", "score": 0.5})
    assert sb.read_iterations("EXP-1") == []
    sb.initialize("EXP-1", baseline={"m": 2})
    assert sa.read_iterations("EXP-1")[0]["change"] == "a-only"


# ---------------------------------------------------------------------------
# R-P5-004 — provenance privacy + YAML-safe candidate front matter
# ---------------------------------------------------------------------------
def _candidate_dir(tmp_path, monkeypatch):
    out = tmp_path / "l3prov"
    out.mkdir()
    monkeypatch.setattr(promo, "CANDIDATES_DIR", out)
    return out


def test_provenance_secret_value_blocked_even_on_apply(tmp_path, monkeypatch):
    p = _project(tmp_path, "prov1")
    out = _candidate_dir(tmp_path, monkeypatch)
    token = "sk-ant-api03-" + "0123456789abcdef" * 3
    res = promo.promote(
        project_root=p, distilled="Generalized lesson.",
        provenance={"type": "task_ref", "value": token},
        source_entry_ts=_l2_source(p, tmp_path / "data"),
        dry_run=False, data_root=tmp_path / "data")
    assert res["ok"] is False
    assert list(out.glob("*.md")) == [], "secret-bearing provenance written to L3 candidate"


def test_provenance_newline_frontmatter_injection_blocked(tmp_path, monkeypatch):
    p = _project(tmp_path, "prov2")
    out = _candidate_dir(tmp_path, monkeypatch)
    res = promo.promote(
        project_root=p, distilled="Generalized lesson.",
        provenance={"type": "review_finding", "value": "R-P5-001\ninjected: yes"},
        source_entry_ts=_l2_source(p, tmp_path / "data"),
        dry_run=False, data_root=tmp_path / "data")
    assert res["ok"] is False
    assert list(out.glob("*.md")) == []


def test_provenance_control_characters_blocked(tmp_path, monkeypatch):
    p = _project(tmp_path, "prov3")
    res = promo.promote(
        project_root=p, distilled="Generalized lesson.",
        provenance={"type": "handoff_ref", "value": "x\x00y\x1fz"},
        source_entry_ts=_l2_source(p, tmp_path / "data"),
        dry_run=True, data_root=tmp_path / "data")
    assert res["ok"] is False
    assert any("evidence" in g["gate"] and not g["passed"] for g in res["gates"])


@pytest.mark.parametrize("etype,value", [
    ("tests_passed", "not-a-number"),
    ("adr_path", "/etc/decisions/adr-1.md"),      # absolute unix path
    ("wiki_ref", "wiki/../secrets.md"),           # traversal
    ("task_ref", "TASK 12 with spaces"),          # spaces malformed
])
def test_provenance_strict_value_shapes(tmp_path, etype, value):
    p = _project(tmp_path, "prov4")
    res = promo.promote(
        project_root=p, distilled="Generalized lesson.",
        provenance={"type": etype, "value": value},
        source_entry_ts=_l2_source(p, tmp_path / "data"),
        dry_run=True, data_root=tmp_path / "data")
    assert res["ok"] is False, f"{etype}={value!r} must fail shape validation"


def test_candidate_front_matter_is_safe_yaml(tmp_path, monkeypatch):
    p = _project(tmp_path, "prov5")
    out = _candidate_dir(tmp_path, monkeypatch)
    ts = _l2_source(p, tmp_path / "data")
    res = promo.promote(
        project_root=p, distilled="Generalized lesson with provenance-safe front matter.",
        provenance={"type": "task_ref", "value": "TASK-42"},
        source_entry_ts=ts, dry_run=False, data_root=tmp_path / "data")
    assert res["ok"] is True, res["gates"]
    (f,) = list(out.glob("*.md"))
    text = f.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    _, front, _body = text.split("---\n", 2)
    meta = yaml.safe_load(front)                 # parses back cleanly
    assert isinstance(meta, dict)
    assert meta["schema"] == "awiki-promotion-candidate/v1"
    assert meta["provenance"]["type"] == "task_ref"
    assert meta["provenance"]["value"] == "TASK-42"
    assert "injected" not in meta


# ---------------------------------------------------------------------------
# R-P5-005 — status is read-only and private-path-safe
# ---------------------------------------------------------------------------
_DRIVE_LETTER = re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\\\/]")
_UNIX_HOME = re.compile(r"(?:/Users/|/home/)")


def test_status_emits_no_absolute_machine_paths(tmp_path):
    p = _project(tmp_path, "stat1")
    info = mem_status(p, data_root=tmp_path / "data")
    blob = json.dumps(info)
    assert str(tmp_path) not in blob
    assert not _DRIVE_LETTER.search(blob)
    assert not _UNIX_HOME.search(blob)


def test_status_never_mutates_filesystem(tmp_path, monkeypatch):
    """No-create resolution: status must not fall back to creating
    ~/.a-wiki-data, and must not create any storage."""
    p = _project(tmp_path, "stat2")
    fake_home = tmp_path / "fakehome"
    fake_home.mkdir()
    monkeypatch.setenv("USERPROFILE", str(fake_home))
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.delenv("AWIKI_DATA_DIR", raising=False)
    before = sorted(str(q) for q in fake_home.rglob("*"))

    info = mem_status(p, data_root=None)         # default resolution path

    after = sorted(str(q) for q in fake_home.rglob("*"))
    assert before == after, "status mutated the filesystem"
    assert not (fake_home / ".a-wiki-data").exists()
    assert isinstance(info, dict)                # deterministic, no traceback
    assert "storage_ok" in info or info.get("adapter_valid") is False


def test_status_storage_failure_is_deterministic(tmp_path):
    p = _project(tmp_path, "stat3")
    info = mem_status(p, data_root=Path("relative/root"))   # invalid root
    assert isinstance(info, dict)
    assert info["adapter_valid"] is True          # adapter fine, storage broken
    assert info.get("storage_ok") is False        # deterministic failure, no traceback


def test_status_invalid_adapter_reports_without_storage(tmp_path):
    broken = _project(tmp_path, "stat4")
    (broken / ".awiki" / "project.yaml").write_text("schema: [unclosed", encoding="utf-8")
    info = mem_status(broken, data_root=tmp_path / "data")
    assert info["adapter_valid"] is False


# ---------------------------------------------------------------------------
# R-P5-006 — L2 routes through the MemoryLedger seam
# ---------------------------------------------------------------------------
def test_l2_entries_have_ledger_schema(tmp_path):
    p = _project(tmp_path, "seam1")
    root = tmp_path / "data"
    store = pm.ProjectMemoryStore(p, data_root=root)
    ts = store.append_entry("lesson routed through the ledger seam")
    entries_file = root / "projects" / "seam1" / "memory" / "entries.jsonl"
    (line,) = [json.loads(x) for x in entries_file.read_text(encoding="utf-8").splitlines() if x.strip()]
    for key in ("ts", "session_id", "type", "summary"):
        assert key in line, f"ledger schema key {key} missing from L2 entry"
    assert line["ts"] == ts
    assert line["project"] == "seam1"           # project tag preserved
    # readable through the ledger seam itself
    ledger = memory_ledger.MemoryLedger(entries_file)
    assert any("ledger seam" in e["summary"] for e in ledger.search("ledger seam"))


def test_l2_inherits_ledger_secret_redaction(tmp_path):
    p = _project(tmp_path, "seam2")
    store = pm.ProjectMemoryStore(p, data_root=tmp_path / "data")
    token = "sk-" + "red" + "act-me-please-" + "987654"
    store.append_entry(f"leaked {token} in project memory")
    entries_file = tmp_path / "data" / "projects" / "seam2" / "memory" / "entries.jsonl"
    assert token not in entries_file.read_text(encoding="utf-8")


def test_l2_concurrent_appends_stay_valid_jsonl(tmp_path):
    p = _project(tmp_path, "seam3")
    root = tmp_path / "data"
    store = pm.ProjectMemoryStore(p, data_root=root)
    store.append_entry("seed")                  # ensure dirs exist first
    errors: list[Exception] = []

    def worker(n: int):
        try:
            s = pm.ProjectMemoryStore(p, data_root=root)
            for i in range(5):
                s.append_entry(f"concurrent-{n}-{i}")
        except Exception as e:                  # noqa: BLE001 -- recorded for assert
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(n,)) for n in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
    entries_file = root / "projects" / "seam3" / "memory" / "entries.jsonl"
    lines = [x for x in entries_file.read_text(encoding="utf-8").splitlines() if x.strip()]
    assert len(lines) == 11                      # 1 seed + 2×5 concurrent
    parsed = [json.loads(x) for x in lines]      # every line valid JSON
    assert all(e.get("project") == "seam3" for e in parsed)


def test_l2_isolation_guard_skips_foreign_lines(tmp_path):
    p = _project(tmp_path, "seam4")
    root = tmp_path / "data"
    store = pm.ProjectMemoryStore(p, data_root=root)
    store.append_entry("own entry")
    entries_file = root / "projects" / "seam4" / "memory" / "entries.jsonl"
    foreign = json.dumps({"ts": 999.0, "session_id": "x", "type": "lesson",
                          "summary": "own entry foreign", "tags": [],
                          "project": "someone-else"})
    with entries_file.open("a", encoding="utf-8") as f:
        f.write(foreign + "\n")
    hits = store.read_entries("entry")
    assert all(h.get("project") == "seam4" for h in hits), "foreign line leaked through"


def test_memory_ledger_vanilla_append_unchanged(tmp_path):
    """The narrowly-justified ledger extension must not alter vanilla callers."""
    ledger = memory_ledger.MemoryLedger(tmp_path / "vanilla.jsonl")
    ledger.append(session_id="s", type="lesson", summary="plain")
    (line,) = [json.loads(x) for x in (tmp_path / "vanilla.jsonl").read_text(encoding="utf-8").splitlines()]
    assert set(line.keys()) == {"ts", "session_id", "type", "summary", "files", "tags", "parent_ts"}
