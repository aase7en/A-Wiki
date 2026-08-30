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


# R-FR-006/007 adversarial preservation + exactness coverage.
def _provider_config_path(target, provider):
    return {
        "claude": target / ".claude" / "settings.json",
        "codex": target / ".codex" / "hooks.json",
        "zcode": target / ".zcode" / "config.json",
    }[provider]


def _provider_events(data, provider):
    if provider == "zcode":
        return data["hooks"]["events"]
    return data["hooks"]


def _hook_commands(events):
    return [
        h.get("command", "")
        for blocks in events.values()
        if isinstance(blocks, list)
        for block in blocks
        if isinstance(block, dict)
        for h in block.get("hooks", [])
        if isinstance(h, dict)
    ]


@pytest.mark.parametrize("provider", ["claude", "codex", "zcode"])
def test_adopt_preserves_foreign_provider_hooks_and_top_level_fields(
        target, fake_brain, provider):
    path = _provider_config_path(target, provider)
    path.parent.mkdir(parents=True, exist_ok=True)
    foreign_block = {
        "matcher": "ForeignTool",
        "hooks": [{"type": "command", "command": "foreign-hook --keep", "timeout": 9}],
        "foreignBlockField": "keep",
    }
    events = {"PreToolUse": [foreign_block], "ForeignEvent": [foreign_block]}
    if provider == "zcode":
        original = {
            "foreignTop": {"keep": True},
            "hooks": {"enabled": False, "foreignHooksKey": "keep", "events": events},
        }
    else:
        original = {"foreignTop": {"keep": True}, "hooks": events}
    path.write_text(json.dumps(original, ensure_ascii=False), encoding="utf-8")

    assert adopt.main([str(target), "--brain", str(fake_brain)]) == 0
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["foreignTop"] == {"keep": True}
    if provider == "zcode":
        assert data["hooks"]["foreignHooksKey"] == "keep"
        assert data["hooks"]["enabled"] is True
    installed_events = _provider_events(data, provider)
    assert installed_events["ForeignEvent"][0] == foreign_block
    assert any(c == "foreign-hook --keep" for c in _hook_commands(installed_events))
    assert sum("hooks_runner.py" in c for c in _hook_commands(installed_events)) == 7


@pytest.mark.parametrize("provider", ["claude", "codex", "zcode"])
def test_re_adopt_replaces_stale_awiki_hooks_but_keeps_mixed_foreign_hook(
        target, fake_brain, provider):
    path = _provider_config_path(target, provider)
    path.parent.mkdir(parents=True, exist_ok=True)
    stale = {
        "type": "command",
        "command": '"python" "old-brain/scripts/hooks_runner.py" --provider wrong --event PreToolUse',
        "timeout": 999,
    }
    foreign = {"type": "command", "command": "foreign-hook --keep", "timeout": 5}
    mixed = {"matcher": "Edit", "hooks": [foreign, stale]}
    events = {"PreToolUse": [mixed]}
    data = ({"hooks": {"events": events, "foreignHooksKey": "keep"}}
            if provider == "zcode" else {"hooks": events})
    path.write_text(json.dumps(data), encoding="utf-8")

    assert adopt.main([str(target), "--brain", str(fake_brain)]) == 0
    installed = json.loads(path.read_text(encoding="utf-8"))
    commands = _hook_commands(_provider_events(installed, provider))
    assert "foreign-hook --keep" in commands
    assert all("old-brain" not in c for c in commands)
    assert sum("hooks_runner.py" in c for c in commands) == 7
    before = path.read_bytes()
    assert adopt.main([str(target), "--brain", str(fake_brain)]) == 0
    assert path.read_bytes() == before


@pytest.mark.parametrize("provider", ["claude", "codex", "zcode"])
def test_adopt_check_rejects_tampered_awiki_hook_wiring(target, fake_brain, provider):
    assert adopt.main([str(target), "--brain", str(fake_brain)]) == 0
    path = _provider_config_path(target, provider)
    data = json.loads(path.read_text(encoding="utf-8"))
    events = _provider_events(data, provider)
    for blocks in events.values():
        for block in blocks:
            for hook in block.get("hooks", []):
                if "hooks_runner.py" in hook.get("command", ""):
                    hook["command"] += " --tampered"
                    path.write_text(json.dumps(data), encoding="utf-8")
                    assert adopt.main([str(target), "--brain", str(fake_brain), "--check"]) == 1
                    return
    raise AssertionError("expected an A-Wiki hook")


