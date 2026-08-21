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


# ══════════════════════════════════════════════════════════════════════
# v0.2 — Brain Bridge: verify / recall / claim
# ══════════════════════════════════════════════════════════════════════
class TestVerify:
    def test_verify_runs_repo_gates_bounded_and_structured(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from conductor.bridge import run_verify
        out = run_verify(repo_root=REPO_ROOT, gates=["registry"], timeout=120)
        assert out["schema"] == "awiki-conductor/v1"
        g = {r["gate"]: r for r in out["results"]}
        assert g["registry"]["passed"] is True
        assert g["registry"]["duration_s"] >= 0

    def test_verify_unknown_gate_fails_closed(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from conductor.bridge import run_verify, VerifyError
        with pytest.raises(VerifyError):
            run_verify(repo_root=REPO_ROOT, gates=["not-a-gate"], timeout=10)

    def test_verify_bounded_timeout_reports_failure(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from conductor.bridge import run_verify
        out = run_verify(repo_root=REPO_ROOT, gates=["registry"], timeout=0)
        assert out["results"][0]["passed"] is False
        assert "timeout" in out["results"][0]["detail"].lower()


class TestRecall:
    def test_recall_reads_ledger_read_only(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        led = tmp_path / "ledger.jsonl"
        import time as _t
        rows = [
            {"ts": _t.time() - 5, "session_id": "s1", "type": "lesson",
             "summary": "hook engine registry owns matchers", "files": [], "tags": [],
             "parent_ts": None},
            {"ts": _t.time(), "session_id": "s2", "type": "decision",
             "summary": "scanner strict mode fail-closed", "files": [], "tags": [],
             "parent_ts": None},
        ]
        led.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
        from conductor.bridge import recall
        hits = recall("registry", ledger=led, limit=5)
        assert any("matchers" in h["summary"] for h in hits)
        # read-only: file unchanged
        assert len(led.read_text(encoding="utf-8").splitlines()) == 2

    def test_recall_never_emits_secrets(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        led = tmp_path / "ledger.jsonl"
        token = "sk-" + "RecallProbe" + "0123456789abcdef"
        led.write_text(json.dumps({
            "ts": 1.0, "session_id": "s", "type": "lesson",
            "summary": f"leaked {token} once", "files": [], "tags": [],
            "parent_ts": None}), encoding="utf-8")
        from conductor.bridge import recall
        hits = recall("leaked", ledger=led)
        blob = json.dumps(hits)
        assert token not in blob and "***" in blob


class TestClaim:
    def _collab(self, tmp_path, rows=""):
        p = tmp_path / "COLLAB.md"
        p.write_text(
            "# COLLAB\n\n| Chunk/WO | Agent | Claimed | Scope | Branch / PR |\n"
            "|---|---|---|---|---|\n" + rows, encoding="utf-8")
        return p

    def test_claim_appends_row_after_go(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        p = self._collab(tmp_path)
        from conductor.bridge import add_claim
        out = add_claim(repo_root=tmp_path, topic="fresh-thing",
                        agent="zcode", scope="scripts/x.py", branch="feat/x")
        assert out["claimed"] is True
        text = p.read_text(encoding="utf-8")
        assert "fresh-thing" in text and "zcode" in text and "feat/x" in text

    def test_claim_refuses_on_conflict(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        self._collab(tmp_path, "| taken-topic | claude | 2026-08-21 | a/** | feat/a |\n")
        from conductor.bridge import add_claim, ClaimConflict
        with pytest.raises(ClaimConflict):
            add_claim(repo_root=tmp_path, topic="taken-topic", agent="zcode")

    def test_claim_idempotent_same_agent(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        self._collab(tmp_path)
        from conductor.bridge import add_claim
        add_claim(repo_root=tmp_path, topic="t1", agent="zcode")
        out = add_claim(repo_root=tmp_path, topic="t1", agent="zcode")
        assert out["claimed"] is True and out.get("already") is True
        text = (tmp_path / "COLLAB.md").read_text(encoding="utf-8")
        assert text.count("| t1 |") == 1

    def test_claim_refuses_when_collab_missing(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from conductor.bridge import add_claim, ClaimConflict
        with pytest.raises(ClaimConflict):
            add_claim(repo_root=tmp_path, topic="x", agent="z")


class TestBridgeCli:
    def _run(self, *args):
        import subprocess
        return subprocess.run(
            [sys.executable, "-m", "conductor", *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(REPO_ROOT), timeout=180)

    def test_verify_cli(self):
        r = self._run("verify", "--gates", "registry", "--json")
        assert r.returncode == 0, r.stderr[:300]
        out = json.loads(r.stdout)
        assert out["results"][0]["gate"] == "registry"

    def test_recall_cli(self):
        r = self._run("recall", "--query", "phase", "--json")
        assert r.returncode == 0, r.stderr[:300]
        assert "hits" in json.loads(r.stdout)


# ══════════════════════════════════════════════════════════════════════
# Slice 1 — Brain Bridge graph/search navigation (A-Conductor Phase 4)
# ══════════════════════════════════════════════════════════════════════
class TestBridgeSearch:
    def _run(self, *args):
        import subprocess
        return subprocess.run(
            [sys.executable, "-m", "conductor", *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(REPO_ROOT), timeout=180)

    def test_search_fts_returns_structured_hits(self):
        r = self._run("search", "--query", "esp32 lora", "--mode", "fts", "--json")
        assert r.returncode == 0, r.stderr[:400]
        out = json.loads(r.stdout)
        assert out["schema"] == "awiki-conductor/v1"
        assert out["mode"] == "fts"
        assert isinstance(out["hits"], list) and out["hits"], "must find esp32/lora pages"
        hit = out["hits"][0]
        for key in ("path", "title", "score"):
            assert key in hit

    def test_search_hybrid_mode_is_default(self):
        r = self._run("search", "--query", "mqtt protocol iot", "--json")
        assert r.returncode == 0, r.stderr[:400]
        out = json.loads(r.stdout)
        assert out["mode"] in ("hybrid", "fts")  # hybrid when deps present, else fts

    def test_search_bad_mode_fails_closed(self):
        r = self._run("search", "--query", "x", "--mode", "bogus", "--json")
        assert r.returncode != 0
        assert "mode" in r.stdout + r.stderr


class TestBridgeRelated:
    def _run(self, *args):
        import subprocess
        return subprocess.run(
            [sys.executable, "-m", "conductor", *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(REPO_ROOT), timeout=120)

    def test_related_returns_graph_neighbors(self):
        r = self._run("related", "--page", "wiki/entities/iot/esp32.md", "--json")
        assert r.returncode == 0, r.stderr[:400]
        out = json.loads(r.stdout)
        assert out["page"] == "wiki/entities/iot/esp32.md"
        assert isinstance(out.get("neighbors"), list)
        # a hub page must actually have neighbors
        assert out["neighbors"], "esp32 is a hub — must have graph neighbors"

    def test_related_unknown_page_is_deterministic(self):
        r = self._run("related", "--page", "wiki/no/such-page.md", "--json")
        assert r.returncode == 0
        out = json.loads(r.stdout)
        assert out["neighbors"] == []


class TestBridgeHubs:
    def _run(self, *args):
        import subprocess
        return subprocess.run(
            [sys.executable, "-m", "conductor", *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(REPO_ROOT), timeout=120)

    def test_hubs_returns_ranked_list(self):
        r = self._run("hubs", "--json")
        assert r.returncode == 0, r.stderr[:400]
        out = json.loads(r.stdout)
        assert isinstance(out["hubs"], list) and out["hubs"]
        top = out["hubs"][0]
        assert "path" in top and "degree" in top
        degrees = [h["degree"] for h in out["hubs"]]
        assert degrees == sorted(degrees, reverse=True)


class TestRecallBM25:
    def test_recall_ranks_by_relevance_not_substring(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        led = tmp_path / "ledger.jsonl"
        import time as _t
        rows = [
            {"ts": 1.0, "session_id": "s1", "type": "lesson",
             "summary": "unrelated topic alpha beta", "files": [], "tags": [], "parent_ts": None},
            {"ts": 2.0, "session_id": "s2", "type": "lesson",
             "summary": "esp32 lora gateway deep lesson learned", "files": [], "tags": [], "parent_ts": None},
            {"ts": 3.0, "session_id": "s3", "type": "decision",
             "summary": "esp32 pinout note only — no lora here", "files": [], "tags": [], "parent_ts": None},
        ]
        led.write_text("\n".join(json.dumps(x) for x in rows), encoding="utf-8")
        from conductor.bridge import recall
        hits = recall("esp32 lora gateway", ledger=led)
        assert hits, "must find the relevant entry"
        assert "esp32 lora" in hits[0]["summary"], (
            "top hit must be the entry matching MOST query terms — a "
            "single-token distractor must lose to the multi-term match")
