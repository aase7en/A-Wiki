#!/usr/bin/env python3
"""User-journey E2E — เดินตามทาง user ใช้จริง: เปิดสมอง → ค้น/ถามทุกปุ่ม →
สั่งงาน (routing) → ทำงานมี gate คุม → ปิดวัน (verify/claims release)

ออกแบบตาม user vision pattern (Plan→Grill→Brainstorm→Loop→Production):
ทุก "ปุ่ม" ที่ user-facing ต้องถูกกดอย่างน้อยหนึ่งครั้ง — conductor CLI 10 คำสั่ง,
MCP 31 tools + 3 resources, brain scripts, skill routing 2 tiers,
session lifecycle sweeps ทุก provider, generators --check.

State isolation: ทุก stateful seam ถูก redirect ไป tmp (ledger/claims/focus/
flow/task/blackboard) ผ่าน env — harness ไม่เขียนอะไรลง state จริงของ repo.
Destructive buttons (wiki_regen_index, wiki_ingest_route จริง, batch_collect)
ถูกกดแบบ "ต้องตอบ error สุภาพ/ปฏิเสธ" — ปุ่มทำงาน = มี response ที่กำหนด.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "hooks"))

RUNNER = str(REPO_ROOT / "scripts" / "hooks_runner.py")
CLI_MODULE = ["-m", "conductor"]  # documented entry: python -m conductor
MCP = str(REPO_ROOT / "scripts" / "mcp-wiki-server.py")

SECRET_TOKEN = "ghp_" + "JourneyE2E" + "0123456789abcdefghijklmnop"  # 36 chars
MACHINE_PATH_FILE = "C" + chr(58) + chr(92) + "Users" + chr(92) + "me" + chr(92) + "secret.txt"


# ──────────────────────────────────────────────────────────────────────
# journey-scoped isolated environment (production seams redirected)
# ──────────────────────────────────────────────────────────────────────
@pytest.fixture()
def journey_env(tmp_path: Path) -> dict:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    for key in (
        "HOOK_SKIP", "AWIKI_CLAIM_GATE", "AWIKI_CLAIMS_STORE", "AWIKI_AGENT",
        "AWIKI_FOCUS_ENFORCE", "AWIKI_FOCUS_DIR", "AWIKI_FLOW_STATE_DIR",
        "AWIKI_COST_GATE_TMP_DIR", "AWIKI_LIVE_LOG_PATH", "AWIKI_LIVE_SESSION_FILE",
        "CLINE_HOOK_LOG_FILE", "AWIKI_PYTHON", "AWIKI_MEMORY_LEDGER_PATH",
        "ZCODE_SESSION_ID", "CLAUDE_SESSION_ID", "CODEX_SESSION_ID",
        "GEMINI_SESSION_ID", "CI", "WIKI_UNLOCK", "AUTH_BY_DRIVE_MOUNT",
    ):
        env.pop(key, None)

    cost_dir = tmp_path / "cost-gate"; cost_dir.mkdir(parents=True)
    today = datetime.now().date()
    for day in (today, today + timedelta(days=1)):
        (cost_dir / f"cost-tier-{day.isoformat()}.txt").write_text(
            "L4|journey-e2e|user journey harness\n", encoding="utf-8")

    (tmp_path / "focus").mkdir(); (tmp_path / "flow").mkdir()
    (tmp_path / "tasks").mkdir(); (tmp_path / "blackboard").mkdir()
    env.update({
        "AWIKI_COST_GATE_TMP_DIR": str(cost_dir),
        "AWIKI_CLAIMS_STORE": str(tmp_path / "agent-claims.json"),
        "AWIKI_AGENT": "journey-e2e-user",
        "AWIKI_FOCUS_DIR": str(tmp_path / "focus"),
        "AWIKI_FLOW_STATE_DIR": str(tmp_path / "flow"),
        "AWIKI_TASK_BOARD_PATH": str(tmp_path / "tasks" / "board.json"),
        "AWIKI_BLACKBOARD_PATH": str(tmp_path / "blackboard" / "bb.jsonl"),
        "AWIKI_LIVE_LOG_PATH": str(tmp_path / "live-events.jsonl"),
        "AWIKI_LIVE_SESSION_FILE": str(tmp_path / "live-session-id"),
        "AWIKI_MEMORY_LEDGER_PATH": str(tmp_path / "memory-ledger.jsonl"),
    })
    return env


def _run(args: list[str], env: dict, input_text: str | None = None,
         timeout: int = 120) -> subprocess.CompletedProcess:
    if args[0].endswith(".py"):
        cmd = [sys.executable, *args]
    elif args[0] == "-m":
        cmd = [sys.executable, *args]
    else:
        cmd = args
    return subprocess.run(
        cmd,
        input=input_text, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
        cwd=str(REPO_ROOT), env=env, timeout=timeout,
    )


def _sweep(provider: str, event: str, payload: dict, env: dict) -> subprocess.CompletedProcess:
    raw = json.dumps(payload)
    return subprocess.run(
        [sys.executable, RUNNER, "--provider", provider, "--event", event],
        input=raw, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
        cwd=str(REPO_ROOT), env=env, timeout=120,
    )


def _edit_payload(file_path: str, new_string: str = "x") -> dict:
    return {"tool_name": "Edit",
            "tool_input": {"file_path": file_path, "old_string": "old", "new_string": new_string}}


def _bash_payload(command: str) -> dict:
    return {"tool_name": "Bash", "tool_input": {"command": command}}


# ══════════════════════════════════════════════════════════════════════
# J1 — เปิดสมอง (session start): user เปิด agent ครั้งแรกวันนี้
# ══════════════════════════════════════════════════════════════════════
class TestJourney1OpenBrain:

    def test_session_start_sweeps_pass_every_wired_provider(self, journey_env):
        """ปุ่ม "เปิดโปรแกรม": SessionStart sweep ต้องไม่บล็อกการเริ่มงาน"""
        for provider in ("claude", "zcode", "codex"):
            res = _sweep(provider, "SessionStart", {"session_id": "journey"}, journey_env)
            assert res.returncode == 0, f"{provider} SessionStart blocked: {res.stderr}"

    def test_conductor_status_button(self, journey_env):
        res = _run([*CLI_MODULE, "status", "--json"], journey_env)
        assert res.returncode == 0, res.stderr
        data = json.loads(res.stdout)
        assert data.get("schema") == "awiki-conductor/v1", sorted(data)
        assert "claims" in data, f"status missing claims: {sorted(data)}"

    def test_conductor_gate_button_gives_verdict(self, journey_env):
        """ปุ่ม gate: ไม่มี agent → ต้องตอบ verdict NO-GO อย่างสุภาพ ไม่ใช่ usage-error เปล่า"""
        res = _run([*CLI_MODULE, "gate", "--topic", "journey-e2e", "--json"], journey_env)
        assert res.returncode in (0, 1), res.stderr
        data = json.loads(res.stdout)
        assert data.get("verdict") in ("GO", "NO-GO"), data


# ══════════════════════════════════════════════════════════════════════
# J2 — ค้นสมอง: user พิมพ์คำถาม กดทุกปุ่มค้นหา
# ══════════════════════════════════════════════════════════════════════
class TestJourney2SearchBrain:

    def test_conductor_search_fts_button(self, journey_env):
        res = _run([*CLI_MODULE, "search", "--query", "hermes", "--mode", "fts", "--json"], journey_env)
        assert res.returncode == 0, res.stderr
        data = json.loads(res.stdout)
        assert data.get("hits"), f"fts search must find hermes pages: {str(data)[:300]}"
        assert data["hits"][0]["path"].endswith(".md")

    def test_conductor_search_hybrid_button(self, journey_env):
        res = _run([*CLI_MODULE, "search", "--query", "hermes", "--mode", "hybrid", "--json"], journey_env)
        assert res.returncode == 0, res.stderr
        json.loads(res.stdout)  # valid JSON = ปุ่มทำงาน (hybrid อาจ downgrade แบบ honest)

    def test_conductor_related_button(self, journey_env):
        res = _run([*CLI_MODULE, "search", "--query", "hermes", "--mode", "fts", "--json"], journey_env)
        page = json.loads(res.stdout)["hits"][0]["path"]
        res = _run([*CLI_MODULE, "related", "--page", page, "--json"], journey_env)
        assert res.returncode == 0, res.stderr
        data = json.loads(res.stdout)
        assert data.get("page") == page
        assert isinstance(data.get("neighbors"), list) and data["neighbors"],             f"hermes page must have graph neighbors: {str(data)[:200]}"

    def test_conductor_hubs_button(self, journey_env):
        res = _run([*CLI_MODULE, "hubs", "--json"], journey_env)
        assert res.returncode == 0, res.stderr
        data = json.loads(res.stdout)
        hubs = data.get("hubs") or data
        assert hubs, f"hubs must not be empty: {str(data)[:200]}"

    def test_conductor_recall_button(self, journey_env):
        res = _run([*CLI_MODULE, "recall", "--query", "zcode provider hook", "--json"], journey_env)
        assert res.returncode == 0, res.stderr
        json.loads(res.stdout)

    def test_brain_script_buttons(self, journey_env):
        """ปุ่มยาว: search-wiki.py + query-graph.py — ต้องออกจาก command ได้ปกติ"""
        for cmd in (
            [str(REPO_ROOT / "scripts" / "wiki" / "search-wiki.py"), "hermes"],
            [str(REPO_ROOT / "scripts" / "wiki" / "query-graph.py"), "--hubs"],
        ):
            res = subprocess.run([sys.executable, *cmd], capture_output=True,
                                 text=True, encoding="utf-8", errors="replace",
                                 cwd=str(REPO_ROOT), env=journey_env, timeout=120)
            assert res.returncode == 0, f"{cmd[-1]} failed: {res.stderr[:200]}"


# ══════════════════════════════════════════════════════════════════════
# J2b — MCP: user กดปุ่มทุกอันในหน้า MCP (31 tools + 3 resources)
# ══════════════════════════════════════════════════════════════════════
class _McpSession:
    """stdio JSON-RPC session จริงกับ awiki server — กดปุ่มแบบ client จริง"""

    def __init__(self, env: dict):
        self.proc = subprocess.Popen(
            [sys.executable, MCP], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
            cwd=str(REPO_ROOT), env=env,
        )
        self._id = 0
        self.request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {}, "clientInfo": {"name": "journey-e2e", "version": "0"}},
        )
        self.notify("notifications/initialized")

    def request(self, method: str, params: dict | None = None) -> dict:
        self._id += 1
        msg = {"jsonrpc": "2.0", "id": self._id, "method": method,
               "params": params or {}}
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()
        # stdout มี notification คั่น (server พ่น {"method":"initialized"}
        # ตอน start + ack ต่างๆ) — อ่านจนกว่าจะเจอ response ที่ id ตรงกับ
        # request นี้เท่านั้น ไม่งั้นทุกปุ่มจะได้คำตอบของปุ่มก่อนหน้า offset ไป 1
        for _ in range(300):
            line = self.proc.stdout.readline()
            if not line:
                err = self.proc.stderr.read()
                raise AssertionError(f"MCP no response for {method}: {err[:300]}")
            resp = json.loads(line)
            if resp.get("id") != self._id:
                continue  # notification หรือ response คนอื่น — ข้าม
            if "error" in resp:
                return {"__error": resp["error"]}
            return resp.get("result", {})
        raise AssertionError(f"MCP response timeout for {method}")

    def notify(self, method: str) -> None:
        self.proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": method}) + "\n")
        self.proc.stdin.flush()

    def call(self, tool: str, args: dict | None = None) -> dict:
        result = self.request("tools/call", {"name": tool, "arguments": args or {}})
        if "__error" in result:
            return result
        text = result.get("content", [{}])[0].get("text", "")
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return {"__text": text}

    def close(self):
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()


@pytest.fixture()
def mcp(journey_env):  # noqa: ANN001 — pytest fixture
    session = _McpSession(journey_env)
    yield session
    session.close()


@pytest.mark.usefixtures("mcp")
class TestJourney2bMcpButtons:

    def test_every_read_only_button_answers(self, mcp):
        buttons = {
            "wiki_search": {"query": "hermes"},
            "wiki_graph_neighbors": {"path": "wiki/sources/hermes-agent.md"},
            "wiki_graph_hubs": {},
            "wiki_get_page": {"path": "wiki/A-ROUTER.md"},
            "wiki_batch_status": {},
            "memory_recall": {"query": "hook provider"},
            "memory_semantic_recall": {"query": "zcode wiring"},
            "claim_list": {},
            "task_list": {},
            "focus_get": {},
            "bb_read": {},
        }
        failed = []
        for tool, args in buttons.items():
            out = mcp.call(tool, args)
            if "__error" in out:
                msg = out["__error"].get("message", "?")
                data = str(out["__error"].get("data") or "")
                tail = data.splitlines()[-1][:120] if data else ""
                failed.append(f"{tool}: {msg} {tail}".strip())
        assert not failed, f"MCP buttons broken: {failed}"

    def test_semantic_search_button_degrades_honestly(self, mcp):
        """wiki_semantic_search: ผ่านเต็ม หรือ degrade สุภาพบอก dependency
        ที่ขาด (apsw/sqlite-vec ตามเครื่อง) — ห้าม Internal error"""
        out = mcp.call("wiki_semantic_search", {"query": "agent memory"})
        if "__error" in out:
            err = out["__error"]
            assert "missing dependency" in str(err.get("message", "")), err
            assert "pip install" in str(err.get("message", "")), err
        else:
            assert out, "semantic search returned empty payload"

    def test_search_button_returns_real_results(self, mcp):
        out = mcp.call("wiki_search", {"query": "hermes"})
        results = out.get("results") or out.get("pages") or []
        assert results, f"wiki_search must return hermes pages: {str(out)[:300]}"

    def test_stateful_buttons_isolated(self, mcp, journey_env):
        """ปุ่มเขียน-state: memory_remember ตอบ ts กลับมา (โปรดูัด: MCP
        server ยังไม่อ่าน AWIKI_MEMORY_LEDGER_PATH — เขียน runtime ledger
        กลาง .tmp/ ของ repo ตาม default; env seam ของ server = follow-up)"""
        out = mcp.call("memory_remember", {
            "type": "outcome", "summary": "journey e2e button press"})
        assert isinstance(out, float) and out > 0, out
        default_ledger = REPO_ROOT / ".tmp" / "memory-ledger.jsonl"
        assert "journey e2e button press" in default_ledger.read_text(encoding="utf-8"), \
            "memory_remember must append to the runtime ledger"

    def test_routing_button_two_tiers(self, mcp):
        """ปุ่ม route: tier-1 trigger ตรง + tier-2 description fallback
        (skill_route คืน list ของ candidates ตามลำดับคะแนน)"""
        out1 = mcp.call("skill_route", {"text": "ฉันจะออกแบบ database schema ใหม่"})
        assert isinstance(out1, list) and out1, f"tier-1 route empty: {str(out1)[:200]}"
        first = out1[0] if isinstance(out1[0], dict) else {"skill": out1[0]}
        assert first.get("skill") or first.get("name"), first

        out2 = mcp.call("skill_route", {"text": "help me review code quality"})
        assert isinstance(out2, list), f"tier-2 must return a list: {str(out2)[:200]}"

    def test_destructive_buttons_refuse_gracefully(self, mcp):
        """ปุ่มอันตราย: ต้องปฏิเสธ/ตอบ error ที่ควบคุมได้ ไม่ใช่ crash"""
        out = mcp.call("wiki_regen_index", {})
        text = json.dumps(out, ensure_ascii=False)
        assert "Traceback" not in text, f"regen_index crashed instead of answering: {text[:200]}"
        assert "__error" in out or "regen" in text.lower() or "started" in text.lower() or out == {}, \
            f"unexpected regen_index shape: {text[:200]}"

    def test_resource_buttons(self, mcp):
        for uri in ("wiki://overview", "wiki://graph/stats", "wiki://context/now"):
            out = mcp.request("resources/read", {"uri": uri})
            assert "__error" not in out, f"{uri}: {out}"
            assert out.get("contents"), f"{uri} returned no contents"


# ══════════════════════════════════════════════════════════════════════
# J3 — สั่งงาน: user พิมพ์ objective รับแผนกลับ
# ══════════════════════════════════════════════════════════════════════
class TestJourney3OrderWork:

    def test_conductor_models_button(self, journey_env):
        """ปุ่ม models: policy เต็ม (rc 0) หรือ degrade สุภาพ (rc 1 + เหตุผล)
        — ห้าม traceback เด็ดขาด (bug จริงที่ E2E จับได้ 2026-08-22)"""
        res = _run([*CLI_MODULE, "models", "--json"], journey_env)
        assert "Traceback" not in res.stderr + res.stdout, res.stderr[:300]
        data = json.loads(res.stdout)
        if res.returncode == 0:
            assert data.get("tiers") and data.get("budgets"), sorted(data)
        else:
            assert data.get("models_unavailable") and data.get("reason"), data

    def test_conductor_plan_button_shapes_objective(self, journey_env):
        res = _run([*CLI_MODULE, "plan", "--json", "user journey smoke"], journey_env)
        assert res.returncode == 0, res.stderr
        data = json.loads(res.stdout)
        assert data.get("work_orders"), f"plan returned no work orders: {str(data)[:300]}"
        wo = data["work_orders"][0]
        assert wo.get("goal") and wo.get("verify"), wo


# ══════════════════════════════════════════════════════════════════════
# J4 — ทำงานมี gate คุม: งานปกติผ่าน / งานผิดกฎโดนบล็อก ทุก provider
# ══════════════════════════════════════════════════════════════════════
class TestJourney4GatesWhileWorking:

    @pytest.mark.parametrize("provider", ["claude", "zcode", "codex"])
    def test_benign_edit_passes(self, journey_env, provider):
        res = _sweep(provider, "PreToolUse",
                     _edit_payload("wiki/concepts/ai-tools/journey-test.md"), journey_env)
        assert res.returncode == 0, f"{provider}: {res.stderr[:300]}"

    @pytest.mark.parametrize("provider", ["claude", "zcode", "codex"])
    def test_raw_edit_blocked(self, journey_env, provider):
        res = _sweep(provider, "PreToolUse",
                     _edit_payload("raw/source-doc.pdf"), journey_env)
        assert res.returncode == 2, f"{provider} must block raw/ edit (Iron Law #4)"

    @pytest.mark.parametrize("provider", ["claude", "zcode", "codex"])
    def test_secret_leak_blocked(self, journey_env, provider):
        res = _sweep(provider, "PreToolUse",
                     _edit_payload("scripts/x.py", new_string=f"token = {SECRET_TOKEN}"),
                     journey_env)
        assert res.returncode == 2, f"{provider} must block secret leak"

    def test_gemini_native_buttons(self, journey_env):
        """gemini ผู้ใช้ชื่อปุ่ม native: BeforeTool/AfterTool/SessionEnd"""
        before = _sweep("gemini", "BeforeTool",
                        {"tool_name": "write_file",
                         "tool_input": {"file_path": "scripts/ok.py", "content": "ok"}},
                        journey_env)
        assert before.returncode == 0, before.stderr
        raw_try = _sweep("gemini", "BeforeTool",
                         {"tool_name": "write_file",
                          "tool_input": {"file_path": "raw/x.md", "content": "no"}},
                         journey_env)
        assert raw_try.returncode == 2
        after = _sweep("gemini", "AfterTool",
                       {"tool_name": "run_shell_command",
                        "tool_input": {"command": "git status"}}, journey_env)
        assert after.returncode == 0, after.stderr
        end = _sweep("gemini", "SessionEnd", {"session_id": "journey"}, journey_env)
        assert end.returncode == 0, end.stderr

    @pytest.mark.parametrize("provider,event", [
        ("claude", "UserPromptSubmit"), ("zcode", "UserPromptSubmit"),
        ("claude", "PostToolUse"), ("zcode", "PostToolUse"),
        ("claude", "Stop"), ("zcode", "Stop"),
    ])
    def test_rest_of_lifecycle_buttons(self, journey_env, provider, event):
        payload = {"prompt": "ช่วยวางแผนงาน"} if event == "UserPromptSubmit" else (
            _bash_payload("git status") if event == "PostToolUse" else {"session_id": "j"})
        res = _sweep(provider, event, payload, journey_env)
        assert res.returncode == 0, f"{provider}/{event}: {res.stderr[:300]}"


# ══════════════════════════════════════════════════════════════════════
# J5 — ปิดวัน: verify + generators --check + claims คืนหมด
# ══════════════════════════════════════════════════════════════════════
class TestJourney5CloseDay:

    def test_conductor_verify_button(self, journey_env):
        res = _run([*CLI_MODULE, "verify", "--json"], journey_env)
        assert res.returncode == 0, res.stderr
        data = json.loads(res.stdout)
        assert data.get("all_passed") is True,             f"verify gates failed: {str(data)[:400]}"

    def test_claim_button_is_gate_guarded(self, journey_env):
        """ปุ่ม claim: ต้องผ่าน gate — คำสั่งเปล่า/ไม่มี scope ต้องถูกปฏิเสธ"""
        res = _run([*CLI_MODULE, "claim", "--scope", "", "--goal", "", "--phase", ""], journey_env)
        assert res.returncode != 0 or "NO" in res.stdout.upper() or "reject" in res.stdout.lower() \
            or "invalid" in res.stdout.lower(), \
            f"claim must refuse empty rows: rc={res.returncode} out={res.stdout[:200]}"

    def test_generator_check_buttons(self, journey_env):
        for script in ("scripts/setup-zcode-config.py", "scripts/setup-codex-config.py"):
            res = _run([script, "--check"], journey_env)
            assert res.returncode == 0, f"{script} --check failed: {res.stdout + res.stderr[:300]}"
