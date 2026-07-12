"""
test_hooks_subprocess_encoding.py — cp874 subprocess regression guard.

Root cause class (recurring on Thai Windows, cp874 console): any
`subprocess.run(..., text=True)` WITHOUT an explicit `encoding=` decodes
child output with the locale codec. Git output containing UTF-8 bytes
outside cp874 (em-dash in a commit subject, Thai text, emoji) then raises
UnicodeDecodeError inside the reader thread → the caller's `except` swallows
it → hooks silently misbehave (e.g. check_delegation_gate saw
"Last commit: (none)" and blocked a perfectly valid
`chunk(...): ... [next: ...]` push on 2026-07-12).

Two layers:
1. AST lint over scripts/hooks/*.py + scripts/hooks_runner.py — every
   text-mode subprocess call must pin `encoding=` (the established repo
   pattern is `encoding="utf-8", errors="replace"`).
2. Functional proof for the observed failure: a commit subject with an
   em-dash must survive get_most_recent_commit_message() regardless of the
   console codec.
"""
from __future__ import annotations

import ast
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = REPO_ROOT / "scripts" / "hooks"

SUBPROCESS_FUNCS = {"run", "check_output", "check_call", "call", "Popen"}

LINTED_FILES = sorted(HOOKS_DIR.glob("*.py")) + [REPO_ROOT / "scripts" / "hooks_runner.py"]


def _text_mode_calls_missing_encoding(path: Path) -> list[int]:
    """Line numbers of subprocess calls that set text/universal_newlines
    truthy but omit encoding=."""
    tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    offenders: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
        if name not in SUBPROCESS_FUNCS:
            continue
        kwargs = {kw.arg for kw in node.keywords if kw.arg}
        wants_text = any(
            kw.arg in ("text", "universal_newlines")
            and isinstance(kw.value, ast.Constant)
            and bool(kw.value.value)
            for kw in node.keywords
        )
        if wants_text and "encoding" not in kwargs:
            offenders.append(node.lineno)
    return offenders


@pytest.mark.parametrize("path", LINTED_FILES, ids=lambda p: p.name)
def test_text_mode_subprocess_pins_encoding(path):
    offenders = _text_mode_calls_missing_encoding(path)
    assert offenders == [], (
        f"{path.relative_to(REPO_ROOT)}: subprocess call(s) at line(s) {offenders} "
        'use text=True without encoding= — on Thai Windows (cp874) this '
        "UnicodeDecodeErrors on git output containing em-dash/Thai/emoji. "
        'Add encoding="utf-8", errors="replace".'
    )


class TestDelegationGateEmDashCommit:
    """The observed 2026-07-12 failure: chunk(...) subject with an em-dash."""

    def _load_gate(self):
        spec = importlib.util.spec_from_file_location(
            "check_delegation_gate_enc_mod", HOOKS_DIR / "check_delegation_gate.py"
        )
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        return mod

    def test_em_dash_commit_subject_survives(self, tmp_path, monkeypatch):
        subject = "chunk(enc-test): fix — em-dash survives [next: none]"
        env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
        for cmd in (
            ["git", "init", "-q"],
            ["git", "add", "-A"],
        ):
            subprocess.run(cmd, cwd=tmp_path, check=True, capture_output=True)
        (tmp_path / "f.txt").write_text("x", encoding="utf-8")
        subprocess.run(["git", "add", "f.txt"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", subject],
            cwd=tmp_path, check=True, capture_output=True,
            env={**__import__("os").environ, **env},
        )

        gate = self._load_gate()
        monkeypatch.setattr(gate, "REPO_ROOT", tmp_path)
        msg = gate.get_most_recent_commit_message()
        assert "em-dash survives" in msg, (
            f"commit subject lost (got {msg!r}) — decode failure swallowed by except"
        )
        assert gate.ALLOWED_PUSH_PATTERN.search(msg), "chunk(...) pattern must match"