@pytest.mark.parametrize("provider", ["claude", "codex", "zcode"])
def test_adopt_check_allows_foreign_hooks_added_after_adopt(target, fake_brain, provider):
    assert adopt.main([str(target), "--brain", str(fake_brain)]) == 0
    path = _provider_config_path(target, provider)
    data = json.loads(path.read_text(encoding="utf-8"))
    events = _provider_events(data, provider)
    events["ForeignEvent"] = [{
        "matcher": "X",
        "hooks": [{"type": "command", "command": "foreign-added", "timeout": 3}],
    }]
    data["foreignTop"] = "allowed"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert adopt.main([str(target), "--brain", str(fake_brain), "--check"]) == 0


@pytest.mark.parametrize("provider", ["claude", "codex", "zcode"])
def test_adopt_invalid_provider_json_fails_closed_and_preserves_bytes(
        target, fake_brain, provider):
    path = _provider_config_path(target, provider)
    path.parent.mkdir(parents=True, exist_ok=True)
    original = b'{"hooks":'
    path.write_bytes(original)
    assert adopt.main([str(target), "--brain", str(fake_brain)]) == 1
    assert path.read_bytes() == original


@pytest.mark.parametrize("provider", ["claude", "codex"])
def test_adopt_wrong_hooks_container_fails_closed_and_preserves_bytes(
        target, fake_brain, provider):
    path = _provider_config_path(target, provider)
    path.parent.mkdir(parents=True, exist_ok=True)
    original = json.dumps({"hooks": ["foreign"]}).encode()
    path.write_bytes(original)
    assert adopt.main([str(target), "--brain", str(fake_brain)]) == 1
    assert path.read_bytes() == original


def test_adopt_wrong_zcode_events_container_fails_closed_and_preserves_bytes(target, fake_brain):
    path = _provider_config_path(target, "zcode")
    path.parent.mkdir(parents=True, exist_ok=True)
    original = json.dumps({"hooks": {"events": ["foreign"]}}).encode()
    path.write_bytes(original)
    assert adopt.main([str(target), "--brain", str(fake_brain)]) == 1
    assert path.read_bytes() == original


def test_adopt_check_requires_exact_awiki_mcp_entry_but_allows_foreign_servers(target, fake_brain):
    assert adopt.main([str(target), "--brain", str(fake_brain)]) == 0
    path = target / ".mcp.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["mcpServers"]["foreign"] = {"command": "keep"}
    path.write_text(json.dumps(data), encoding="utf-8")
    assert adopt.main([str(target), "--brain", str(fake_brain), "--check"]) == 0

    data["mcpServers"]["awiki"]["args"] = ["wrong-server.py"]
    path.write_text(json.dumps(data), encoding="utf-8")
    assert adopt.main([str(target), "--brain", str(fake_brain), "--check"]) == 1


@pytest.mark.parametrize("provider", ["claude", "codex", "zcode"])
def test_adopt_preserves_foreign_empty_event_list(target, fake_brain, provider):
    path = _provider_config_path(target, provider)
    path.parent.mkdir(parents=True, exist_ok=True)
    events = {"ForeignEmpty": []}
    data = ({"hooks": {"events": events, "foreignHooksKey": "keep"}}
            if provider == "zcode" else {"hooks": events})
    path.write_text(json.dumps(data), encoding="utf-8")
    assert adopt.main([str(target), "--brain", str(fake_brain)]) == 0
    installed = json.loads(path.read_text(encoding="utf-8"))
    installed_events = _provider_events(installed, provider)
    assert "ForeignEmpty" in installed_events
    assert installed_events["ForeignEmpty"] == []


def _symlink_or_skip(link, target, *, directory=False):
    try:
        link.symlink_to(target, target_is_directory=directory)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlink unavailable: {exc}")


