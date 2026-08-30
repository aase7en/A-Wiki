"""Skill pipeline — Slice B: unlimited skill updates with a frame.

Contract (user promise: "อัปเดททักษะไม่จำกัด" + Iron Law #3):
  content/external/pattern signals -> PROPOSAL (queued, never auto-applied)
  -> AUTO-EVAL (generated suite, deterministic) -> ready flag
  -> ONE-BUTTON approve (new-skill --apply + regen + ledger provenance)

The user stays the Senior Critic: nothing lands in the registry without
an explicit approve.
"""
from __future__ import annotations

import importlib.util as ilu
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
spec = ilu.spec_from_file_location("pipe", REPO_ROOT / "scripts" / "lib" / "skill_pipeline.py")
pipe = ilu.module_from_spec(spec)
spec.loader.exec_module(pipe)


@pytest.fixture()
def workdir(tmp_path):
    return tmp_path / "pipe"


def _page(tmp_path, name="thai-tax-workflow", body="คำนวณภาษี"):
    p = tmp_path / "wiki" / "concepts" / "business" / f"{name}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        f"---\ntitle: {name}\ntags: [business, tax]\n---\n\n# {name}\n\n{body}\n",
        encoding="utf-8")
    return p


def test_propose_from_wiki_page_creates_queued_proposal(workdir, tmp_path):
    page = _page(tmp_path)
    prop = pipe.propose_from_page(page, queue_dir=workdir,
                                  source_note="promotion 2026-08-23")
    f = workdir / f"{prop['id']}.json"
    assert f.is_file(), "proposal must be durable on disk"
    saved = json.loads(f.read_text(encoding="utf-8"))
    assert saved["id"] == prop["id"] == "thai-tax-workflow"
    assert saved["source"] == "content"
    assert saved["status"] == "draft"
    assert saved["description"], "description feeds tier-2 routing later"
    assert saved["source_note"] == "promotion 2026-08-23"
    assert saved["skill_md"], "draft SKILL.md generated for eval"


def test_propose_is_idempotent(workdir, tmp_path):
    page = _page(tmp_path)
    a = pipe.propose_from_page(page, queue_dir=workdir)
    b = pipe.propose_from_page(page, queue_dir=workdir)
    assert a["id"] == b["id"]
    assert len(list(workdir.glob("*.json"))) == 1


def test_propose_external_enters_same_queue(workdir):
    prop = pipe.propose_external(
        name="pdf-table-extract",
        description="Extract tables from PDFs into CSV (found on GitHub)",
        url="https://github.com/example/pdf-table-extract",
        queue_dir=workdir)
    saved = json.loads((workdir / f"{prop['id']}.json").read_text(encoding="utf-8"))
    assert saved["source"] == "external" and saved["url"].endswith("pdf-table-extract")
    assert saved["status"] == "draft"


def test_auto_eval_marks_ready_and_generates_suite(workdir, tmp_path):
    page = _page(tmp_path, name="thai-tax-workflow")
    prop = pipe.propose_from_page(page, queue_dir=workdir)
    result = pipe.run_eval(prop["id"], queue_dir=workdir,
                           brain_root=REPO_ROOT, scratch=tmp_path / "eval")
    saved = pipe.load(prop["id"], queue_dir=workdir)
    assert saved["status"] == "ready", f"eval said: {result}"
    assert saved["eval"]["suite"]["required"], "suite has required terms"
    assert saved["eval"]["passed"] is True


def test_auto_eval_fails_bad_draft(workdir, tmp_path):
    page = _page(tmp_path, name="empty-skill-thing")
    prop = pipe.propose_from_page(page, queue_dir=workdir)
    saved_path = workdir / f"{prop['id']}.json"
    saved = json.loads(saved_path.read_text(encoding="utf-8"))
    saved["skill_md"] = "# nothing useful\n\ndocument body missing entirely\n"
    saved_path.write_text(json.dumps(saved, ensure_ascii=False), encoding="utf-8")
    pipe.run_eval(prop["id"], queue_dir=workdir,
                  brain_root=REPO_ROOT, scratch=tmp_path / "eval2")
    after = pipe.load(prop["id"], queue_dir=workdir)
    assert after["status"] == "failed"
    assert after["eval"]["passed"] is False


