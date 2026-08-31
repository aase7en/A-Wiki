"""Stale-spec gate + plan fold-back — Slice D (community patterns).

1) check-stale-specs: a plan/ADR with frontmatter `scope:` owns exact paths;
   any scoped-path change reachable after the spec commit makes it stale,
   and unknown/shallow Git history fails closed (unless `plan-frozen: true`).
2) plan_foldback: session-end — today's ledger decisions touching a
   plan's scope are folded back into the plan's Deviations section
   (idempotent), so chat memory never stays the only record.
"""
from __future__ import annotations

import importlib.util as ilu
import json
import os
import re
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
    (r / "docs" / "plans").mkdir(parents=True)
    plan = r / "docs" / "plans" / "fresh.md"
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
    (r / "docs" / "plans").mkdir(parents=True)
    plan = r / "docs" / "plans" / "frozen.md"
    plan.write_text("---\nplan-frozen: true\nscope:\n  - src/app.py\n---\n# plan\n",
                    encoding="utf-8")
    src = r / "src" / "app.py"; src.parent.mkdir()
    src.write_text("x = 1\n", encoding="utf-8")
    _commit(r, "add", plan)
    _sleep_commit_gap()
    src.write_text("x = 2\n", encoding="utf-8")
    _commit(r, "later change", src)
    assert stale.check_repo(r) == []


def _commit_with_date(r: Path, msg: str, when: str):
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = when
    env["GIT_COMMITTER_DATE"] = when
    subprocess.run(["git", "add", "-A"], cwd=r, check=True,
                   capture_output=True, env=env)
    subprocess.run(["git", "commit", "-q", "-m", msg], cwd=r,
                   check=True, capture_output=True, env=env)


def test_clock_skew_does_not_hide_scoped_change(tmp_path):
    r = _git_repo(tmp_path)
    (r / "docs" / "plans").mkdir(parents=True)
    plan = r / "docs" / "plans" / "clock.md"
    src = r / "src" / "app.py"; src.parent.mkdir()
    plan.write_text("---\nscope:\n  - src/app.py\n---\n# plan\n", encoding="utf-8")
    src.write_text("x = 1\n", encoding="utf-8")
    _commit_with_date(r, "baseline", "2030-01-01T00:00:00+0000")
    src.write_text("x = 2\n", encoding="utf-8")
    _commit_with_date(r, "later topology, older clock", "2000-01-01T00:00:00+0000")
    problems = stale.check_repo(r)
    assert problems and any("clock.md" in p for p in problems), problems


def test_shallow_history_fails_closed(tmp_path):
    source_parent = tmp_path / "source-parent"; source_parent.mkdir()
    r = _git_repo(source_parent)
    (r / "docs" / "plans").mkdir(parents=True)
    plan = r / "docs" / "plans" / "shallow.md"
    src = r / "src" / "app.py"; src.parent.mkdir()
    plan.write_text("---\nscope:\n  - src/app.py\n---\n# plan\n", encoding="utf-8")
    src.write_text("x = 1\n", encoding="utf-8")
    _commit(r, "plan and src")
    (r / "README.md").write_text("tip\n", encoding="utf-8")
    _commit(r, "unrelated tip")
    clone = tmp_path / "shallow-clone"
    subprocess.run(["git", "clone", "--depth", "1", "-q", r.as_uri(), str(clone)],
                   check=True, capture_output=True, timeout=60)
    problems = stale.check_repo(clone)
    assert problems and any("shallow" in p.lower() for p in problems), problems


def test_scope_path_normalizes_cross_platform_separators():
    assert stale._normalize_scope_path(r"src\app.py") == "src/app.py"
    assert stale._normalize_scope_path("./src/app.py") == "src/app.py"


@pytest.mark.parametrize("raw", [
    "../src/app.py",
    "src/../app.py",
    "/src/app.py",
    "C:" + "/src/app.py",
    "C:" + "\\" + "src\\app.py",
    "\\" * 2 + "server\\share\\app.py",
])
def test_scope_path_rejects_escape_or_absolute_forms(raw):
    with pytest.raises(ValueError):
        stale._normalize_scope_path(raw)


