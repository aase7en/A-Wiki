"""
test_pre_commit_syntax_gate.py — commit-time Python syntax gate.

Root cause class (observed 2026-07-26 → fixed 2026-07-27): commit 307b3215
("chunk(a-claim): Iron Law #11") wrote two f-strings in
scripts/hooks/session_start.py with a LITERAL newline where `\\n` was meant.
The pre-commit gate printed "✅ AWiki safety gate passed" and let it through.

Two effects, one of them silent-by-design:
1. SessionStart hook crashed every session — its output just never appeared.
2. `pytest tests/` aborted at COLLECTION ("Interrupted: 2 errors during
   collection") because test_lean_session_start.py and
   test_model_intel_and_skillopt.py exec_module that file at import. The ENTIRE
   suite ran zero tests while looking like an infrastructure error rather than
   a failure list.

Effect 2 is why this gate exists at commit time. tests/test_hooks_subprocess_
encoding.py ALREADY ast.parses every scripts/hooks/*.py — it would have caught
this — but a suite that cannot collect cannot catch anything. The same check
has to run at a point that does not depend on the suite being runnable.

Covered here:
- the exact 307b3215 shape blocks, with file:line and the compiler message
- the gate reads the STAGED blob, not the working tree
- clean / non-Python / deleted-file staged states do not block
- HOOK_SKIP=check_staged_syntax bypasses (Layer-2 override convention)
- end-to-end through scripts/hooks/pre-commit-awiki.sh
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CHECKER = REPO_ROOT / "scripts" / "check-staged-syntax.py"
GATE = REPO_ROOT / "scripts" / "hooks" / "pre-commit-awiki.sh"

# The 307b3215 shape: a literal newline inside a single-quoted f-string.
# Line 3 is the offender.
BROKEN_FSTRING = (
    'import sys\n'
    'def emit():\n'
    '    sys.stderr.write(f"see `claim_list`:\n'
    '")\n'
)
CLEAN_FSTRING = (
    'import sys\n'
    'def emit():\n'
    '    sys.stderr.write(f"see `claim_list`:\\n")\n'
)


# ── helpers ─────────────────────────────────────────────────────────────

def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=str(repo), capture_output=True,
        text=True, encoding="utf-8", errors="replace", check=True,
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """Temp repo with one commit — staging area starts empty."""
    r = tmp_path / "wiki"
    r.mkdir()
    _git(r, "init", "-q")
    _git(r, "config", "user.email", "test@a-wiki.local")
    _git(r, "config", "user.name", "Test Runner")
    (r / "README.md").write_text("# t\n", encoding="utf-8")
    _git(r, "add", "README.md")
    _git(r, "commit", "-q", "-m", "init")
    return r


def _run_checker(repo: Path, **env_extra: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    env.pop("HOOK_SKIP", None)
    env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(CHECKER), "--staged"],
        cwd=str(repo), capture_output=True,
        text=True, encoding="utf-8", errors="replace", env=env,
    )


def _stage(repo: Path, name: str, content: str) -> None:
    (repo / name).write_text(content, encoding="utf-8")
    _git(repo, "add", name)


# ── unit: the checker ───────────────────────────────────────────────────

class TestStagedSyntaxChecker:

    def test_literal_newline_fstring_blocks(self, repo):
        """The 307b3215 regression itself."""
        _stage(repo, "session_start.py", BROKEN_FSTRING)
        res = _run_checker(repo)
        out = res.stdout + res.stderr
        assert res.returncode == 1, f"expected block, got rc={res.returncode}: {out!r}"
        assert "session_start.py" in out, f"finding must name the file: {out!r}"
        assert ":3" in out, f"finding must carry the line number (3): {out!r}"
        assert "unterminated" in out.lower(), (
            f"finding must carry the compiler message: {out!r}"
        )

    def test_clean_python_passes(self, repo):
        _stage(repo, "session_start.py", CLEAN_FSTRING)
        res = _run_checker(repo)
        assert res.returncode == 0, f"clean file must pass: {res.stdout + res.stderr!r}"
        assert res.stdout.strip() == ""

    def test_reads_index_not_worktree(self, repo):
        """Staged broken + fixed on disk (unstaged) must STILL block.

        This is what makes the gate honest: git commits the index, so the
        index is what has to compile.
        """
        _stage(repo, "session_start.py", BROKEN_FSTRING)
        (repo / "session_start.py").write_text(CLEAN_FSTRING, encoding="utf-8")  # not staged
        res = _run_checker(repo)
        assert res.returncode == 1, (
            "gate compiled the working tree instead of the staged blob — a broken "
            "file would sail into the commit"
        )

    def test_broken_worktree_but_clean_index_passes(self, repo):
        """Inverse: mid-edit garbage on disk must not block an unrelated commit."""
        _stage(repo, "session_start.py", CLEAN_FSTRING)
        (repo / "session_start.py").write_text(BROKEN_FSTRING, encoding="utf-8")  # not staged
        res = _run_checker(repo)
        assert res.returncode == 0, (
            f"unstaged worktree edits must not block: {res.stdout + res.stderr!r}"
        )

    def test_non_python_ignored(self, repo):
        _stage(repo, "notes.md", "```python\ndef broken(:\n```\n")
        res = _run_checker(repo)
        assert res.returncode == 0
        assert res.stdout.strip() == ""

    def test_deleted_python_ignored(self, repo):
        _stage(repo, "gone.py", CLEAN_FSTRING)
        _git(repo, "commit", "-q", "-m", "add")
        _git(repo, "rm", "-q", "gone.py")
        res = _run_checker(repo)
        assert res.returncode == 0, (
            f"a staged deletion has no blob to compile: {res.stdout + res.stderr!r}"
        )

    def test_empty_index_passes(self, repo):
        res = _run_checker(repo)
        assert res.returncode == 0
        assert res.stdout.strip() == ""

    def test_reports_every_broken_file(self, repo):
        _stage(repo, "a.py", BROKEN_FSTRING)
        _stage(repo, "b.py", "def f(:\n")
        _stage(repo, "ok.py", CLEAN_FSTRING)
        res = _run_checker(repo)
        assert res.returncode == 1
        assert "a.py" in res.stdout and "b.py" in res.stdout
        assert "ok.py" not in res.stdout

    def test_hook_skip_bypasses(self, repo):
        _stage(repo, "session_start.py", BROKEN_FSTRING)
        res = _run_checker(repo, HOOK_SKIP="check_staged_syntax")
        assert res.returncode == 0, "HOOK_SKIP=check_staged_syntax must bypass"

    def test_hook_skip_other_hook_does_not_bypass(self, repo):
        _stage(repo, "session_start.py", BROKEN_FSTRING)
        res = _run_checker(repo, HOOK_SKIP="check_cost_tier,check_apikey")
        assert res.returncode == 1, "an unrelated HOOK_SKIP token must not disarm this gate"

    def test_noop_without_staged_flag(self, repo):
        """No args = silent no-op, so the file is inert if it is ever run as a
        PreToolUse hook or imported."""
        res = subprocess.run(
            [sys.executable, str(CHECKER)], cwd=str(repo), capture_output=True,
            text=True, encoding="utf-8", errors="replace",
        )
        assert res.returncode == 0
        assert res.stderr.strip() == ""

    def test_initial_commit_has_no_head(self, tmp_path):
        """A repo with zero commits still gets checked, and does not error out.

        `git diff --cached` falls back to the empty tree when HEAD is missing;
        a refactor to `git diff-index HEAD` would silently break the very first
        commit (rc=2, everything blocked).
        """
        fresh = tmp_path / "fresh"
        fresh.mkdir()
        _git(fresh, "init", "-q")
        _stage(fresh, "a.py", BROKEN_FSTRING)
        res = _run_checker(fresh)
        assert res.returncode == 1, f"{res.stdout + res.stderr!r}"
        assert "a.py:3" in res.stdout

    def test_outside_git_repo_does_not_block(self, tmp_path):
        """Fail-soft when there is no index at all (no repo → nothing staged)."""
        plain = tmp_path / "not-a-repo"
        plain.mkdir()
        res = _run_checker(plain)
        assert res.returncode == 0, f"{res.stdout + res.stderr!r}"


# ── end-to-end: the pre-commit gate ─────────────────────────────────────

GATE_FILES = [
    Path("scripts/hooks/pre-commit-awiki.sh"),
    Path("scripts/hooks/pre_commit_skill_surfaces.sh"),
    Path("scripts/hooks/_scan_staged_diff.py"),
    Path("scripts/hooks/security_patterns.yaml"),
    Path("scripts/check-staged-syntax.py"),
]


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash unavailable")
class TestPreCommitGateEndToEnd:
    """Run the real gate script in a temp repo carrying the real checks."""

    def _install(self, repo: Path) -> None:
        for rel in GATE_FILES:
            src = REPO_ROOT / rel
            if not src.exists():
                pytest.fail(f"gate component missing: {rel}")
            dst = repo / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    def _run_gate(self, repo: Path) -> subprocess.CompletedProcess:
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        env.pop("HOOK_SKIP", None)
        env.pop("PRE_COMMIT_SKIP_AWIKI", None)
        return subprocess.run(
            ["bash", "scripts/hooks/pre-commit-awiki.sh"],
            cwd=str(repo), capture_output=True,
            text=True, encoding="utf-8", errors="replace", env=env,
        )

    def test_gate_blocks_broken_staged_python(self, repo):
        self._install(repo)
        _stage(repo, "session_start.py", BROKEN_FSTRING)
        res = self._run_gate(repo)
        out = res.stdout + res.stderr
        assert res.returncode != 0, f"gate passed a SyntaxError: {out!r}"
        assert "session_start.py" in out and ":3" in out, out
        assert "safety gate passed" not in out, "gate must not claim success"

    def test_gate_passes_clean_staged_python(self, repo):
        self._install(repo)
        _stage(repo, "session_start.py", CLEAN_FSTRING)
        res = self._run_gate(repo)
        out = res.stdout + res.stderr
        assert res.returncode == 0, f"clean commit blocked: {out!r}"
        assert "safety gate passed" in out, out

    def test_gate_override_still_works(self, repo):
        self._install(repo)
        _stage(repo, "session_start.py", BROKEN_FSTRING)
        env = {**os.environ, "PRE_COMMIT_SKIP_AWIKI": "1"}
        res = subprocess.run(
            ["bash", "scripts/hooks/pre-commit-awiki.sh"],
            cwd=str(repo), capture_output=True,
            text=True, encoding="utf-8", errors="replace", env=env,
        )
        assert res.returncode == 0, "emergency override must still bypass everything"
