"""tests/test_check_hexagonal_boundary.py — ADR-0012 C6 prototype test + FP measure.

Two jobs:
  1. Unit-test the hook's logic (block / pass / fail-open paths).
  2. Measure the false-positive rate against the real ports/ files in the
     repo. This is the number revisit condition C6 demands: 'static-detect
     with <20% false-positive in 30 days'. We assert the rate is 0% on the
     known-good ports we just wrote — if a future edit breaks a port, the
     hook fires for the right reason (true positive), not a false alarm.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "hooks" / "check_hexagonal_boundary.py"

# Load hook as a module (filename has dashes-safe here, but use spec for parity)
_spec = importlib.util.spec_from_file_location("chk_hex", HOOK)
chk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(chk)


def _run_hook_via_main(payload: dict) -> int:
    """Invoke main() in-process by feeding stdin via a temporary redirect."""
    import io
    old_stdin = sys.stdin
    sys.stdin = io.StringIO(json.dumps(payload))
    try:
        return chk.main()
    finally:
        sys.stdin = old_stdin


# ── 1. Scope filtering ──────────────────────────────────────────────────
def test_ignores_non_gate_tool():
    assert _run_hook_via_main({"tool_name": "Read", "tool_input": {"file_path": "scripts/lib/ports/x.py"}}) == 0


def test_ignores_file_outside_ports_dir():
    # scripts/lib/neural_spine_mcp.py is NOT in ports/ — must not be checked
    assert _run_hook_via_main({
        "tool_name": "Write",
        "tool_input": {"file_path": "scripts/lib/neural_spine_mcp.py", "content": "import sqlite3"},
    }) == 0


def test_ignores_empty_file_path():
    assert _run_hook_via_main({"tool_name": "Write", "tool_input": {}}) == 0


def test_respects_hook_skip_env(monkeypatch):
    monkeypatch.setenv("HOOK_SKIP", "check_hexagonal_boundary")
    # returns 0 and emits a bypass message
    assert _run_hook_via_main({
        "tool_name": "Write",
        "tool_input": {"file_path": "scripts/lib/ports/x.py", "content": "import sqlite3"},
    }) == 0


# ── 2. True positives: a port importing 'outside' MUST be blocked ───────
@pytest.mark.parametrize("bad_import", [
    "import sqlite3",
    "import adapters.memory",
    "from adapters.memory import JsonlMemoryAdapter",
    "import subprocess",
    "import requests",
    "from fastapi import FastAPI",
])
def test_blocks_port_that_imports_outside(bad_import):
    rc = _run_hook_via_main({
        "tool_name": "Write",
        "tool_input": {
            "file_path": "scripts/lib/ports/example.py",
            "content": bad_import,
        },
    })
    assert rc == 2, f"expected block for: {bad_import}"


# ── 3. True negatives: a clean port MUST pass ───────────────────────────
def test_passes_clean_port():
    clean = (
        "from __future__ import annotations\n"
        "from typing import Protocol\n\n"
        "class MemoryPort(Protocol):\n"
        "    def recall(self, query: str) -> list[dict]: ...\n"
    )
    assert _run_hook_via_main({
        "tool_name": "Write",
        "tool_input": {
            "file_path": "scripts/lib/ports/memory.py",
            "content": clean,
        },
    }) == 0


def test_passes_port_that_imports_only_stdlib_typing():
    clean = "from typing import Protocol, runtime_checkable\nimport time\n"
    # `time` is stdlib, NOT in FORBIDDEN_IN_PORTS — must pass
    assert _run_hook_via_main({
        "tool_name": "Write",
        "tool_input": {"file_path": "x/ports/y.py", "content": clean},
    }) == 0


# ── 4. Fail-open paths ──────────────────────────────────────────────────
def test_syntax_error_fails_open():
    # An unparseable file must NOT block — fail open so a half-typed edit
    # doesn't wedge the repo.
    rc = _run_hook_via_main({
        "tool_name": "Write",
        "tool_input": {
            "file_path": "scripts/lib/ports/broken.py",
            "content": "def f(:\n",  # syntax error
        },
    })
    assert rc == 0


def test_malformed_stdin_fails_open():
    import io
    old_stdin = sys.stdin
    sys.stdin = io.StringIO("not json")
    try:
        assert chk.main() == 0
    finally:
        sys.stdin = old_stdin


# ── 5. FALSE-POSITIVE MEASUREMENT (ADR-0012 revisit condition C6) ───────
# The decisive test. We scan every real ports/*.py in the repo and confirm
# the hook blocks NONE of them — they are all clean by construction. If this
# ever fails, either a port is genuinely broken (true positive) or the hook
# is over-firing (false positive). Either way it is actionable signal.
def test_false_positive_rate_on_real_ports_is_zero():
    ports_dir = REPO_ROOT / "scripts" / "lib" / "ports"
    port_files = list(ports_dir.rglob("*.py"))
    assert port_files, "expected at least one ports/ file (slice A4 created one)"

    false_positives = []
    for pf in port_files:
        source = pf.read_text(encoding="utf-8", errors="replace")
        try:
            imported = chk._imported_names(source)
        except SyntaxError:
            continue  # fail-open, not a FP
        violations = imported & chk.FORBIDDEN_IN_PORTS
        if violations:
            false_positives.append((pf, violations))

    fp_rate = len(false_positives) / len(port_files)
    # C6 threshold is <20%. We assert the much stronger 0% because every
    # port in the repo today was written to the rule. If migration introduces
    # a port that legitimately needs an exception, add it to an allowlist
    # rather than loosening this assertion.
    assert fp_rate == 0.0, (
        f"false-positive on real ports: {false_positives} "
        f"(rate {fp_rate:.0%} of {len(port_files)} files)"
    )


# ── 6. End-to-end via subprocess (proves the runner can invoke it) ──────
def test_subprocess_invocation_blocks_violation(tmp_path):
    """The hook must behave identically when run as `python check_hexagonal_boundary.py`."""
    payload = {
        "tool_name": "Write",
        "tool_input": {
            "file_path": "scripts/lib/ports/x.py",
            "content": "import sqlite3",
        },
    }
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload), capture_output=True, text=True, encoding="utf-8",
    )
    assert result.returncode == 2, f"expected block, got rc={result.returncode}, stderr={result.stderr}"
    assert "HEXAGONAL BOUNDARY VIOLATION" in result.stderr
