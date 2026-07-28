"""Guard: pre-commit gates must not invoke a bare `python`.

Root cause this encodes (found 2026-07-28 on macOS):

  scripts/hooks/pre_commit_skill_surfaces.sh:28 ran `python ... --check`.
  macOS ships no `python`, only `python3`, so the command failed with
  "command not found" -> non-zero exit -> the gate reported "surfaces have
  drifted" on every commit touching a SKILL.md, while
  `python3 scripts/regen-skill-surfaces.py --check` reported no drift.

  scripts/hooks/pre-commit-awiki.sh:48 had the same bare `python`, but piped
  through `2>/dev/null || true`. There the failure was silent: SCAN_RESULT came
  back empty, which the gate reads as "no security finding". The staged-diff
  secret / machine-path scan had therefore been passing without scanning
  anything at all.

The second failure mode is why this is a test and not a one-line fix: a gate
that cannot run must fail LOUDLY, never silently succeed.

Note: the planted-secret fixture below is assembled at runtime from fragments
on purpose. A literal token in this file would (correctly) be blocked by the
check_secret_leak hook.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# Shell gates that run on every commit. If a script here cannot start its
# interpreter, a guardrail is silently off.
GATE_SCRIPTS = [
    REPO_ROOT / "scripts" / "hooks" / "pre-commit-awiki.sh",
    REPO_ROOT / "scripts" / "hooks" / "pre_commit_skill_surfaces.sh",
]

# `python` as a command, not `python3`, not `python_foo`, not a bare word
# inside prose. Command position = start of line, or after a pipe / `$(` /
# `!` / `&&` / `||` / `;`.
BARE_PYTHON = re.compile(r"(?:^|[|(;&!]|\$\()\s*python(?![\w.-])")


def _executable_lines(path: Path) -> list[tuple[int, str]]:
    """Lines that can run a command — comments and echo/printf text excluded.

    The `Fix: python ...` hint strings are user-facing prose, not invocations;
    they are checked separately by test_hint_strings_use_python3.
    """
    out = []
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if re.match(r"^(echo|printf)\b", line):
            continue
        out.append((n, raw))
    return out


@pytest.mark.parametrize("script", GATE_SCRIPTS, ids=lambda p: p.name)
def test_gate_scripts_never_invoke_bare_python(script: Path) -> None:
    """A gate must not depend on `python` existing — macOS only has python3."""
    assert script.is_file(), f"missing gate script: {script}"
    offenders = [
        f"{script.name}:{n}: {text.strip()}"
        for n, text in _executable_lines(script)
        if BARE_PYTHON.search(text)
    ]
    assert not offenders, (
        "Gate invokes a bare `python`, which does not exist on macOS:\n  "
        + "\n  ".join(offenders)
        + "\nUse the python3-first resolver (see scripts/new-skill.sh)."
    )


@pytest.mark.parametrize("script", GATE_SCRIPTS, ids=lambda p: p.name)
def test_hint_strings_use_python3(script: Path) -> None:
    """`Fix: python ...` hints must name a command the user can actually run."""
    bad = [
        f"{script.name}:{n}: {raw.strip()}"
        for n, raw in enumerate(script.read_text(encoding="utf-8").splitlines(), 1)
        if re.search(r"Fix:\s*python(?!3)", raw)
    ]
    assert not bad, "Hint tells the user to run a command macOS lacks:\n  " + "\n  ".join(bad)


def test_secret_scan_failure_is_loud_not_silent() -> None:
    """The staged-diff scanner must never be `2>/dev/null || true`.

    That combination turns an interpreter/scanner crash into an empty
    SCAN_RESULT, which the gate reads as 'clean'. Fail-closed, not fail-open.
    """
    text = (REPO_ROOT / "scripts" / "hooks" / "pre-commit-awiki.sh").read_text(encoding="utf-8")
    # Executable lines only — a comment may legitimately quote the old broken
    # form to explain why it was replaced.
    scan_lines = [
        ln
        for ln in text.splitlines()
        if "_scan_staged_diff.py" in ln and not ln.strip().startswith("#")
    ]
    assert scan_lines, "expected pre-commit-awiki.sh to invoke _scan_staged_diff.py"
    for ln in scan_lines:
        assert "|| true" not in ln, (
            "scanner failure is swallowed by `|| true` — a crash would read as "
            f"'no findings':\n  {ln.strip()}"
        )
        assert "2>/dev/null" not in ln, (
            "scanner stderr is discarded, hiding why it failed:\n  " + ln.strip()
        )


def test_scanner_actually_flags_a_planted_secret() -> None:
    """End-to-end: the scanner really does detect something, via python3.

    Guards against the inverse bug — a gate that runs fine but scans nothing.
    Fragments are concatenated at runtime so this file holds no literal token.
    """
    scanner = REPO_ROOT / "scripts" / "hooks" / "_scan_staged_diff.py"
    assert scanner.is_file(), f"missing scanner: {scanner}"

    fake_gh_token = "ghp" + "_" + ("0123456789abcdef" * 2) + "0123"
    planted = (
        "diff --git a/x.py b/x.py\n"
        "--- a/x.py\n"
        "+++ b/x.py\n"
        f'+token = "{fake_gh_token}"\n'
    )
    proc = subprocess.run(
        ["python3", str(scanner)],
        input=planted,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert proc.returncode == 0, f"scanner crashed: {proc.stderr}"
    assert proc.stdout.strip(), (
        "scanner reported nothing for a diff containing an obvious GitHub "
        "token — it is not actually scanning."
    )