def test_approve_applies_via_injected_command(workdir, tmp_path):
    page = _page(tmp_path, name="thai-tax-workflow")
    prop = pipe.propose_from_page(page, queue_dir=workdir)
    pipe.run_eval(prop["id"], queue_dir=workdir,
                  brain_root=REPO_ROOT, scratch=tmp_path / "e")
    calls = []
    def fake_apply(payload):
        calls.append(payload)
        return 0, ""
    rc = pipe.approve(prop["id"], queue_dir=workdir, apply_fn=fake_apply)
    assert rc == 0 and calls, "apply command must be invoked once"
    assert calls[0]["id"] == "thai-tax-workflow"
    saved = pipe.load(prop["id"], queue_dir=workdir)
    assert saved["status"] == "approved"
    assert saved["approved_at"], "provenance recorded"


def test_approve_refuses_draft_without_eval(workdir, tmp_path):
    page = _page(tmp_path)
    prop = pipe.propose_from_page(page, queue_dir=workdir)
    rc = pipe.approve(prop["id"], queue_dir=workdir,
                      apply_fn=lambda p: (0, ""))
    assert rc != 0, "unapproved quality gate: drafts cannot be applied"


def test_list_groups_by_status(workdir, tmp_path):
    p1 = _page(tmp_path, name="alpha-thing")
    p2 = _page(tmp_path, name="beta-thing")
    pipe.propose_from_page(p1, queue_dir=workdir)
    pipe.propose_from_page(p2, queue_dir=workdir)
    pipe.run_eval("beta-thing", queue_dir=workdir,
                  brain_root=REPO_ROOT, scratch=tmp_path / "s")
    listed = pipe.list_proposals(queue_dir=workdir)
    assert {x["status"] for x in listed} >= {"draft", "ready"}


def test_scout_fills_gaps_into_the_queue(workdir, monkeypatch):
    """skill-scout: registry gap -> external search -> same proposal queue."""
    def fake_search(gap, limit):
        return [{"name": "excel-formula-fix",
                 "description": "Repair broken Excel formulas (repo found)",
                 "url": "https://github.com/x/excel-formula-fix"}]
    monkeypatch.setattr(pipe, "_search_external", fake_search)
    created = pipe.scout_gaps(
        gaps=["excel formula repair"],
        queue_dir=workdir, registry_path=REPO_ROOT / "skills-registry.json")
    assert any(p["id"] == "excel-formula-fix" and p["source"] == "external"
               for p in created)
    # gap already covered by the registry must NOT be proposed
    def fake_search_all(gap, limit):
        raise AssertionError("must not search for a covered gap")
    monkeypatch.setattr(pipe, "_search_external", fake_search_all)
    again = pipe.scout_gaps(gaps=["hermes agent orchestration"],
                             queue_dir=workdir,
                             registry_path=REPO_ROOT / "skills-registry.json")
    assert again == []


# ---------------------------------------------------------------------------
# R-FR-001 — evaluated artifact identity must bind approval/apply
# ---------------------------------------------------------------------------


def test_auto_eval_binds_exact_artifact_bytes(workdir, tmp_path):
    import hashlib

    page = _page(tmp_path, name="artifact-bound-skill")
    prop = pipe.propose_from_page(page, queue_dir=workdir)
    expected = prop["skill_md"].encode("utf-8")

    result = pipe.run_eval(prop["id"], queue_dir=workdir,
                           brain_root=REPO_ROOT, scratch=tmp_path / "exact-eval")

    assert (tmp_path / "exact-eval" / f"{prop['id']}-draft-SKILL.md").read_bytes() == expected
    assert result["artifact"] == {
        "sha256": hashlib.sha256(expected).hexdigest(),
        "size": len(expected),
        "encoding": "utf-8",
    }


