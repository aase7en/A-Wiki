"""A-Wiki Conductor v0.1.0 — contract tests (TDD: red first).

Product: provider-neutral orchestration head over the A-Wiki brain —
layered config (Serena-inspired), unified status, entry-gate verdicts,
and deterministic objective→work-order planning. Reuses COLLAB claims,
hook registry, and repo gates; adds NO new background services.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))


# ── config layering ────────────────────────────────────────────────────
class TestLayeredConfig:
    def test_defaults_load_without_any_project_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from conductor.config import load_config
        cfg = load_config()
        assert cfg["schema"] == "awiki-conductor/v1"
        assert cfg["modes"]["base"] == ["safety"]

    def test_project_layer_overrides_defaults(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".awiki-conductor.yaml").write_text(
            "schema: awiki-conductor/v1\nmodes:\n  added: [night-shift]\n", encoding="utf-8")
        from conductor.config import load_config
        cfg = load_config()
        assert "night-shift" in cfg["modes"]["added"]
        assert cfg["modes"]["base"] == ["safety"]  # defaults survive

    def test_env_layer_wins_over_files(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("AWIKI_CONDUCTOR_MODE_ADDED", "quiet,focus")
        from conductor.config import load_config
        cfg = load_config()
        assert set(cfg["modes"]["added"]) >= {"quiet", "focus"}

    def test_incompatible_modes_fail_closed(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".awiki-conductor.yaml").write_text(
            "schema: awiki-conductor/v1\nmodes:\n  default: [interactive, one-shot]\n",
            encoding="utf-8")
        from conductor.config import ConfigError, load_config
        with pytest.raises(ConfigError):
            load_config()

    def test_unknown_schema_rejected(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".awiki-conductor.yaml").write_text("schema: bogus/v9\n", encoding="utf-8")
        from conductor.config import ConfigError, load_config
        with pytest.raises(ConfigError):
            load_config()


# ── unified status (read-only) ─────────────────────────────────────────
class TestStatus:
    def test_status_reports_claims_branches_and_gates(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "COLLAB.md").write_text(
            "# COLLAB\n\n| Chunk/WO | Agent | Claimed | Scope | Branch / PR |\n"
            "|---|---|---|---|---|\n"
            "| demo-task | claude | 2026-08-21 | scripts/x.py | feat/x |\n",
            encoding="utf-8")
        from conductor.state import conductor_status
        s = conductor_status(repo_root=tmp_path)
        assert any(c["chunk"] == "demo-task" for c in s["claims"])
        assert "branches" in s and isinstance(s["branches"], list)
        assert "gate_tools" in s  # registry-derived hard-gate count

    def test_status_is_read_only(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        before = sorted(str(q) for q in tmp_path.rglob("*"))
        from conductor.state import conductor_status
        conductor_status(repo_root=tmp_path)
        after = sorted(str(q) for q in tmp_path.rglob("*"))
        assert before == after


# ── entry gate verdicts ────────────────────────────────────────────────
class TestEntryGate:
    def _collab(self, tmp_path, rows=""):
        (tmp_path / "COLLAB.md").write_text(
            "# COLLAB\n\n| Chunk/WO | Agent | Claimed | Scope | Branch / PR |\n"
            "|---|---|---|---|---|\n" + rows, encoding="utf-8")

    def test_clean_entry_passes(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        self._collab(tmp_path)
        from conductor.gate import entry_gate
        v = entry_gate(repo_root=tmp_path, topic="fresh-idea", agent="zcode")
        assert v["verdict"] == "GO"
        assert v["checks"]["collab_read"] is True
        assert v["checks"]["no_conflict"] is True

    def test_conflicting_topic_blocks(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        self._collab(tmp_path, "| fresh-idea | claude | 2026-08-21 | a/** | feat/a |\n")
        from conductor.gate import entry_gate
        v = entry_gate(repo_root=tmp_path, topic="fresh-idea", agent="zcode")
        assert v["verdict"] == "NO-GO"
        assert v["conflicts"], "must name the conflicting claim"

    def test_missing_collab_fails_closed(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from conductor.gate import entry_gate
        v = entry_gate(repo_root=tmp_path, topic="x", agent="zcode")
        assert v["verdict"] == "NO-GO"
        assert v["checks"]["collab_read"] is False

    def test_gate_suggests_claim_row(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        self._collab(tmp_path)
        from conductor.gate import entry_gate
        v = entry_gate(repo_root=tmp_path, topic="fresh-idea", agent="zcode")
        assert "fresh-idea" in v["claim_row"] and "zcode" in v["claim_row"]


# ── deterministic planning ─────────────────────────────────────────────
class TestPlanner:
    def test_objective_decomposes_into_work_orders(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from conductor.plan import plan_objective
        wos = plan_objective(
            "ship conductor spike: config layering, entry gate, CLI status",
            repo_root=tmp_path)
        assert len(wos) >= 3
        for wo in wos:
            assert wo["id"] and wo["goal"] and wo["verify"]
        ids = [w["id"] for w in wos]
        assert len(ids) == len(set(ids))

    def test_lanes_suggested_from_paths(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from conductor.plan import plan_objective
        wos = plan_objective("fix scripts/hooks/check_x.py and .github/workflows/ci.yml",
                             repo_root=tmp_path)
        lanes = {w["lane"] for w in wos}
        assert any("hook" in l or "infra" in l for l in lanes)

    def test_plan_writes_work_order_files(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from conductor.plan import plan_objective
        wos = plan_objective("spike: a, b, c", repo_root=tmp_path, write=True)
        files = list((tmp_path / "docs" / "work-orders").glob("*.md"))
        assert len(files) == len(wos)
        for f in files:
            assert "Status" in f.read_text(encoding="utf-8")


# ── CLI ────────────────────────────────────────────────────────────────
class TestCli:
    def _run(self, *args):
        import subprocess
        return subprocess.run(
            [sys.executable, "-m", "conductor", *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(REPO_ROOT), timeout=120)

    def test_status_json_valid(self):
        r = self._run("status", "--json")
        assert r.returncode == 0, r.stderr[:300]
        data = json.loads(r.stdout)
        assert data["schema"] == "awiki-conductor/v1"

    def test_gate_topic_go(self):
        r = self._run("gate", "--topic", "totally-new-thing", "--agent", "zcode", "--json")
        assert r.returncode == 0, r.stderr[:300]
        v = json.loads(r.stdout)
        assert v["verdict"] in ("GO", "NO-GO")

    def test_plan_smoke(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        r = self._run("plan", "spike: alpha, beta, gamma", "--json")
        assert r.returncode == 0, r.stderr[:300]
        assert len(json.loads(r.stdout)["work_orders"]) >= 3


class TestColabParsingRegression:
    def test_lanes_table_not_swallowed_into_claims(self, tmp_path):
        """Real-world COLLAB.md has a Lanes table BEFORE the claims table —
        the claims parser must anchor on the Chunk/WO header, not any |---."""
        (tmp_path / "COLLAB.md").write_text(
            "# COLLAB\n\n"
            "| Lane | ธีมงาน | ไฟล์ | ห้ามแตะ |\n|---|---|---|---|\n"
            "| migration | phases | docs/migration/** | - |\n\n"
            "| Chunk/WO | Agent | Claimed | Scope | Branch / PR |\n|---|---|---|---|---|\n"
            "| real-task | claude | 2026-08-21 | a/** | feat/a |\n",
            encoding="utf-8")
        from conductor.state import parse_claims
        claims = parse_claims(tmp_path / "COLLAB.md")
        chunks = [c["chunk"] for c in claims]
        assert chunks == ["real-task"], f"lanes leaked into claims: {chunks}"