def test_missing_scoped_path_history_fails_closed(tmp_path):
    r = _git_repo(tmp_path)
    (r / "docs" / "plans").mkdir(parents=True)
    plan = r / "docs" / "plans" / "missing.md"
    plan.write_text("---\nscope:\n  - src/missing.py\n---\n# plan\n", encoding="utf-8")
    _commit(r, "plan references missing path")
    problems = stale.check_repo(r)
    assert problems and any("src/missing.py" in p for p in problems), problems


def test_deleted_scoped_file_after_plan_is_stale(tmp_path):
    r = _git_repo(tmp_path)
    (r / "docs" / "plans").mkdir(parents=True)
    plan = r / "docs" / "plans" / "delete.md"
    src = r / "src" / "app.py"; src.parent.mkdir()
    plan.write_text("---\nscope:\n  - src/app.py\n---\n# plan\n", encoding="utf-8")
    src.write_text("x = 1\n", encoding="utf-8")
    _commit(r, "plan and src")
    subprocess.run(["git", "rm", "-q", "src/app.py"], cwd=r, check=True,
                   capture_output=True)
    _commit(r, "delete scoped file")
    problems = stale.check_repo(r)
    assert problems and any("delete.md" in p for p in problems), problems


def test_scope_history_uses_literal_pathspecs(tmp_path):
    r = _git_repo(tmp_path)
    (r / "docs" / "plans").mkdir(parents=True)
    plan = r / "docs" / "plans" / "literal.md"
    src_dir = r / "src"; src_dir.mkdir()
    literal = src_dir / "[ab].py"
    other = src_dir / "a.py"
    plan.write_text("---\nscope:\n  - src/[ab].py\n---\n# plan\n", encoding="utf-8")
    literal.write_text("literal = 1\n", encoding="utf-8")
    other.write_text("other = 1\n", encoding="utf-8")
    _commit_with_date(r, "baseline", "2000-01-01T00:00:00+0000")
    other.write_text("other = 2\n", encoding="utf-8")
    _commit_with_date(r, "change only glob lookalike", "2030-01-01T00:00:00+0000")
    assert stale.check_repo(r) == []


