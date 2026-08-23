"""awiki-adopt — Slice A: embed the A-Wiki brain into any repo.

Contract (user promise: "awiki adopt <repo>" one command):
- writes provider hook configs (claude settings / zcode config / codex
  hooks.json) whose commands point at the BRAIN's runner by ABSOLUTE path
- registers the awiki MCP server in .mcp.json pointing back at the brain
- seeds BRAIN-ENTRY.md + COLLAB.md + an AGENTS.md section (marker-guarded)
- idempotent: re-adopt is a no-op; --check reports drift (rc 1)
- never writes outside <target>
"""
from __future__ import annotations

import importlib.util as ilu
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
spec = ilu.spec_from_file_location("adopt", REPO_ROOT / "scripts" / "awiki-adopt.py")
adopt = ilu.module_from_spec(spec)
spec.loader.exec_module(adopt)


@pytest.fixture()
def fake_brain(tmp_path):
    brain = tmp_path / "brain"
    for rel in ("scripts/hooks_runner.py", "scripts/mcp-wiki-server.py",
                "skills-registry.json", "AGENTS.md", "BRAIN-ENTRY.md"):
        f = brain / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("# fake\n", encoding="utf-8")
    return brain


@pytest.fixture()
def target(tmp_path):
    t = tmp_path / "myapp"
    t.mkdir()
    (t / ".git").mkdir()
    (t / "README.md").write_text("# myapp\n", encoding="utf-8")
    return t


def test_adopt_installs_all_pieces(target, fake_brain):
    rc = adopt.main([str(target), "--brain", str(fake_brain)])
    assert rc == 0
    # 1) provider hook configs point at the brain runner (absolute)
    claude = json.loads((target / ".claude" / "settings.json").read_text(encoding="utf-8"))
    cmds = [h["command"]
            for blocks in claude.get("hooks", {}).values()
            for b in blocks for h in b.get("hooks", [])]
    assert any(f'"{fake_brain}/scripts/hooks_runner.py"' in c
               or f"{fake_brain}/scripts/hooks_runner.py" in c for c in cmds)
    assert any("--provider claude" in c for c in cmds)
    zc = json.loads((target / ".zcode" / "config.json").read_text(encoding="utf-8"))
    assert "PreToolUse" in zc["hooks"]["events"]
    assert "hooks_runner.py" in zc["hooks"]["events"]["PreToolUse"][0]["hooks"][0]["command"]
    codex = json.loads((target / ".codex" / "hooks.json").read_text(encoding="utf-8"))
    assert "PreToolUse" in codex["hooks"]
    # 2) MCP server entry points home
    mcp = json.loads((target / ".mcp.json").read_text(encoding="utf-8"))
    entry = mcp["mcpServers"]["awiki"]
    assert str(fake_brain) in entry["args"][0]
    # 3) SSoT seeds + AGENTS section + gitignore
    assert (target / "BRAIN-ENTRY.md").is_file()
    assert (target / "COLLAB.md").is_file()
    agents = (target / "AGENTS.md").read_text(encoding="utf-8")
    assert "A-Wiki Brain (adopted)" in agents and str(fake_brain) in agents
    assert ".tmp/" in (target / ".gitignore").read_text(encoding="utf-8")


def test_adopt_is_idempotent(target, fake_brain):
    adopt.main([str(target), "--brain", str(fake_brain)])
    snap = {p: p.read_bytes() for p in target.rglob("*") if p.is_file()}
    assert adopt.main([str(target), "--brain", str(fake_brain)]) == 0
    assert {p: p.read_bytes() for p in target.rglob("*") if p.is_file()} == snap


def test_adopt_check_reports_drift(target, fake_brain):
    assert adopt.main([str(target), "--brain", str(fake_brain)]) == 0
    assert adopt.main([str(target), "--brain", str(fake_brain), "--check"]) == 0
    (target / ".claude" / "settings.json").write_text("{}", encoding="utf-8")
    assert adopt.main([str(target), "--brain", str(fake_brain), "--check"]) == 1


def test_adopt_refuses_non_repo(tmp_path, fake_brain):
    empty = tmp_path / "not-a-repo"
    empty.mkdir()
    assert adopt.main([str(empty), "--brain", str(fake_brain)]) == 2


def test_adopt_preserves_existing_mcp_entries(target, fake_brain):
    (target / ".mcp.json").write_text(json.dumps(
        {"mcpServers": {"existing": {"command": "x"}}}), encoding="utf-8")
    adopt.main([str(target), "--brain", str(fake_brain)])
    mcp = json.loads((target / ".mcp.json").read_text(encoding="utf-8"))
    assert "existing" in mcp["mcpServers"] and "awiki" in mcp["mcpServers"]