def test_adopt_rejects_symlinked_provider_file_without_touching_external_target(
        target, fake_brain, tmp_path):
    outside = tmp_path / "outside-settings.json"
    original = b'{"external":"must-stay"}'
    outside.write_bytes(original)
    path = _provider_config_path(target, "claude")
    path.parent.mkdir(parents=True, exist_ok=True)
    _symlink_or_skip(path, outside)
    assert adopt.main([str(target), "--brain", str(fake_brain)]) == 1
    assert outside.read_bytes() == original


def test_adopt_rejects_symlinked_provider_parent_without_writing_outside(
        target, fake_brain, tmp_path):
    outside_dir = tmp_path / "outside-claude"
    outside_dir.mkdir()
    parent = target / ".claude"
    _symlink_or_skip(parent, outside_dir, directory=True)
    assert adopt.main([str(target), "--brain", str(fake_brain)]) == 1
    assert not (outside_dir / "settings.json").exists()


def test_adopt_preflight_is_all_or_nothing_when_late_provider_is_invalid(
        target, fake_brain):
    codex = _provider_config_path(target, "codex")
    codex.parent.mkdir(parents=True, exist_ok=True)
    original = b'{"hooks":'
    codex.write_bytes(original)
    assert adopt.main([str(target), "--brain", str(fake_brain)]) == 1
    assert codex.read_bytes() == original
    assert not _provider_config_path(target, "claude").exists()
    assert not _provider_config_path(target, "zcode").exists()
    assert not (target / ".mcp.json").exists()


def test_adopt_check_rejects_exact_field_and_duplicate_drift(target, fake_brain):
    assert adopt.main([str(target), "--brain", str(fake_brain)]) == 0

    claude_path = _provider_config_path(target, "claude")
    claude = json.loads(claude_path.read_text(encoding="utf-8"))
    claude["hooks"]["SessionStart"][0]["hooks"][0]["timeout"] = 31
    claude_path.write_text(json.dumps(claude), encoding="utf-8")
    assert adopt.main([str(target), "--brain", str(fake_brain), "--check"]) == 1
    assert adopt.main([str(target), "--brain", str(fake_brain)]) == 0

    codex_path = _provider_config_path(target, "codex")
    codex = json.loads(codex_path.read_text(encoding="utf-8"))
    codex["hooks"]["PreToolUse"][0]["matcher"] = "WrongMatcher"
    codex_path.write_text(json.dumps(codex), encoding="utf-8")
    assert adopt.main([str(target), "--brain", str(fake_brain), "--check"]) == 1
    assert adopt.main([str(target), "--brain", str(fake_brain)]) == 0

    zcode_path = _provider_config_path(target, "zcode")
    zcode = json.loads(zcode_path.read_text(encoding="utf-8"))
    zcode["hooks"]["enabled"] = False
    zcode_path.write_text(json.dumps(zcode), encoding="utf-8")
    assert adopt.main([str(target), "--brain", str(fake_brain), "--check"]) == 1
    assert adopt.main([str(target), "--brain", str(fake_brain)]) == 0

    claude = json.loads(claude_path.read_text(encoding="utf-8"))
    claude["hooks"]["SessionStart"].append(claude["hooks"]["SessionStart"][-1])
    claude_path.write_text(json.dumps(claude), encoding="utf-8")
    assert adopt.main([str(target), "--brain", str(fake_brain), "--check"]) == 1


def test_adopt_rejects_symlinked_seed_without_touching_external_target(
        target, fake_brain, tmp_path):
    outside = tmp_path / "outside-agents.md"
    original = b"external instructions must stay\n"
    outside.write_bytes(original)
    agents = target / "AGENTS.md"
    _symlink_or_skip(agents, outside)

    assert adopt.main([str(target), "--brain", str(fake_brain)]) == 1
    assert outside.read_bytes() == original
    assert not _provider_config_path(target, "claude").exists()
    assert not (target / ".mcp.json").exists()


def test_adopt_check_rejects_symlinked_provider(
        target, fake_brain, tmp_path):
    assert adopt.main([str(target), "--brain", str(fake_brain)]) == 0
    path = _provider_config_path(target, "claude")
    path.unlink()
    outside = tmp_path / "external-check.json"
    outside.write_text('{"hooks": {}}', encoding="utf-8")
    _symlink_or_skip(path, outside)

    assert adopt.main([str(target), "--brain", str(fake_brain), "--check"]) == 1


