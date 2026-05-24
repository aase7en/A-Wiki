"""
Shared fixtures for A-Wiki test suites.

Provides temporary git repos, environment sanitization,
and helper factories for all 3 test modules.
"""

from __future__ import annotations
import os
import sys
import subprocess
from pathlib import Path
from typing import Generator, Any

import pytest

# ── repo root ──────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "wiki"))


# ── Helpers ────────────────────────────────────────────────────────────

def _git(*args: str, cwd: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        capture_output=True, text=True,
        cwd=cwd,
    )


def init_temp_repo(path: Path) -> None:
    """Initialise a bare-bones git repo at *path* with one commit."""
    path.mkdir(parents=True, exist_ok=True)
    _git("init", cwd=str(path))
    _git("config", "user.email", "test@a-wiki.local", cwd=str(path))
    _git("config", "user.name", "Test Runner", cwd=str(path))
    readme = path / "README.md"
    readme.write_text("# Test Repo\n", encoding="utf-8")
    _git("add", "README.md", cwd=str(path))
    _git("commit", "-m", "init", cwd=str(path))


# ── Fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def tmp_git_repo(tmp_path: Path) -> Generator[Path, None, None]:
    """A temporary git repo with initial commit."""
    repo = tmp_path / "wiki"
    init_temp_repo(repo)
    yield repo


@pytest.fixture
def repos_two_device(tmp_path: Path) -> Generator[tuple[Path, Path], None, None]:
    """Two independent git repos simulating Device-A and Device-B.

    Both share the same initial state (single commit).
    """
    a = tmp_path / "device_a"
    b = tmp_path / "device_b"
    init_temp_repo(a)
    _git("clone", str(a), str(b), cwd=str(tmp_path))
    yield a, b


@pytest.fixture
def monkeypatch_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sanitize environment for reproducible tests."""
    for key in ("WIKI_DEVICE_NAME", "HOOK_SKIP", "HOOK_TIMEOUT",
                "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY"):
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def sample_sync_paths() -> list[str]:
    """The default SYNC_PATHS from sync.py (as strings)."""
    return [
        "wiki", "log.md", "session-memory.md", "index.md",
        "index-ai.md", "index-env.md", "index-iot.md", "index-it.md",
        "index-pharmacy.md", "CLAUDE.md", "GEMINI.md", "AGENTS.md",
        "brain-map.canvas",
    ]


@pytest.fixture
def hook_input() -> dict[str, Any]:
    """Standard hook input JSON payload."""
    return {
        "message": {
            "role": "user",
            "content": "Make a change to the wiki"
        },
        "session": {
            "device": "test-device",
            "id": "test-session-001"
        },
        "paths": {
            "wiki": "ok",
            "log.md": "ok",
            "CLAUDE.md": "ok"
        }
    }