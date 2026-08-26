"""check_pr_loop — Universal Loop Contract gate (CI-enforced).

Every PR to main must carry Loop-Evidence (the loop-engineer trail:
WO/finding id + what was tested); PRs touching production code must
also touch tests (Iron Law #1 lifted to PR level). Docs-only PRs pass
on evidence alone. This is THE vendor-neutral enforcement point: any
agent (GLM/GPT/Claude/Codex/...) goes through the same CI.
"""
from __future__ import annotations

import importlib.util as ilu
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
_spec = ilu.spec_from_file_location("cpl", REPO_ROOT / "scripts" / "check_pr_loop.py")
cpl = ilu.module_from_spec(_spec)
_spec.loader.exec_module(cpl)


GOOD_BODY = """## Summary
fix the thing

## Loop-Evidence
- WO: WO-LANES-20260824 / finding R-FR-008
- Tested: python -m pytest tests/test_x.py -q (12 passed)
- Root cause: seam mismatch; fix + regression test added
"""


def test_pr_with_loop_evidence_and_tests_passes():
    ok, reasons = cpl.check_pr(GOOD_BODY, ["scripts/lib/x.py", "tests/test_x.py"])
    assert ok, reasons


def test_missing_loop_evidence_section_fails():
    ok, reasons = cpl.check_pr("## Summary\njust a fix\n", ["README.md"])
    assert not ok and any("Loop-Evidence" in r for r in reasons)


def test_evidence_without_any_reference_fails():
    body = "## Loop-Evidence\n- did some work\n"
    ok, reasons = cpl.check_pr(body, ["docs/x.md"])
    assert not ok and any("WO/finding" in r or "reference" in r.lower()
                          for r in reasons)


def test_production_code_without_tests_fails():
    ok, reasons = cpl.check_pr(GOOD_BODY, ["scripts/lib/x.py", "docs/n.md"])
    assert not ok and any("test" in r.lower() for r in reasons)


def test_docs_only_with_evidence_passes():
    ok, reasons = cpl.check_pr(GOOD_BODY, ["docs/getting-started.md",
                                            "wiki/concepts/x.md"])
    assert ok, reasons


def test_test_only_changes_pass_without_prod_tests_rule():
    ok, reasons = cpl.check_pr(GOOD_BODY, ["tests/test_new.py"])
    assert ok, reasons


def test_empty_body_fails_with_clear_reason():
    ok, reasons = cpl.check_pr("", ["scripts/lib/x.py"])
    assert not ok and reasons


def test_cli_reads_json_payload_and_exits():
    import json, subprocess
    payload = {"body": GOOD_BODY, "files": ["a.py", "tests/test_a.py"]}
    res = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "check_pr_loop.py")],
        input=json.dumps(payload), capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=60)
    assert res.returncode == 0, res.stderr[-200:]
    bad = {"body": "no evidence", "files": ["a.py", "tests/t.py"]}
    res2 = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "check_pr_loop.py")],
        input=json.dumps(bad), capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=60)
    assert res2.returncode == 1


def test_gate_workflow_checks_out_merge_ref_not_head():
    """Regression 2026-08-26 (PR #26 incident): pinning the checkout to
    head.sha made the gate exit 2 (checker file not found) on any branch
    cut before scripts/check_pr_loop.py landed. The merge ref (the default
    checkout) carries main's checker and a PR's own edits to it, so the
    dogfood property survives without breaking pre-checker branches."""
    import re
    yaml_text = (REPO_ROOT / ".github" / "workflows" / "pr-loop-gate.yml"
                 ).read_text(encoding="utf-8")
    assert "scripts/check_pr_loop.py" in yaml_text
    ref_pins = re.findall(r"^\s*ref:\s*\S.*$", yaml_text, flags=re.M)
    assert not any("head.sha" in pin for pin in ref_pins), (
        "pr-loop-gate must run the checker from the merge ref (default "
        "checkout); a head.sha ref pin breaks branches predating the checker")