def test_non_git_history_fails_closed(tmp_path):
    r = tmp_path / "not-a-repo"
    (r / "docs" / "plans").mkdir(parents=True)
    (r / "src").mkdir()
    (r / "docs" / "plans" / "nogit.md").write_text(
        "---\nscope:\n  - src/app.py\n---\n# plan\n", encoding="utf-8")
    (r / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
    problems = stale.check_repo(r)
    assert problems and any("history" in p.lower() or "git" in p.lower() for p in problems), problems


def test_core_ci_fetches_full_history_for_stale_spec_gate():
    text = (REPO_ROOT / ".github" / "workflows" / "ci-core.yml").read_text(encoding="utf-8")
    assert re.search(
        r"(?m)^      - name: Checkout\n"
        r"        uses: actions/checkout@v4\n"
        r"        with:\n"
        r"          fetch-depth: 0$",
        text,
    ), "Core verification checkout must fetch full Git history for stale-spec semantics"


def test_spec_update_after_scoped_change_restores_freshness(tmp_path):
    r = _git_repo(tmp_path)
    (r / "docs" / "plans").mkdir(parents=True)
    plan = r / "docs" / "plans" / "updated.md"
    src = r / "src" / "app.py"; src.parent.mkdir()
    plan.write_text("---\nscope:\n  - src/app.py\n---\n# plan v1\n", encoding="utf-8")
    src.write_text("x = 1\n", encoding="utf-8")
    _commit(r, "baseline")
    src.write_text("x = 2\n", encoding="utf-8")
    _commit(r, "change scoped file")
    assert stale.check_repo(r), "target change after spec must be stale before spec refresh"
    plan.write_text("---\nscope:\n  - src/app.py\n---\n# plan v2 covers x=2\n", encoding="utf-8")
    _commit(r, "refresh spec")
    assert stale.check_repo(r) == []


def test_rename_of_scoped_path_after_spec_is_stale(tmp_path):
    r = _git_repo(tmp_path)
    (r / "docs" / "plans").mkdir(parents=True)
    plan = r / "docs" / "plans" / "rename.md"
    src = r / "src" / "old.py"; src.parent.mkdir()
    plan.write_text("---\nscope:\n  - src/old.py\n---\n# plan\n", encoding="utf-8")
    src.write_text("x = 1\n", encoding="utf-8")
    _commit(r, "baseline")
    subprocess.run(["git", "mv", "src/old.py", "src/new.py"], cwd=r,
                   check=True, capture_output=True)
    _commit(r, "rename scoped file")
    problems = stale.check_repo(r)
    assert problems and any("rename.md" in p for p in problems), problems


def test_change_then_revert_after_spec_is_still_stale(tmp_path):
    r = _git_repo(tmp_path)
    (r / "docs" / "plans").mkdir(parents=True)
    plan = r / "docs" / "plans" / "revert.md"
    src = r / "src" / "app.py"; src.parent.mkdir()
    plan.write_text("---\nscope:\n  - src/app.py\n---\n# plan\n", encoding="utf-8")
    src.write_text("x = 1\n", encoding="utf-8")
    _commit(r, "baseline")
    src.write_text("x = 2\n", encoding="utf-8")
    _commit(r, "temporary scoped change")
    src.write_text("x = 1\n", encoding="utf-8")
    _commit(r, "revert scoped change")
    problems = stale.check_repo(r)
    assert problems and any("revert.md" in p for p in problems), problems


def test_merged_side_branch_scoped_change_is_stale(tmp_path):
    r = _git_repo(tmp_path)
    (r / "docs" / "plans").mkdir(parents=True)
    plan = r / "docs" / "plans" / "merge.md"
    src = r / "src" / "app.py"; src.parent.mkdir()
    plan.write_text("---\nscope:\n  - src/app.py\n---\n# plan\n", encoding="utf-8")
    src.write_text("x = 1\n", encoding="utf-8")
    _commit(r, "baseline")
    initial = subprocess.run(
        ["git", "branch", "--show-current"], cwd=r, check=True, capture_output=True,
        text=True, encoding="utf-8", timeout=60,
    ).stdout.strip()
    assert initial
    subprocess.run(["git", "checkout", "-q", "-b", "side"], cwd=r, check=True)
    src.write_text("x = 2\n", encoding="utf-8")
    _commit(r, "side scoped change")
    subprocess.run(["git", "checkout", "-q", initial], cwd=r, check=True)
    (r / "README.md").write_text("main\n", encoding="utf-8")
    _commit(r, "main unrelated")
    subprocess.run(["git", "merge", "--no-ff", "-q", "side", "-m", "merge side"],
                   cwd=r, check=True, capture_output=True)
    problems = stale.check_repo(r)
    assert problems and any("merge.md" in p for p in problems), problems


def test_shallow_cli_exits_nonzero_and_names_history_problem(tmp_path):
    source_parent = tmp_path / "cli-source-parent"; source_parent.mkdir()
    r = _git_repo(source_parent)
    (r / "docs" / "plans").mkdir(parents=True)
    plan = r / "docs" / "plans" / "cli-shallow.md"
    src = r / "src" / "app.py"; src.parent.mkdir()
    plan.write_text("---\nscope:\n  - src/app.py\n---\n# plan\n", encoding="utf-8")
    src.write_text("x = 1\n", encoding="utf-8")
    _commit(r, "baseline")
    (r / "README.md").write_text("tip\n", encoding="utf-8")
    _commit(r, "tip")
    clone = tmp_path / "cli-shallow"
    subprocess.run(["git", "clone", "--depth", "1", "-q", r.as_uri(), str(clone)],
                   check=True, capture_output=True, timeout=60)
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "check-stale-specs.py"),
         "--root", str(clone)], capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=60,
    )
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "shallow" in proc.stdout.lower(), proc.stdout


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

# ── R-FR-004/005 adversarial fold-back integrity ──────────────────────
def _decision_entry(*, ts, summary, files=None, tags=None, session_id="s"):
    return {"ts": ts, "type": "decision", "session_id": session_id,
            "summary": summary, "files": files or [], "tags": tags or []}