class TestAdoptE2EWithRealBrain:
    """Full journey against the REAL brain + a fresh sandbox repo:
    adopt once -> gates actually guard the sandbox (cross-repo), claims
    land in the sandbox, and the brain MCP answers from sandbox cwd."""

    def _sandbox(self, tmp_path):
        import subprocess as sp
        t = tmp_path / "sandbox-app"
        t.mkdir()
        sp.run(["git", "init", "-q", str(t)], check=True, timeout=60)
        (t / "README.md").write_text("# sandbox\n", encoding="utf-8")
        return t

    def test_gates_guard_sandbox_after_adopt(self, tmp_path):
        t = self._sandbox(tmp_path)
        assert adopt.main([str(t), "--brain", str(REPO_ROOT)]) == 0
        import subprocess as sp
        # absolute path inside sandbox/raw/ must be BLOCKED via payload cwd
        (t / "raw").mkdir()
        victim = t / "raw" / "doc.md"
        victim.write_text("src", encoding="utf-8")
        payload = {"cwd": str(t), "session_id": "e2e",
                   "tool_name": "Edit",
                   "tool_input": {"file_path": str(victim),
                                   "old_string": "a", "new_string": "b"}}
        res = sp.run([sys.executable, str(REPO_ROOT / "scripts" / "hooks_runner.py"),
                      "--provider", "claude", "--event", "PreToolUse"],
                     input=json.dumps(payload), capture_output=True, text=True,
                     encoding="utf-8", errors="replace",
                     cwd=str(t), timeout=120)
        assert res.returncode == 2, "adopted repo must be guarded by brain gates"

    def test_claims_isolated_to_sandbox(self, tmp_path):
        """Runner exports AWIKI_CLAIMS_STORE=<cwd>/.tmp/agent-claims.json for
        hook subprocesses; a claim made under that env lands in the sandbox
        and stays invisible to the brain's own store."""
        t = self._sandbox(tmp_path)
        assert adopt.main([str(t), "--brain", str(REPO_ROOT)]) == 0
        import subprocess as sp, os
        store = t / ".tmp" / "agent-claims.json"
        lib = str(REPO_ROOT / "scripts" / "lib")
        env = {**os.environ, "AWIKI_CLAIMS_STORE": str(store),
               "AWIKI_AGENT": "sandbox-agent", "PYTHONPATH": lib}
        code = ("import json,agent_claims as ac;"
                "ac.acquire(agent='sandbox-agent',"
                "scope=['skills/demo/SKILL.md'], goal='sandbox work',"
                "phase='implement');"
                "print(json.dumps([c['goal'] for c in ac.live()]))")
        res = sp.run([sys.executable, "-c", code], capture_output=True,
                     text=True, encoding="utf-8", errors="replace",
                     cwd=str(t), env=env, timeout=120)
        assert res.returncode == 0, res.stderr[-300:]
        assert store.exists(), "claim store must land in the sandbox"
        assert "sandbox work" in res.stdout
        brain_seen = sp.run(
            [sys.executable, "-c",
             "import json,agent_claims as ac;"
             "print(json.dumps([c['goal'] for c in ac.live()]))"],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", cwd=str(REPO_ROOT),
            env={**os.environ, "PYTHONPATH": lib}, timeout=120)
        assert "sandbox work" not in brain_seen.stdout

    def test_brain_mcp_answers_from_sandbox(self, tmp_path):
        """The adopted .mcp.json env (AWIKI_ROOT) points home; simulate the
        client by spawning the brain server with that env from sandbox cwd."""
        t = self._sandbox(tmp_path)
        assert adopt.main([str(t), "--brain", str(REPO_ROOT)]) == 0
        import subprocess as sp, os
        mcp = json.loads((t / ".mcp.json").read_text(encoding="utf-8"))
        entry = mcp["mcpServers"]["awiki"]
        env = {**os.environ, "PYTHONIOENCODING": "utf-8",
               **entry.get("env", {})}
        proc = sp.Popen([entry["command"], *entry["args"]],
                        stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE,
                        text=True, encoding="utf-8", errors="replace",
                        cwd=str(t), env=env)

        def send(m):
            proc.stdin.write(json.dumps(m) + "\n"); proc.stdin.flush()

        def read(rid):
            for _ in range(300):
                line = proc.stdout.readline()
                if not line:
                    return None
                d = json.loads(line)
                if d.get("id") == rid:
                    return d
        try:
            send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                  "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                             "clientInfo": {"name": "adopt-e2e", "version": "0"}}})
            read(1)
            send({"jsonrpc": "2.0", "method": "notifications/initialized"})
            send({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                  "params": {"name": "wiki_search",
                             "arguments": {"query": "hermes"}}})
            r = read(2)
            assert r and "result" in r
            assert "hermes" in r["result"]["content"][0]["text"].lower()
        finally:
            proc.stdin.close()
            proc.kill()
