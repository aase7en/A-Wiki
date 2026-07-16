"""Tests for the P6 global env system: loader, IDE hook, linker expansion.

Hermetic — uses temp dirs + fixture env files, no real Drive mount needed.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"


def _run_bash(script: Path, args: list[str], env: dict | None = None,
              timeout: int = 30) -> subprocess.CompletedProcess:
    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    return subprocess.run(
        ["bash", str(script)] + args,
        cwd=str(REPO_ROOT), text=True, capture_output=True, timeout=timeout, env=full_env,
    )


class TestLoader:
    def test_loader_has_help_flag(self):
        proc = _run_bash(SCRIPTS / "load-global-env.sh", ["--help"])
        assert proc.returncode == 0

    def test_loader_print_mode_outputs_kv(self, tmp_path):
        secrets = tmp_path / "secrets"
        secrets.mkdir()
        (secrets / "global.env").write_text("FAKE_KEY_1=abc123\nFAKE_KEY_2=xyz\n", encoding="utf-8")
        proc = _run_bash(SCRIPTS / "load-global-env.sh", ["--print"],
                         env={"A_WIKI_DRIVE_PATH": str(tmp_path)})
        assert proc.returncode == 0
        assert "FAKE_KEY_1=abc123" in proc.stdout
        assert "FAKE_KEY_2=xyz" in proc.stdout

    def test_loader_repo_override(self, tmp_path):
        secrets = tmp_path / "secrets"
        secrets.mkdir()
        (secrets / "global.env").write_text("SHARED_KEY=global\nOVERRIDE_ME=from_global\n", encoding="utf-8")
        (secrets / "myrepo.env").write_text("OVERRIDE_ME=from_repo\nREPO_ONLY=repo_value\n", encoding="utf-8")
        proc = _run_bash(SCRIPTS / "load-global-env.sh", ["--print", "--repo", "myrepo"],
                         env={"A_WIKI_DRIVE_PATH": str(tmp_path)})
        assert proc.returncode == 0
        out = proc.stdout
        assert "SHARED_KEY=global" in out
        assert "OVERRIDE_ME=from_repo" in out, f"repo override not applied; got: {out!r}"
        assert "REPO_ONLY=repo_value" in out


class TestIdeHook:
    def test_status_flag_works(self):
        proc = _run_bash(SCRIPTS / "setup-ide-env.sh", ["--status"])
        assert proc.returncode == 0
        assert "IDE env hook status" in proc.stdout

    def test_inject_is_idempotent(self, tmp_path):
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        (fake_home / ".bashrc").write_text("# existing\n", encoding="utf-8")
        env = dict(os.environ); env["HOME"] = str(fake_home)
        _run_bash(SCRIPTS / "setup-ide-env.sh", [], env=env)
        c1 = (fake_home / ".bashrc").read_text(encoding="utf-8")
        n1 = c1.count("A-Wiki global env (setup-ide-env.sh)")
        _run_bash(SCRIPTS / "setup-ide-env.sh", [], env=env)
        c2 = (fake_home / ".bashrc").read_text(encoding="utf-8")
        n2 = c2.count("A-Wiki global env (setup-ide-env.sh)")
        assert n1 == 1
        assert n2 == 1


class TestLinkerEnvAgents:
    def test_env_agents_covers_all_supported_agents(self):
        import re
        linker = (SCRIPTS / "link-agent-configs.sh").read_text(encoding="utf-8")
        an = re.search(r'AGENT_NAMES="([^"]+)"', linker)
        ea = re.search(r'ENV_AGENTS="([^"]+)"', linker)
        assert an and ea
        agent_names = set(an.group(1).split())
        env_agents = set(ea.group(1).split())
        missing = agent_names - env_agents
        assert not missing, f"agents missing from ENV_AGENTS: {missing}"


class TestScriptsExist:
    @pytest.mark.parametrize("name", [
        "load-global-env.sh", "setup-ide-env.sh", "link-agent-configs.sh",
    ])
    def test_script_present(self, name):
        assert (SCRIPTS / name).exists()

    def test_secrets_protocol_doc_present(self):
        assert (REPO_ROOT / "docs" / "protocols" / "secrets-global-env.md").exists()
