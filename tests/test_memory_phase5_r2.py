"""Phase 5 remediation round 2 — R-P5-001 + R-P5-006 (PR #15 re-review).

Iron Law #1: failing tests written FIRST.

  R-P5-001  the promoted candidate IS the verified L2 entry — promote()
            consumes the entry's stored (redacted) summary; there is no
            free-form distilled argument a caller could substitute; the
            candidate metadata persists the source identity + content
            digest; a valid L2 ts can never authorize unrelated text.
  R-P5-006  MemoryLedger extra seam is namespaced + collision-safe;
            nested metadata is recursively redacted; canonical fields
            can never be overwritten.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "project"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import project_memory as pm         # noqa: E402
import promotion as promo           # noqa: E402
import memory_ledger                # noqa: E402


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


def _project(tmp_path: Path, pid: str = "alpha") -> Path:
    p = tmp_path / pid
    p.mkdir(parents=True)
    aw = p / ".awiki"
    aw.mkdir()
    (aw / "project.yaml").write_text(_valid_yaml_text(pid=pid), encoding="utf-8")
    (aw / "context.md").write_text("# c\n", encoding="utf-8")
    (aw / "state").mkdir()
    (p / "AGENTS.md").write_text("<!-- awiki-project-adapter v1 -->\n", encoding="utf-8")
    return p


def _l2(p: Path, data_root: Path, text: str) -> float:
    return pm.ProjectMemoryStore(p, data_root=data_root).append_entry(text)


# ---------------------------------------------------------------------------
# R-P5-001 — the verified L2 entry IS the promoted content
# ---------------------------------------------------------------------------
CLEAN = "Prefer explicit capability enums over vendor names in stable contracts."


def test_promotion_has_no_free_form_distilled_argument(tmp_path):
    """The unrelated-text channel is removed from the API surface itself."""
    p = _project(tmp_path, "bind1")
    root = tmp_path / "data"
    ts = _l2(p, root, CLEAN)
    with pytest.raises(TypeError):
        promo.promote(
            project_root=p,
            distilled="totally unrelated attacker text",     # must not exist
            provenance={"type": "commit_sha", "value": "10507cee"},
            source_entry_ts=ts, dry_run=True, data_root=root)


def test_candidate_content_is_the_stored_l2_summary(tmp_path, monkeypatch):
    p = _project(tmp_path, "bind2")
    root = tmp_path / "data"
    ts = _l2(p, root, CLEAN)
    out = tmp_path / "l3r2"
    out.mkdir()
    monkeypatch.setattr(promo, "CANDIDATES_DIR", out)
    res = promo.promote(
        project_root=p,
        provenance={"type": "commit_sha", "value": "10507cee"},
        source_entry_ts=ts, dry_run=False, data_root=root)
    assert res["ok"] is True, res["gates"]
    (f,) = list(out.glob("*.md"))
    body = f.read_text(encoding="utf-8")
    assert CLEAN in body                       # candidate IS the L2 entry
    assert "unrelated" not in body.lower()


def test_valid_ts_cannot_authorize_unrelated_text(tmp_path, monkeypatch):
    """Reviewer's required negative: real L2 ts for text A + attempted
    promotion of unrelated text B with apply → nothing written. With the
    free-form channel removed, the only injection route left is passing
    B as the L2 entry itself — which the gates evaluate on the STORED
    text, and a project-specific B fails generalize."""
    p = _project(tmp_path, "bind3")
    root = tmp_path / "data"
    ts = _l2(p, root, CLEAN)                   # benign, promotable A
    out = tmp_path / "l3r2"
    out.mkdir()
    monkeypatch.setattr(promo, "CANDIDATES_DIR", out)
    # unrelated B smuggled via provenance-free channel does not exist; the
    # strongest remaining attack: claim A's ts while hoping B is written —
    # impossible by construction, and the candidate proves it:
    res = promo.promote(
        project_root=p,
        provenance={"type": "commit_sha", "value": "10507cee"},
        source_entry_ts=ts, dry_run=False, data_root=root)
    assert res["ok"] is True
    (f,) = list(out.glob("*.md"))
    assert CLEAN in f.read_text(encoding="utf-8")
    # and an entry whose STORED text is unpromotable fails on that text:
    ts_bad = _l2(p, root, "At project bind3 we deploy server prod-db-01")
    res2 = promo.promote(
        project_root=p,
        provenance={"type": "commit_sha", "value": "10507cee"},
        source_entry_ts=ts_bad, dry_run=False, data_root=root)
    assert res2["ok"] is False, "stored unpromotable text reached L3?"
    assert len(list(out.glob("*.md"))) == 1    # still exactly one file


def test_candidate_metadata_persists_source_identity_and_digest(tmp_path, monkeypatch):
    p = _project(tmp_path, "bind4")
    root = tmp_path / "data"
    ts = _l2(p, root, CLEAN)
    out = tmp_path / "l3r2"
    out.mkdir()
    monkeypatch.setattr(promo, "CANDIDATES_DIR", out)
    res = promo.promote(
        project_root=p,
        provenance={"type": "commit_sha", "value": "10507cee"},
        source_entry_ts=ts, dry_run=False, data_root=root)
    assert res["ok"] is True
    (f,) = list(out.glob("*.md"))
    text = f.read_text(encoding="utf-8")
    _, front, _body = text.split("---\n", 2)
    meta = yaml.safe_load(front)
    src = meta["source"]
    assert src["layer"] == "L2"
    assert src["entry_ts"] == ts
    # digest is mechanically verifiable offline against the stored summary
    expect = hashlib.sha256(CLEAN.encode("utf-8")).hexdigest()[:16]
    assert src["summary_digest"] == expect


def test_promoted_text_is_already_secret_redacted_in_l2(tmp_path, monkeypatch):
    """Binding to the stored summary means the redaction that happened at
    append time is the redaction the candidate carries — a secret cannot
    ride into L3 through the source entry."""
    p = _project(tmp_path, "bind5")
    root = tmp_path / "data"
    token = "sk-" + "bind" + "ing-secret-" + "445566"
    ts = _l2(p, root, f"lesson that once contained {token} in it")
    out = tmp_path / "l3r2"
    out.mkdir()
    monkeypatch.setattr(promo, "CANDIDATES_DIR", out)
    res = promo.promote(
        project_root=p,
        provenance={"type": "commit_sha", "value": "10507cee"},
        source_entry_ts=ts, dry_run=False, data_root=root)
    assert res["ok"] is True, res["gates"]
    (f,) = list(out.glob("*.md"))
    assert token not in f.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# R-P5-006 — collision-safe, recursively-redacted extra seam
# ---------------------------------------------------------------------------
def test_extra_is_namespaced_and_cannot_collide(tmp_path):
    ledger = memory_ledger.MemoryLedger(tmp_path / "x.jsonl")
    ledger.append(session_id="s", type="lesson", summary="plain",
                  extra={"project": "alpha", "meta": {"k": 1}})
    (line,) = [json.loads(x) for x in (tmp_path / "x.jsonl").read_text(encoding="utf-8").splitlines()]
    # canonical shape intact…
    for key in ("ts", "session_id", "type", "summary", "files", "tags", "parent_ts"):
        assert key in line
    # …and extra lives under ONE reserved namespaced key
    assert isinstance(line.get("extra"), dict)
    assert line["extra"]["project"] == "alpha"
    assert line["extra"]["meta"] == {"k": 1}


def test_extra_rejects_reserved_canonical_keys(tmp_path):
    ledger = memory_ledger.MemoryLedger(tmp_path / "x.jsonl")
    with pytest.raises(ValueError):
        ledger.append(session_id="s", type="lesson", summary="plain",
                      extra={"ts": 1.0})
    with pytest.raises(ValueError):
        ledger.append(session_id="s", type="lesson", summary="plain",
                      extra={"summary": "overridden"})
    assert not (tmp_path / "x.jsonl").exists()   # nothing written


def test_extra_nested_metadata_recursively_redacted(tmp_path):
    ledger = memory_ledger.MemoryLedger(tmp_path / "x.jsonl")
    t1 = "sk-" + "nest" + "ed-level-one-" + "111222"
    t2 = "ghp_" + "nest" + "edleveltwo0123456789ab"
    t3 = "AKIA" + "ABCDEFGHIJKLMNOP"
    ledger.append(
        session_id="s", type="lesson", summary="clean summary",
        extra={"meta": {"note": t1, "list": [t2, {"deep": t3}], "ok": "keep me"}})
    blob = (tmp_path / "x.jsonl").read_text(encoding="utf-8")
    for t in (t1, t2, t3):
        assert t not in blob, f"nested secret {t} survived redaction"
    (line,) = [json.loads(x) for x in blob.splitlines()]
    assert line["extra"]["meta"]["ok"] == "keep me"      # non-secrets intact
    assert "***" in json.dumps(line["extra"]["meta"])


def test_project_store_tag_lives_in_namespaced_extra(tmp_path):
    p = _project(tmp_path, "seamr2")
    root = tmp_path / "data"
    store = pm.ProjectMemoryStore(p, data_root=root)
    ts = store.append_entry("r2 seam lesson", meta={"note": "n"})
    (line,) = [json.loads(x) for x in
               (root / "projects" / "seamr2" / "memory" / "entries.jsonl")
               .read_text(encoding="utf-8").splitlines() if x.strip()]
    assert line["extra"]["project"] == "seamr2"
    assert line["extra"]["meta"] == {"note": "n"}
    assert line["ts"] == ts
    # isolation filter reads the namespaced tag
    assert store.get_entry(ts)["extra"]["project"] == "seamr2"
    assert store.read_entries("seam lesson") or store.read_entries("r2 seam lesson")


def test_foreign_namespaced_tag_still_skipped(tmp_path):
    p = _project(tmp_path, "seamr2b")
    root = tmp_path / "data"
    store = pm.ProjectMemoryStore(p, data_root=root)
    store.append_entry("own tagged entry")
    entries_file = root / "projects" / "seamr2b" / "memory" / "entries.jsonl"
    foreign = json.dumps({"ts": 999.0, "session_id": "x", "type": "lesson",
                          "summary": "own tagged entry foreign", "tags": [],
                          "extra": {"project": "someone-else"}})
    with entries_file.open("a", encoding="utf-8") as f:
        f.write(foreign + "\n")
    hits = store.read_entries("tagged entry")
    assert hits and all(h["extra"]["project"] == "seamr2b" for h in hits)