def test_foldback_matches_structural_files_without_summary_path(tmp_path):
    plan = tmp_path / "PLAN.md"
    plan.write_text(PLAN, encoding="utf-8")
    ledger = _ledger(tmp_path, [_decision_entry(
        ts=time.time(), summary="changed implementation", files=["src/app.py"])])
    assert fb.foldback(plan, ledger) == 1
    assert "changed implementation" in plan.read_text(encoding="utf-8")


def test_foldback_files_override_misleading_summary(tmp_path):
    plan = tmp_path / "PLAN.md"
    plan.write_text(PLAN, encoding="utf-8")
    ledger = _ledger(tmp_path, [_decision_entry(
        ts=time.time(), summary="mentions src/app.py but did not touch it",
        files=["src/other.py"])])
    assert fb.foldback(plan, ledger) == 0


def test_foldback_normalizes_windows_file_separators(tmp_path):
    plan = tmp_path / "PLAN.md"
    plan.write_text(PLAN, encoding="utf-8")
    ledger = _ledger(tmp_path, [_decision_entry(
        ts=time.time(), summary="windows path", files=[r"src\app.py"])])
    assert fb.foldback(plan, ledger) == 1


def test_foldback_does_not_match_similar_prefix_path(tmp_path):
    plan = tmp_path / "PLAN.md"
    plan.write_text(PLAN, encoding="utf-8")
    ledger = _ledger(tmp_path, [_decision_entry(
        ts=time.time(), summary="backup only", files=["src/app.py.bak"])])
    assert fb.foldback(plan, ledger) == 0


def test_foldback_invalid_structural_file_does_not_fall_back_to_summary(tmp_path):
    plan = tmp_path / "PLAN.md"
    plan.write_text(PLAN, encoding="utf-8")
    unsafe = ".." + "/src/app.py"
    ledger = _ledger(tmp_path, [_decision_entry(
        ts=time.time(), summary="mentions src/app.py", files=[unsafe])])
    assert fb.foldback(plan, ledger) == 0


def test_foldback_legacy_entry_without_files_keeps_compatibility(tmp_path):
    plan = tmp_path / "PLAN.md"
    plan.write_text(PLAN, encoding="utf-8")
    ledger = _ledger(tmp_path, [_decision_entry(
        ts=time.time(), summary="legacy decision for src/app.py", files=[])])
    assert fb.foldback(plan, ledger) == 1


def test_foldback_escapes_untrusted_markdown_and_newlines(tmp_path):
    plan = tmp_path / "PLAN.md"
    plan.write_text(PLAN, encoding="utf-8")
    summary = "safe\n## injected\n[click](https://example.invalid)\n```boom```"
    session = "sess]\n## session-injected"
    ledger = _ledger(tmp_path, [_decision_entry(
        ts=time.time(), summary=summary, files=["src/app.py"], session_id=session)])
    assert fb.foldback(plan, ledger) == 1
    out = plan.read_text(encoding="utf-8")
    assert "\n## injected" not in out
    assert "\n## session-injected" not in out
    assert "\n```boom```" not in out
    assert "[click](https://example.invalid)" not in out
    assert "awiki-foldback:" in out


def test_foldback_same_timestamp_distinct_entries_do_not_collide(tmp_path):
    plan = tmp_path / "PLAN.md"
    plan.write_text(PLAN, encoding="utf-8")
    now = time.time()
    ledger = _ledger(tmp_path, [
        _decision_entry(ts=now, summary="first", files=["src/app.py"], session_id="a"),
        _decision_entry(ts=now, summary="second", files=["src/app.py"], session_id="b"),
    ])
    assert fb.foldback(plan, ledger) == 2
    out = plan.read_text(encoding="utf-8")
    assert out.count("awiki-foldback:") == 2
    assert fb.foldback(plan, ledger) == 0


def test_foldback_respects_legacy_ts_marker(tmp_path):
    now = time.time()
    plan = tmp_path / "PLAN.md"
    plan.write_text(PLAN + f"\n{fb.MARKER}\n\n- old entry (ts={now})\n", encoding="utf-8")
    ledger = _ledger(tmp_path, [_decision_entry(
        ts=now, summary="legacy decision for src/app.py", files=[])])
    assert fb.foldback(plan, ledger) == 0
    assert plan.read_text(encoding="utf-8").count(f"(ts={now})") == 1

