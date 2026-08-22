"""`awiki` pip-package CLI — one-command access to the brain.

Contract (user promise: "pip install awiki → ใช้ได้เลย"):
1. Finds the A-Wiki repo root via AWIKI_ROOT env, or by walking up from
   cwd looking for the repo markers (AGENTS.md + skills-registry.json).
2. Dispatches to the repo's conductor CLI (python -m conductor ...) with
   the same subcommands: search/related/hubs/recall/status/gate/plan/
   verify/models.
3. No repo found → clean, actionable error (exit 2), never a traceback.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from awiki_cli.cli import build_command, find_repo_root, main  # noqa: E402


def test_find_root_from_env(tmp_path, monkeypatch):
    monkeypatch.setenv("AWIKI_ROOT", str(REPO_ROOT))
    assert find_repo_root() == REPO_ROOT


def test_find_root_walks_up_from_cwd(tmp_path, monkeypatch):
    monkeypatch.delenv("AWIKI_ROOT", raising=False)
    deep = REPO_ROOT / "wiki" / "context"
    monkeypatch.chdir(deep)
    assert find_repo_root() == REPO_ROOT


def test_find_root_missing_is_clean_error(monkeypatch):
    # must be OUTSIDE the repo (pytest tmp lives under A-Wiki/.tmp and
    # would walk up into the real root)
    import tempfile
    outside = Path(tempfile.mkdtemp(prefix="awiki-no-root-"))
    monkeypatch.delenv("AWIKI_ROOT", raising=False)
    monkeypatch.chdir(outside)
    with pytest.raises(SystemExit) as ei:
        find_repo_root()
    assert ei.value.code == 2


def test_build_command_maps_subcommands():
    for sub in ("search", "related", "hubs", "recall", "status",
                "gate", "plan", "verify", "models"):
        argv = build_command(["search", "--query", "x"]) if sub == "search" \
            else build_command([sub])
        assert argv[0] == sys.executable and "-m" in argv and "conductor" in argv


def test_cli_status_end_to_end(monkeypatch):
    """The installed entry point runs the real repo's conductor status."""
    monkeypatch.setenv("AWIKI_ROOT", str(REPO_ROOT))
    rc = main(["status", "--json"])
    assert rc == 0