def test_adopt_check_rejects_link_before_read(target, fake_brain, tmp_path, monkeypatch):
    assert adopt.main([str(target), "--brain", str(fake_brain)]) == 0
    path = _provider_config_path(target, "claude")
    path.unlink()
    outside = tmp_path / "external-link-canary.json"
    outside.write_text('{"hooks": {}}', encoding="utf-8")
    _symlink_or_skip(path, outside)
    original_read_text = Path.read_text

    def guarded_read_text(self, *args, **kwargs):
        if self == path and self.is_symlink():
            raise AssertionError("verifier read linked config before rejecting it")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded_read_text)
    assert adopt.main([str(target), "--brain", str(fake_brain), "--check"]) == 1


def test_adopt_check_rejects_linked_agents_without_raising(
        target, fake_brain, tmp_path, monkeypatch):
    assert adopt.main([str(target), "--brain", str(fake_brain)]) == 0
    agents = target / "AGENTS.md"
    agents.unlink()
    outside = tmp_path / "external-agents-canary.md"
    outside.write_text("external\n", encoding="utf-8")
    _symlink_or_skip(agents, outside)
    original_read_text = Path.read_text

    def guarded_read_text(self, *args, **kwargs):
        if self == agents and self.is_symlink():
            raise AssertionError("verifier read linked AGENTS.md")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded_read_text)
    assert adopt.main([str(target), "--brain", str(fake_brain), "--check"]) == 1


def test_adopt_check_rejects_extra_metadata_on_awiki_owned_block(target, fake_brain):
    assert adopt.main([str(target), "--brain", str(fake_brain)]) == 0
    path = _provider_config_path(target, "claude")
    data = json.loads(path.read_text(encoding="utf-8"))
    data["hooks"]["SessionStart"][0]["unexpectedBehavior"] = "tampered"
    path.write_text(json.dumps(data), encoding="utf-8")

    assert adopt.main([str(target), "--brain", str(fake_brain), "--check"]) == 1


def test_adopt_check_rejects_missing_owned_gitignore_rule(target, fake_brain):
    assert adopt.main([str(target), "--brain", str(fake_brain)]) == 0
    path = target / ".gitignore"
    path.write_text("# target rules only\n", encoding="utf-8")

    assert adopt.main([str(target), "--brain", str(fake_brain), "--check"]) == 1


def test_adopt_check_rejects_wrong_adopted_brain_root(target, fake_brain):
    assert adopt.main([str(target), "--brain", str(fake_brain)]) == 0
    path = target / "AGENTS.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace(f"- Brain root: `{fake_brain}`", "- Brain root: `wrong-brain`")
    path.write_text(text, encoding="utf-8")

    assert adopt.main([str(target), "--brain", str(fake_brain), "--check"]) == 1


def test_re_adopt_repairs_owned_brain_root_and_preserves_foreign_agents_text(
        target, fake_brain):
    assert adopt.main([str(target), "--brain", str(fake_brain)]) == 0
    path = target / "AGENTS.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace(f"- Brain root: `{fake_brain}`", "- Brain root: `stale-brain`")
    text += "\nFOREIGN TARGET RULE — KEEP\n"
    path.write_text(text, encoding="utf-8")

    assert adopt.main([str(target), "--brain", str(fake_brain)]) == 0
    repaired = path.read_text(encoding="utf-8")
    assert f"- Brain root: `{fake_brain}`" in repaired
    assert "stale-brain" not in repaired
    assert "FOREIGN TARGET RULE — KEEP" in repaired


def test_re_adopt_restores_exact_gitignore_rule_when_only_comment_mentions_it(
        target, fake_brain):
    assert adopt.main([str(target), "--brain", str(fake_brain)]) == 0
    path = target / ".gitignore"
    path.write_text("# .tmp/ rule intentionally removed\n", encoding="utf-8")

    assert adopt.main([str(target), "--brain", str(fake_brain), "--check"]) == 1
    assert adopt.main([str(target), "--brain", str(fake_brain)]) == 0
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    assert ".tmp/" in lines