def test_approve_rejects_post_eval_artifact_drift_and_requires_reeval(workdir, tmp_path):
    page = _page(tmp_path, name="artifact-drift-skill")
    prop = pipe.propose_from_page(page, queue_dir=workdir)
    pipe.run_eval(prop["id"], queue_dir=workdir,
                  brain_root=REPO_ROOT, scratch=tmp_path / "drift-eval")

    saved_path = workdir / f"{prop['id']}.json"
    saved = json.loads(saved_path.read_text(encoding="utf-8"))
    saved["skill_md"] += "\n## Mutated after eval\nthis content was never evaluated\n"
    saved_path.write_text(json.dumps(saved, ensure_ascii=False), encoding="utf-8")

    calls = []
    rc = pipe.approve(prop["id"], queue_dir=workdir,
                      apply_fn=lambda payload: (calls.append(payload) or (0, "")))

    assert rc != 0
    assert calls == [], "stale evaluated content must never reach apply"
    after = pipe.load(prop["id"], queue_dir=workdir)
    assert after["status"] == "draft", "artifact drift must require explicit re-evaluation"
    assert after["eval"]["stale"] is True
    assert after["eval"]["current_artifact"]["sha256"] != after["eval"]["artifact"]["sha256"]


def test_approve_records_exact_approved_artifact_identity(workdir, tmp_path):
    page = _page(tmp_path, name="artifact-provenance-skill")
    prop = pipe.propose_from_page(page, queue_dir=workdir)
    pipe.run_eval(prop["id"], queue_dir=workdir,
                  brain_root=REPO_ROOT, scratch=tmp_path / "approved-eval")

    assert pipe.approve(prop["id"], queue_dir=workdir,
                        apply_fn=lambda payload: (0, "ok")) == 0
    saved = pipe.load(prop["id"], queue_dir=workdir)
    assert saved["approved_artifact"] == saved["eval"]["artifact"]


def test_default_apply_hands_new_skill_exact_artifact_and_expected_hash(monkeypatch):
    import hashlib
    import subprocess
    from types import SimpleNamespace

    artifact = "---\nname: exact-handoff\ndescription: exact\n---\n\n# exact-handoff\n"
    digest = hashlib.sha256(artifact.encode("utf-8")).hexdigest()
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = list(cmd)
        captured["kwargs"] = dict(kwargs)
        if "--skill-file" in cmd:
            p = Path(cmd[cmd.index("--skill-file") + 1])
            captured["path"] = p
            captured["bytes"] = p.read_bytes()
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    rc, _ = pipe._default_apply({
        "id": "exact-handoff",
        "skill_md": artifact,
        "eval": {"artifact": {"sha256": digest, "size": len(artifact.encode("utf-8")),
                                "encoding": "utf-8"}},
    })

    assert rc == 0
    assert captured["bytes"] == artifact.encode("utf-8")
    assert captured["cmd"][captured["cmd"].index("--expected-sha256") + 1] == digest
    assert "--apply" in captured["cmd"]
    assert not captured["path"].exists(), "temporary handoff artifact must be cleaned after apply"


def test_generated_pipeline_draft_uses_canonical_registry_domain(workdir, tmp_path):
    import re
    import sys

    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from skills_registry import VALID_DOMAINS

    prop = pipe.propose_from_page(_page(tmp_path, name="domain-valid-skill"), queue_dir=workdir)
    match = re.search(r"^domain:\s*\[([^\]]+)\]", prop["skill_md"], re.MULTILINE)
    assert match, "generated skill draft must declare a domain"
    domains = [item.strip() for item in match.group(1).split(",") if item.strip()]
    assert domains and all(domain in VALID_DOMAINS for domain in domains)
