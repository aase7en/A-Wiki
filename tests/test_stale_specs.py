"""Stale-spec gate + plan fold-back — Slice D (community patterns).

1) check-stale-specs: a plan/ADR with frontmatter `scope:` owns files;
   if a scoped file's LAST COMMIT is newer than the plan's last commit,
   the plan is stale -> CI red (unless `plan-frozen: true`).
2) plan_foldback: session-end — today's ledger decisions touching a
   plan's scope are folded back into the plan's Deviations section
   (idempotent), so chat memory never stays the only record.
"""
from __future__ import annotations

import importlib.util as ilu
import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
_spec = ilu.spec_from_file_location("stale", REPO_ROOT / "scripts" / "check-stale-specs.py")
stale = ilu.module_from_spec(_spec)
_spec.loader.exec_module(stale)

_fb = ilu.spec_from_file_location("fb", REPO_ROOT / "scripts" / "hooks" / "plan_foldback.py")
fb = ilu.module_from_spec(_fb)
_fb.loader.exec_module(fb)


def _git_repo(tmp_path: Path) -> Path:
    r = tmp_path / "repo"
    r.mkdir()
    def git(*a):
        subprocess.run(["git", *a], cwd=r, check=True, capture_output=True,
                       timeout=60)
    git("init", "-q")
    git("config", "user.email", "t@t"); git("config", "user.name", "t")
    return r


def _commit(r: Path, msg: str, path: Path = None):
    subprocess.run(["git", "add", "-A"], cwd=r, check=True,
                   capture_output=True)
    subprocess.run(["git", "commit", "-q", "-m", msg], cwd=r,
                   check=True, capture_output=True)


def _sleep_commit_gap():
    time.sleep(1.1)  # git commit timestamps share a second by default


def test_fresh_plan_passes(tmp_path):
    r = _git_repo(tmp_path)
    plan = r / "PLAN.md"
    plan.write_text("---\nscope:\n  - src/app.py\n---\n# plan\n",
                    encoding="utf-8")
    src = r / "src" / "app.py"; src.parent.mkdir()
    src.write_text("x = 1\n", encoding="utf-8")
    _commit(r, "add plan+src")
    problems = stale.check_repo(r)
    assert problems == []


def test_scoped_file_newer_than_plan_fails(tmp_path):
    r = _git_repo(tmp_path)
    (r / "docs" / "plans").mkdir(parents=True, exist_ok=True)
    plan = r / "docs" / "plans" / "plan-x.md"
    plan.write_text("---\nscope:\n  - src/app.py\n---\n# plan\n",
                    encoding="utf-8")
    src = r / "src" / "app.py"; src.parent.mkdir()
    src.write_text("x = 1\n", encoding="utf-8")
    _commit(r, "add plan+src", plan)
    _sleep_commit_gap()
    src.write_text("x = 2\n", encoding="utf-8")
    _commit(r, "touch scoped file only", src)
    problems = stale.check_repo(r)
    assert problems and any("plan-x.md" in p for p in problems),         f"expected stale plan-x, got: {problems}"


def test_frozen_plan_exempt(tmp_path):
    r = _git_repo(tmp_path)
    plan = r / "PLAN.md"
    plan.write_text("---\nplan-frozen: true\nscope:\n  - src/app.py\n---\n# plan\n",
                    encoding="utf-8")
    src = r / "src" / "app.py"; src.parent.mkdir()
    src.write_text("x = 1\n", encoding="utf-8")
    _commit(r, "add", plan)
    _sleep_commit_gap()
    src.write_text("x = 2\n", encoding="utf-8")
    _commit(r, "later change", src)
    assert stale.check_repo(r) == []


# ── fold-back ─────────────────────────────────────────────────────────
PLAN = "---\nscope:\n  - src/app.py\n---\n# plan\n\nbody\n"


def _ledger(tmp_path, entries):
    p = tmp_path / "ledger.jsonl"
    p.write_text("\n".join(json.dumps(e, ensure_ascii=False)
                            for e in entries) + "\n", encoding="utf-8")
    return p


def test_foldback_appends_today_decision_touching_scope(tmp_path):
    plan = tmp_path / "PLAN.md"
    plan.write_text(PLAN, encoding="utf-8")
    now = time.time()
    ledger = _ledger(tmp_path, [
        {"ts": now, "type": "decision", "session_id": "s1",
         "summary": "เปลี่ยน src/app.py ใช้ config แทน env",
         "tags": ["src/app.py"]},
        {"ts": now, "type": "decision", "session_id": "s1",
         "summary": "unrelated decision about docs only", "tags": []},
    ])
    folded = fb.foldback(plan, ledger)
    text = plan.read_text(encoding="utf-8")
    assert folded == 1
    assert "## Deviations (auto-folded)" in text
    assert "src/app.py" in text and "config แทน env" in text
    assert "unrelated decision" not in text


def test_foldback_idempotent(tmp_path):
    plan = tmp_path / "PLAN.md"
    plan.write_text(PLAN, encoding="utf-8")
    now = time.time()
    ledger = _ledger(tmp_path, [
        {"ts": now, "type": "decision", "session_id": "s1",
         "summary": "แก้ src/app.py เรื่อง cache", "tags": ["src/app.py"]}])
    fb.foldback(plan, ledger)
    first = plan.read_text(encoding="utf-8")
    assert fb.foldback(plan, ledger) == 0
    assert plan.read_text(encoding="utf-8") == first
