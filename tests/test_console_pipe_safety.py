"""Tier-1 regression — CLI entries must survive non-UTF-8 (cp874) pipes.

Native Thai-Windows sessions give child processes locale cp874 stdout/stderr
pipes. Entries that print status glyphs (✅ U+2705), emoji banners, or Thai
crash with `UnicodeEncodeError: 'charmap' codec ...` and exit with the wrong
code. The repo convention is to reconfigure stdout/stderr to UTF-8 at entry
(same idiom as scripts/hooks_runner.py and scripts/a_escalate.py); every
test parent already decodes child output as UTF-8.

These tests force `PYTHONIOENCODING=cp874` (+ `PYTHONUTF8=0`, because UTF-8
mode would ignore it) in the child so the historical crash reproduces
deterministically on ANY machine/locale — including UTF-8 CI — then assert
the documented contract: expected exit code and UTF-8-decodable output.

Baseline evidence (WO-PORTABILITY-BASELINE-20260902 PB-0, 2026-09-02):
13 nodeids failed exactly this way under the no-override native run.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# Simulate the native Thai-Windows pipe on any machine. PYTHONUTF8=0 is
# required: with system PYTHONUTF8=1 the io encoding override is ignored.
CP874_ENV = {**os.environ, "PYTHONIOENCODING": "cp874", "PYTHONUTF8": "0"}

GOOD_PR_BODY = """## Summary
fix the thing

## Loop-Evidence
- WO: WO-LANES-20260824 / finding R-FR-008
- Tested: python -m pytest tests/test_x.py -q (12 passed)
- Root cause: seam mismatch; fix + regression test added
"""


def _run(cmd: list[str], *, stdin: str | None = None,
         timeout: int = 180) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd, input=stdin, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
        env=CP874_ENV, cwd=str(REPO_ROOT), timeout=timeout)


def test_conductor_status_survives_cp874_pipe():
    r = _run([sys.executable, "-m", "conductor", "status", "--json"],
             timeout=240)
    assert r.returncode == 0, r.stderr[-300:]
    json.loads(r.stdout)  # stdout must stay valid JSON through the pipe


def test_awiki_guide_survives_cp874_pipe():
    r = _run([sys.executable, "scripts/awiki-guide.py"], timeout=60)
    assert r.returncode == 0, r.stderr[-300:]
    # Thai text must round-trip: proves UTF-8 bytes, not mojibake/question marks
    assert "30 วินาที" in r.stdout


def test_awiki_doctor_survives_cp874_pipe():
    """Doctor must get past its banner and print sections (no rc assert:
    findings depend on the checkout, crashes do not)."""
    r = _run([sys.executable, "scripts/awiki-doctor.py"], timeout=600)
    for sec in ("registry", "hooks", "mcp"):
        assert sec in r.stdout, f"doctor missing section {sec}: {r.stderr[-200:]}"


def test_check_pr_loop_survives_cp874_pipe():
    payload = json.dumps({"body": GOOD_PR_BODY, "files": ["a.py", "tests/test_a.py"]})
    r = _run([sys.executable, "scripts/check_pr_loop.py"], stdin=payload, timeout=60)
    assert r.returncode == 0, r.stderr[-300:]


def test_check_machine_path_verdict_survives_cp874_pipe():
    """The BLOCK path prints the deny reason; under cp874 it used to crash
    with rc 1 before reaching the rc 2 verdict."""
    payload = json.dumps({
        "tool_name": "Write",
        "tool_input": {
            "file_path": "scripts/foo.py",
            "content": 'HOME_DIR = "/home/you/"',  # example
        },
    })
    r = _run([sys.executable, "scripts/hooks/check_machine_path.py"],
             stdin=payload, timeout=60)
    assert r.returncode == 2, r.stderr[-300:]


def test_check_graph_yaml_survives_cp874_pipe():
    r = _run([sys.executable, "scripts/check-graph-yaml.py"], timeout=120)
    assert r.returncode == 0, r.stdout[-200:] + r.stderr[-200:]


def test_verify_regression_survives_cp874_pipe():
    pytest.importorskip("pandas", reason="rabies regression needs the domain stack")
    pytest.importorskip("openpyxl", reason="rabies regression HN workbook needs openpyxl")
    r = _run([sys.executable, "scripts/hospital/verify_regression.py"], timeout=120)
    assert r.returncode == 0, r.stderr[-300:]


@pytest.mark.parametrize("relative_path", [
    "scripts/awiki-doctor.py",
    "scripts/awiki-guide.py",
    "scripts/check-graph-yaml.py",
    "scripts/check_pr_loop.py",
    "scripts/hooks/check_machine_path.py",
    "scripts/hospital/verify_regression.py",
])
def test_import_does_not_reconfigure_host_stdio(relative_path: str):
    """Importing a CLI module must not mutate the embedding process streams.

    The cp874 repair belongs to CLI execution only. Some of these files are
    imported with importlib by tests/tools, so module import must preserve the
    caller's stdout/stderr encoding.
    """
    # The hospital verifier intentionally has optional domain dependencies
    # (pandas / PyYAML / classify_rabies) that core CI does not install.  Stub
    # only those imports in this subprocess: the contract under test is module
    # import preserving host stdio, not availability of the hospital stack.
    optional_stubs = ""
    if relative_path == "scripts/hospital/verify_regression.py":
        optional_stubs = (
            "import types; "
            "sys.modules['pandas']=types.ModuleType('pandas'); "
            "sys.modules['yaml']=types.ModuleType('yaml'); "
            "cr=types.ModuleType('classify_rabies'); "
            "cr.VAC_IM='IM'; cr.VAC_ID='ID'; cr.VAC_ERIG='ERIG'; cr.VAC_HRIG='HRIG'; "
            "sys.modules['classify_rabies']=cr; "
        )
    probe = (
        "import runpy,sys; "
        + optional_stubs
        + "before=sys.stdout.encoding; "
        "runpy.run_path(sys.argv[1], run_name='awiki_import_probe'); "
        "after=sys.stdout.encoding; "
        "raise SystemExit(0 if before == after else 9)"
    )
    env = {**os.environ, "PYTHONIOENCODING": "cp874", "PYTHONUTF8": "0"}
    r = subprocess.run(
        [sys.executable, "-c", probe, str(REPO_ROOT / relative_path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(REPO_ROOT), timeout=120,
    )
    assert r.returncode == 0, (
        f"import mutated host stdio for {relative_path}: rc={r.returncode}; "
        f"stderr={r.stderr[-300:]}"
    )
