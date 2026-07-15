#!/usr/bin/env python3
"""
A-Wiki Live Dashboard — SSE Server
===================================
Serves the live-dashboard.html and streams events via Server-Sent Events.

Usage:
  python3 scripts/live-dashboard/server.py          # foreground
  python3 scripts/live-dashboard/server.py --run    # foreground (explicit)

Endpoints:
  GET /              → live-dashboard.html
  GET /events        → SSE stream (tails .tmp/live-events.jsonl)
  GET /clear         → clear log file
  GET /status        → JSON status
  GET /api/models    → model config JSON
  POST /api/models   → save model config
  GET /api/keys      → key names + set/unset status (never values)
  POST /api/keys     → save one API key to .tmp/live-dashboard-keys.env
  GET /api/capabilities → capability scorecard + recommended_by_task
  GET /api/council    → Brainstorm Council rounds ({"councils": [...]})
  GET /api/council/<id> → full council transcript; 404 on unknown/invalid id

Port: 7790  (separate from render-html-preview on 7788)
"""
import json
import os
import argparse
import os
import queue
import re
import signal
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DASHBOARD_DIR = Path(__file__).resolve().parent  # scripts/live-dashboard/

# scripts/lib is not an installed package — same sys.path convention as
# tests/test_council_room.py uses to import council_room.
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))
import council_room  # noqa: E402
import pid_check  # noqa: E402

# Skills service lives next to this server file.
sys.path.insert(0, str(REPO_ROOT / "scripts" / "live-dashboard"))
import skills_service  # noqa: E402
import subagent_stats  # noqa: E402

LOG_FILE = REPO_ROOT / ".tmp" / "live-events.jsonl"
DASHBOARD_HTML = REPO_ROOT / "scripts" / "live-dashboard" / "live-dashboard.html"
DASHBOARD_HTML_FALLBACK = REPO_ROOT / "exports" / "html" / "live-dashboard.html"
MODEL_CONFIG_FILE = REPO_ROOT / ".tmp" / "model-config.json"
DASHBOARD_KEYS_FILE = REPO_ROOT / ".tmp" / "live-dashboard-keys.env"
CAPABILITY_CACHE = REPO_ROOT / ".tmp" / "model-capability-cache.json"
CAPABILITY_SCORECARD = REPO_ROOT / "wiki" / "context" / "model-capability-scores.json"
PORT = 7790
ADMIN_PASSWORD_FILE = REPO_ROOT / ".tmp" / "admin-password.hash"
AGENT_REGISTRY_FILE = REPO_ROOT / "scripts" / "live-dashboard" / "agent-registry.json"
AGENT_CONFIG_FILE = REPO_ROOT / ".tmp" / "agent-config.json"
CHAT_LOG_FILE = REPO_ROOT / ".tmp" / "chat-log.jsonl"
UPLOAD_DIR = REPO_ROOT / ".tmp" / "uploads"

# ── Run-this-skill: explicit allowlist (security) ──────────────────────────
# Only scripts in this dict can be executed via POST /api/run. Each entry
# declares whether args are expected. Default OFF: env AWIKI_DASHBOARD_ALLOW_RUN=1
# must be set, otherwise /api/run returns 403.
ALLOW_RUN_SCRIPTS = {
    "scripts/wiki/search-wiki.py": {"desc": "FTS5 wiki search", "needs_args": True},
    "scripts/wiki/query-graph.py": {"desc": "Knowledge graph query", "needs_args": False},
    "scripts/agent-preflight.py": {"desc": "Cross-platform safety check", "needs_args": False},
    "scripts/regen-skill-surfaces.py": {"desc": "Regenerate + validate skill surfaces", "needs_args": False},
    "scripts/check-privacy.py": {"desc": "Pre-publish privacy scan", "needs_args": False},
}
# Shell metacharacters that must never appear in args (injection defense).
_ARG_BLOCKLIST = re.compile(r"[;&|`$(){}!\n\r]")

PID_FILE = REPO_ROOT / ".tmp" / "live-dashboard.pid"
DAEMON_LOG = REPO_ROOT / ".tmp" / "live-dashboard.log"
IDLE_TTL_S = 1800  # 30 min idle → auto-shutdown

# task_type → capability dimension (mirrors delegate.sh::_capability_dimension)
TASK_DIMENSION = {
    "reason": "reasoning", "compare": "reasoning",
    "scan": "terminal_bench",
    "search": "speed", "lookup": "speed", "summarize": "speed",
}

DEFAULT_MODEL_CONFIG = {
    "models": [
        {
            "id": "gemini", "name": "Gemini 2.5 Flash", "enabled": True,
            "provider": "gemini", "key_env": "GEMINI_API_KEY",
            "model_id": "gemini-2.5-flash",
        },
        {
            "id": "deepseek", "name": "DeepSeek V3", "enabled": True,
            "provider": "deepseek", "key_env": "DEEPSEEK_API_KEY",
            "model_id": "deepseek-chat",
        },
        {
            "id": "openrouter", "name": "OpenRouter", "enabled": True,
            "provider": "openrouter", "key_env": "OPENROUTER_API_KEY",
        },
        {
            "id": "groq", "name": "Groq / Llama 70B", "enabled": True,
            "provider": "groq", "key_env": "GROQ_API_KEY",
            "model_id": "llama-3.3-70b-versatile",
        },
        {
            "id": "anthropic", "name": "Claude Haiku", "enabled": True,
            "provider": "anthropic", "key_env": "ANTHROPIC_API_KEY",
            "model_id": "claude-haiku-4-5",
        },
        {
            "id": "zhipu", "name": "GLM 5.2 (Z.ai)", "enabled": False,
            "provider": "zhipu", "key_env": "ZHIPU_API_KEY",
            "model_id": "glm-4.6",
            "api_url": "https://api.z.ai/api/paas/v4/chat/completions",
        },
    ]
}

_clients = []
_clients_lock = threading.Lock()
_stats = {"events_sent": 0, "clients_connected": 0, "started": time.time()}
_idle_since = time.time()  # updated in _sse connect/disconnect
_idle_lock = threading.Lock()

# ── Workflow Graph State (Step 2 — dashboard-v2) ──────────────────
_graph_nodes: dict[str, dict] = {}   # id → {id, type, label, status, color, ...}
_graph_edges: dict[tuple, dict] = {}  # (from, to, kind) → {from, to, kind, active}
_active_agents: set[str] = set()
_task_stack: list[str] = []
_graph_lock = threading.Lock()

_AGENT_COLORS = {
    "primary": "#F59E0B",
    "architect": "#06B6D4",
    "executioner": "#10B981",
    "subagent": "#8B5CF6",
    "unknown": "#F59E0B",
}

_server_ref = None  # set in __main__ so idle_watchdog can call shutdown()


# ---------------------------------------------------------------------------
# Workflow Graph Engine (Step 2 — dashboard-v2)
# ---------------------------------------------------------------------------

def _process_graph_event(evt: dict) -> None:
    """Update in-memory graph state from one event dict.
    Called by tail_log() for every line read from the event log."""
    global _graph_nodes, _graph_edges, _active_agents, _task_stack

    etype = evt.get("type", "")
    sid = evt.get("session_id", "")
    aid = evt.get("agent_id", "")
    role = evt.get("agent_role", "unknown")
    tid = evt.get("task_id")
    pid = evt.get("parent_task_id")

    with _graph_lock:
        # ── session_start ──────────────────────────────────
        if etype == "session_start" and sid:
            _graph_nodes[sid] = {
                "id": sid, "type": "session", "label": f"Session {sid[-8:]}",
                "status": "active", "color": "#F59E0B"
            }

        # ── task_start ─────────────────────────────────────
        elif etype == "task_start" and tid:
            _graph_nodes[tid] = {
                "id": tid, "type": "task", "label": f"Task {tid[-6:]}",
                "status": "active", "color": "#3B82F6",
            }
            if pid and pid.lower() not in ("none", "null", ""):
                _graph_edges[(pid, tid, "parent")] = {
                    "from": pid, "to": tid, "kind": "parent", "active": True
                }
            _task_stack.append(tid)

        # ── task_complete ──────────────────────────────────
        elif etype == "task_complete" and tid:
            if tid in _graph_nodes:
                _graph_nodes[tid]["status"] = "completed"
            if tid in _task_stack:
                _task_stack.remove(tid)

        # ── agent_spawn ────────────────────────────────────
        elif etype == "agent_spawn" and aid:
            model = evt.get("model", "")
            color = _AGENT_COLORS.get(role, _AGENT_COLORS["unknown"])
            _graph_nodes[aid] = {
                "id": aid, "type": "agent", "role": role,
                "label": f"{role.title()}",
                "status": "active", "color": color,
                "model": model,
            }
            _active_agents.add(aid)
            if tid and tid in _graph_nodes:
                _graph_edges[(tid, aid, "assigns")] = {
                    "from": tid, "to": aid, "kind": "assigns", "active": True
                }

        # ── agent_done ─────────────────────────────────────
        elif etype == "agent_done" and aid:
            if aid in _graph_nodes:
                _graph_nodes[aid]["status"] = "completed"
            _active_agents.discard(aid)

        # ── delegate_start/done/fail → derived agent activity ──
        # delegate.sh emits delegate_* (not agent_spawn/done). Derive per-model
        # agent nodes so parallel delegations show in the graph + parallel_count.
        elif etype == "delegate_start":
            model = evt.get("model", "") or "unknown"
            did = f"agent:{model}"
            label = model.split("/")[0].split("(")[0][:24] or "delegate"
            _graph_nodes[did] = {
                "id": did, "type": "agent", "role": "executioner",
                "label": label, "status": "active",
                "color": _AGENT_COLORS["executioner"], "model": model,
                "task": evt.get("task", ""),
            }
            _active_agents.add(did)
        elif etype in ("delegate_done", "delegate_fail"):
            model = evt.get("model", "") or "unknown"
            did = f"agent:{model}"
            if did in _graph_nodes:
                _graph_nodes[did]["status"] = "completed" if etype == "delegate_done" else "failed"
                if etype == "delegate_done" and evt.get("duration_ms"):
                    _graph_nodes[did]["duration_ms"] = evt.get("duration_ms")
            _active_agents.discard(did)

        # ── hook_check / tool events → tool clusters ───────
        elif etype == "hook_check":
            tool = evt.get("tool", "")
            if tool:
                cluster_id = f"tool_{tool}"
                if cluster_id not in _graph_nodes:
                    _graph_nodes[cluster_id] = {
                        "id": cluster_id, "type": "tool_cluster",
                        "label": tool, "count": 0, "color": "#6B7280"
                    }
                _graph_nodes[cluster_id]["count"] += 1
                if aid and aid in _graph_nodes:
                    _graph_edges[(aid, cluster_id, "uses")] = {
                        "from": aid, "to": cluster_id, "kind": "uses", "active": True
                    }


def _graph_snapshot() -> dict:
    """Return current graph state as {nodes, edges, parallel_count, active_agents}."""
    with _graph_lock:
        nodes = list(_graph_nodes.values())
        edges = list(_graph_edges.values())
        parallel_count = len(_active_agents)
        active = list(_active_agents)
    return {
        "nodes": nodes,
        "edges": edges,
        "parallel_count": parallel_count,
        "active_agents": active,
    }


# ---------------------------------------------------------------------------
# Daemon helpers
# ---------------------------------------------------------------------------

def is_already_running() -> bool:
    """Return True if a live-dashboard.pid process is still alive.

    Uses pid_check.is_pid_alive() rather than a bare os.kill(pid, 0). On
    Windows, CPython special-cases signal 0 to GenerateConsoleCtrlEvent()
    rather than TerminateProcess() (confirmed on this machine — it does not
    instantly kill the target), but that event's delivery depends on
    console/process-group configuration this caller doesn't control and can
    raise OSError for a process in a different process group (exactly the
    case here: server.py's daemonize() spawns with
    DETACHED_PROCESS|CREATE_NEW_PROCESS_GROUP). It's the wrong primitive for
    "is this PID alive" regardless of the instant-kill question — see
    scripts/lib/pid_check.py's docstring for the full write-up.
    is_pid_alive() is well-defined and safe on both platforms.
    """
    if not PID_FILE.exists():
        return False
    try:
        pid = int(PID_FILE.read_text().strip())
    except ValueError:
        PID_FILE.unlink(missing_ok=True)
        return False
    if pid_check.is_pid_alive(pid):
        return True
    PID_FILE.unlink(missing_ok=True)
    return False


def _is_port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def daemonize() -> None:
    """Detach into a background daemon; write PID file; redirect stdio.

    Cross-platform: POSIX uses the classic double-fork. Windows has no
    os.fork — instead the parent re-spawns this script as a fully detached
    child (DETACHED_PROCESS) marked with _AWIKI_DASH_CHILD=1 and exits; the
    child (handled in __main__) claims the PID and serves.
    """
    DAEMON_LOG.parent.mkdir(exist_ok=True)

    if os.name == "nt":
        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        CREATE_NO_WINDOW = 0x08000000
        argv = [sys.executable, os.path.abspath(__file__), "--daemonize"]
        if "--no-browser" in sys.argv:
            argv.append("--no-browser")
        logf = open(str(DAEMON_LOG), "a", encoding="utf-8")
        env = dict(os.environ, _AWIKI_DASH_CHILD="1")
        proc = subprocess.Popen(
            argv, stdin=subprocess.DEVNULL, stdout=logf, stderr=logf,
            creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW,
            env=env, close_fds=True, cwd=str(REPO_ROOT),
        )
        PID_FILE.write_text(str(proc.pid))
        sys.exit(0)

    # POSIX double-fork
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        sys.stderr.write(f"fork #1 failed: {e}\n")
        sys.exit(1)

    os.setsid()
    os.umask(0)

    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        sys.stderr.write(f"fork #2 failed: {e}\n")
        sys.exit(1)

    sys.stdout.flush()
    sys.stderr.flush()
    with open(os.devnull, "r") as devnull:
        os.dup2(devnull.fileno(), sys.stdin.fileno())
    with open(str(DAEMON_LOG), "a") as logf:
        os.dup2(logf.fileno(), sys.stdout.fileno())
        os.dup2(logf.fileno(), sys.stderr.fileno())

    PID_FILE.write_text(str(os.getpid()))


def idle_watchdog(server) -> None:
    """Shut down server after IDLE_TTL_S seconds with no SSE clients."""
    global _idle_since
    while True:
        time.sleep(60)
        with _idle_lock:
            idle = _idle_since
        if idle is not None and (time.time() - idle) >= IDLE_TTL_S:
            server.shutdown()
            try:
                PID_FILE.unlink(missing_ok=True)
            except Exception:
                pass
            return


def broadcast(line):
    _stats["events_sent"] += 1
    with _clients_lock:
        dead = []
        for q in _clients:
            try:
                q.put_nowait(line)
            except queue.Full:
                dead.append(q)
        for q in dead:
            _clients.remove(q)


# ---------------------------------------------------------------------------
# CHUNK GG — registry push: detect skills-registry.json mtime change and
# broadcast an SSE event so dashboards auto-refresh without polling.
# Helpers are pure + module-level so tests can exercise them directly.
# ---------------------------------------------------------------------------
_registry_last_mtime = 0.0


def build_registry_event() -> str:
    """Build the SSE payload for a registry change. Pure + JSON-safe."""
    return json.dumps({"type": "registry_update", "ts": time.time()},
                      ensure_ascii=False)


def check_registry_changed() -> bool:
    """Return True once when skills-registry.json mtime advances since the
    last call, then False until it changes again. Seeds on the first call.
    """
    global _registry_last_mtime
    try:
        mtime = skills_service.REGISTRY_FILE.stat().st_mtime
    except OSError:
        return False
    if _registry_last_mtime == 0.0:
        _registry_last_mtime = mtime
        return False
    if mtime != _registry_last_mtime:
        _registry_last_mtime = mtime
        return True
    return False


def registry_watchdog():
    """Background thread: poll registry mtime every 2s, broadcast on change."""
    while True:
        try:
            if check_registry_changed():
                broadcast(build_registry_event())
        except Exception:
            pass
        time.sleep(2.0)


def tail_log():
    """Poll log file every 100ms for new lines and broadcast to all SSE clients."""
    pos = 0
    while True:
        try:
            if LOG_FILE.exists():
                size = LOG_FILE.stat().st_size
                if size < pos:
                    pos = 0
                with open(LOG_FILE, "r", encoding="utf-8") as f:
                    f.seek(pos)
                    lines = f.readlines()
                    pos = f.tell()
                for line in lines:
                    line = line.strip()
                    if line:
                        broadcast(line)
                        # Step 2 — feed graph engine
                        try:
                            evt = json.loads(line)
                            _process_graph_event(evt)
                            # Broadcast graph delta to SSE clients
                            snapshot = json.dumps(
                                {"type": "graph_update", **_graph_snapshot()},
                                ensure_ascii=False
                            )
                            broadcast(snapshot)
                        except Exception:
                            pass
        except Exception:
            pass
        time.sleep(0.1)


def _load_model_config():
    try:
        if MODEL_CONFIG_FILE.exists():
            data = json.loads(MODEL_CONFIG_FILE.read_text("utf-8"))
            saved_ids = {m["id"] for m in data.get("models", [])}
            for dm in DEFAULT_MODEL_CONFIG["models"]:
                if dm["id"] not in saved_ids:
                    data.setdefault("models", []).append(dict(dm))
            return data
    except Exception:
        pass
    import copy
    return copy.deepcopy(DEFAULT_MODEL_CONFIG)


def _save_model_config(data):
    MODEL_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    MODEL_CONFIG_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")


def _load_capabilities():
    """Load capability scorecard: cache if present, else committed scorecard."""
    for path in (CAPABILITY_CACHE, CAPABILITY_SCORECARD):
        try:
            if path.exists():
                return json.loads(path.read_text("utf-8"))
        except Exception:
            continue
    return {"families": {}, "dimensions": [], "neutral_default": 50}


def _family_for_model(families, model):
    """Match a model config entry to a capability family via match substrings."""
    hay = " ".join(str(model.get(k, "")) for k in ("id", "model_id", "name", "provider")).lower()
    for key, fam in families.items():
        if any(s in hay for s in fam.get("match", [])):
            return key, fam
    return None, None


def _recommended_by_task():
    """For each task_type, the best-capability ENABLED model (excludes disabled)."""
    caps = _load_capabilities()
    families = caps.get("families", {})
    neutral = caps.get("neutral_default", 50)
    cfg = _load_model_config()
    enabled = [m for m in cfg.get("models", []) if m.get("enabled", True)]

    rec = {}
    for task, dim in TASK_DIMENSION.items():
        best, best_score = None, -1
        for m in enabled:
            _, fam = _family_for_model(families, m)
            score = (fam or {}).get(dim, neutral)
            if score > best_score:
                best, best_score = m, score
        if best is not None:
            rec[task] = {"id": best["id"], "name": best.get("name", best["id"]),
                         "dimension": dim, "score": best_score}
    return rec


def _read_keys_status():
    """Return list of {name, set: bool} — never the actual values."""
    cfg = _load_model_config()
    known = {}
    for m in cfg.get("models", []):
        k = m.get("key_env")
        if k:
            known[k] = bool(os.environ.get(k))
    if DASHBOARD_KEYS_FILE.exists():
        for line in DASHBOARD_KEYS_FILE.read_text("utf-8").splitlines():
            line = line.strip()
            if line.startswith("export "):
                line = line[7:]
            if "=" in line:
                k = line.split("=", 1)[0].strip()
                if k:
                    known[k] = True
    return [{"name": k, "set": v} for k, v in known.items()]


def _save_key(key_name, key_value):
    """Append/update a key in live-dashboard-keys.env."""
    DASHBOARD_KEYS_FILE.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if DASHBOARD_KEYS_FILE.exists():
        existing = DASHBOARD_KEYS_FILE.read_text("utf-8").splitlines()
    new_line = f'export {key_name}="{key_value}"'
    replaced = False
    result = []
    for line in existing:
        norm = line.strip()
        if norm.startswith("export "):
            norm = norm[7:]
        if norm.startswith(f"{key_name}="):
            result.append(new_line)
            replaced = True
        else:
            result.append(line)
    if not replaced:
        result.append(new_line)
    DASHBOARD_KEYS_FILE.write_text("\n".join(result) + "\n", "utf-8")
    _try_write_to_drive_secrets(key_name, key_value)


def _try_write_to_drive_secrets(key_name, key_value):
    """Best-effort: also write key to drive/.secrets if drive/ is mounted."""
    try:
        drive = REPO_ROOT / "drive"
        if not drive.exists():
            return
        secrets_file = drive / ".secrets"
        existing = []
        if secrets_file.exists():
            existing = secrets_file.read_text("utf-8").splitlines()
        new_line = f'{key_name}="{key_value}"'
        replaced = False
        result = []
        for line in existing:
            if line.strip().startswith(f"{key_name}="):
                result.append(new_line)
                replaced = True
            else:
                result.append(line)
        if not replaced:
            result.append(new_line)
        secrets_file.write_text("\n".join(result) + "\n", "utf-8")
    except Exception:
        pass


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/events":
            self._sse()
        elif path in ("/", "/dashboard"):
            self._serve_html()
        elif path == "/sw.js":
            self._serve_static_file("sw.js", "application/javascript")
        elif path == "/manifest.json":
            self._serve_static_file("manifest.json", "application/manifest+json")
        elif path == "/clear":
            self._clear_log()
        elif path == "/status":
            self._status()
        elif path == "/api/models":
            self._api_models_get()
        elif path == "/api/keys":
            self._api_keys_get()
        elif path == "/api/capabilities":
            self._api_capabilities_get()
        elif path == "/api/graph":
            self._json_response(_graph_snapshot())
        elif path == "/api/council":
            self._api_council_get()
        elif path.startswith("/api/council/"):
            self._api_council_detail_get(path[len("/api/council/"):])
        elif path == "/api/admin/status":
            self._api_admin_status()
        elif path == "/api/agents":
            self._api_agents_get()
        elif path == "/api/skills":
            self._api_skills_list()
        elif path == "/api/skills/agents":
            self._json_response(skills_service.agent_overview())
        elif path == "/api/skills/graph":
            self._api_skills_graph()
        elif path == "/api/skills/recommend":
            self._api_skills_recommend()
        elif path == "/api/skills/cycles":
            self._api_skills_cycles()
        elif path == "/api/skills/matrix":
            self._api_skills_matrix()
        elif path.startswith("/api/skills/"):
            self._api_skills_detail(path[len("/api/skills/"):])
        elif path == "/api/walkthroughs":
            self._api_walkthroughs_list()
        elif path.startswith("/api/walkthroughs/"):
            self._api_walkthroughs_detail(path[len("/api/walkthroughs/"):])
        elif path == "/api/coverage":
            try:
                from urllib.parse import parse_qs
                qs = self.path.split("?", 1)[1] if "?" in self.path else ""
                params = parse_qs(qs)
                compare = params.get("compare", [None])[0]
                self._json_response(skills_service.coverage_stats(compare=compare))
            except Exception as e:
                self._json_response({"error": str(e)}, 500)
        elif path == "/api/subagents/stats":
            try:
                from urllib.parse import parse_qs
                qs = self.path.split("?", 1)[1] if "?" in self.path else ""
                params = parse_qs(qs)
                since_raw = params.get("since", ["0"])[0]
                try:
                    window = int(since_raw)
                except ValueError:
                    # accept '24h' / '30m' forms too
                    v = since_raw.strip().lower()
                    mult = 3600 if v.endswith("h") else 60 if v.endswith("m") else 1
                    window = int(float(v.rstrip("hms")) * mult)
                self._json_response(subagent_stats.aggregate(window_seconds=window))
            except Exception as e:
                self._json_response({"error": str(e)}, 500)
        elif path == "/api/run/allowlist":
            self._json_response({
                "enabled": os.environ.get("AWIKI_DASHBOARD_ALLOW_RUN", "0") == "1",
                "scripts": ALLOW_RUN_SCRIPTS,
            })
        elif path.startswith("/api/uploads/"):
            self._serve_upload(path)
        else:
            self.send_error(404, "Not found")

    def do_POST(self):
        path = self.path.split("?")[0]
        if path == "/api/models":
            self._api_models_post()
        elif path == "/api/keys":
            self._api_keys_post()
        elif path == "/api/admin/auth":
            self._api_admin_auth()
        elif path == "/api/agents":
            self._api_agents_post()
        elif path == "/api/agents/reorder":
            self._api_agents_reorder()
        elif path == "/api/chat":
            self._api_chat_post()
        elif path == "/api/upload":
            self._api_upload_post()
        elif path == "/api/run":
            self._api_run_post()
        elif path.startswith("/api/skills/") and path.endswith("/edit"):
            self._api_skills_edit(path[len("/api/skills/"):-len("/edit")])
        else:
            self.send_error(404, "Not found")

    def _read_body(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            return json.loads(body)
        except Exception:
            return {}

    def _json_response(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _api_models_get(self):
        self._json_response(_load_model_config())

    def _api_models_post(self):
        data = self._read_body()
        if not isinstance(data, dict) or "models" not in data:
            self._json_response({"error": "body must be {models:[...]}"}, 400)
            return
        try:
            _save_model_config(data)
            broadcast(json.dumps({"ts": round(time.time(), 3), "type": "config_update"}))
            self._json_response({"ok": True})
        except Exception as e:
            self._json_response({"error": str(e)}, 500)

    def _api_keys_get(self):
        self._json_response({"keys": _read_keys_status()})

    def _api_capabilities_get(self):
        caps = _load_capabilities()
        caps = dict(caps)
        caps["recommended_by_task"] = _recommended_by_task()
        self._json_response(caps)

    # ── Brainstorm Council (Live Dashboard "Council" pane) ──────
    def _api_council_get(self):
        try:
            self._json_response({"councils": council_room.list_councils()})
        except Exception as e:
            self._json_response({"error": str(e)}, 500)

    def _api_council_detail_get(self, council_id):
        try:
            transcript = council_room.load_council(council_id)
        except ValueError as e:
            # covers both malformed/path-traversal ids and unknown ids —
            # council_room validates the id against COUNCIL_ID_RE before
            # touching the filesystem (see council_room._council_path).
            self._json_response({"error": str(e)}, 404)
            return
        except Exception as e:
            self._json_response({"error": str(e)}, 500)
            return
        self._json_response(transcript)

    def _api_keys_post(self):
        data = self._read_body()
        key_name = data.get("key_name", "").strip().upper()
        key_value = data.get("key_value", "").strip()
        if not key_name or not key_value:
            self._json_response({"error": "key_name and key_value required"}, 400)
            return
        if not all(c.isalnum() or c == "_" for c in key_name):
            self._json_response({"error": "invalid key_name"}, 400)
            return
        try:
            _save_key(key_name, key_value)
            os.environ[key_name] = key_value
            self._json_response({"ok": True})
        except Exception as e:
            self._json_response({"error": str(e)}, 500)

    def _api_run_post(self):
        """POST /api/run — execute an allowlisted script.

        Body: {"script": "scripts/wiki/search-wiki.py", "args": ["MQTT"]}
        Returns: {"ok": bool, "stdout": str, "stderr": str, "exit_code": int,
                  "duration_ms": int}

        Security:
          - Env AWIKI_DASHBOARD_ALLOW_RUN=1 required (default OFF)
          - Script must be in ALLOW_RUN_SCRIPTS dict (explicit allowlist)
          - Args checked against shell-metachar blocklist
          - subprocess.run with cwd=REPO_ROOT, timeout=30s, no shell=True
        """
        # Guard 1: feature must be explicitly enabled.
        if os.environ.get("AWIKI_DASHBOARD_ALLOW_RUN", "0") != "1":
            self._json_response({"error": "Run feature disabled. Set AWIKI_DASHBOARD_ALLOW_RUN=1 to enable."}, 403)
            return
        data = self._read_body()
        script = (data.get("script") or "").strip()
        args = data.get("args") or []
        if not script:
            self._json_response({"error": "script required"}, 400)
            return
        # Guard 2: allowlist check.
        if script not in ALLOW_RUN_SCRIPTS:
            self._json_response({"error": f"script not in allowlist: {script}"}, 403)
            return
        meta = ALLOW_RUN_SCRIPTS[script]
        # Guard 3: if script doesn't take args but user sent some, ignore them.
        if not meta.get("needs_args"):
            args = []
        # Guard 4: args must be strings, no shell metacharacters.
        if not isinstance(args, list):
            self._json_response({"error": "args must be a list"}, 400)
            return
        clean_args = []
        for a in args:
            if not isinstance(a, str):
                self._json_response({"error": "args must be strings"}, 400)
                return
            if _ARG_BLOCKLIST.search(a):
                self._json_response({"error": f"arg contains blocked char: {a!r}"}, 400)
                return
            clean_args.append(a)
        # Guard 5: script path must resolve inside REPO_ROOT (no ../ escape).
        script_path = (REPO_ROOT / script).resolve()
        try:
            script_path.relative_to(REPO_ROOT.resolve())
        except ValueError:
            self._json_response({"error": "script path escapes repo root"}, 403)
            return
        if not script_path.is_file():
            self._json_response({"error": f"script not found: {script}"}, 404)
            return
        # Execute: no shell=True, cwd=REPO_ROOT, 30s timeout.
        cmd = [sys.executable, str(script_path)] + clean_args
        t0 = time.time()
        try:
            result = subprocess.run(
                cmd, cwd=str(REPO_ROOT), capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=30,
            )
            duration_ms = int((time.time() - t0) * 1000)
            self._json_response({
                "ok": result.returncode == 0,
                "stdout": result.stdout[-8000:],  # cap output size
                "stderr": result.stderr[-4000:],
                "exit_code": result.returncode,
                "duration_ms": duration_ms,
                "script": script,
                "args": clean_args,
            })
        except subprocess.TimeoutExpired:
            self._json_response({"error": "script timed out (30s)", "script": script}, 504)
        except Exception as e:
            self._json_response({"error": str(e)}, 500)

    def _sse(self):
        global _idle_since
        q = queue.Queue(maxsize=200)
        with _clients_lock:
            _clients.append(q)
            _stats["clients_connected"] = len(_clients)
        with _idle_lock:
            _idle_since = None  # active client → not idle

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self._cors()
        self.end_headers()

        try:
            if LOG_FILE.exists():
                lines = LOG_FILE.read_text("utf-8").strip().splitlines()
                for line in lines[-150:]:
                    if line.strip():
                        self.wfile.write(f"data: {line}\n\n".encode())
                if lines:
                    self.wfile.write(b"data: {\"type\":\"backlog_complete\"}\n\n")
                self.wfile.flush()

            while True:
                try:
                    data = q.get(timeout=20)
                    self.wfile.write(f"data: {data}\n\n".encode())
                    self.wfile.flush()
                except queue.Empty:
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            with _clients_lock:
                if q in _clients:
                    _clients.remove(q)
                _stats["clients_connected"] = len(_clients)
                remaining = len(_clients)
            with _idle_lock:
                if remaining == 0:
                    _idle_since = time.time()  # start idle countdown

    # ── Admin Auth ────────────────────────────────────────────
    def _api_admin_status(self):
        has_pass = ADMIN_PASSWORD_FILE.exists()
        self._json_response({"password_set": has_pass, "free_only": not has_pass})

    def _api_admin_auth(self):
        data = self._read_body()
        pw = data.get("password", "")
        if not pw or not ADMIN_PASSWORD_FILE.exists():
            self._json_response({"ok": False, "error": "No password set or empty"}, 401)
            return
        stored = ADMIN_PASSWORD_FILE.read_text().strip()
        if ":" in stored:
            salt, hash_val = stored.split(":", 1)
            import hashlib
            if hashlib.sha256((salt + pw).encode()).hexdigest() == hash_val:
                self._json_response({"ok": True, "token": "session-" + salt[:8]})
                return
        self._json_response({"ok": False, "error": "Invalid password"}, 401)

    # ── Agent Registry ────────────────────────────────────────
    def _api_agents_get(self):
        registry = {}
        if AGENT_REGISTRY_FILE.exists():
            try:
                registry = json.loads(AGENT_REGISTRY_FILE.read_text())
            except Exception:
                pass
        config = {}
        if AGENT_CONFIG_FILE.exists():
            try:
                config = json.loads(AGENT_CONFIG_FILE.read_text())
            except Exception:
                pass
        # Merge skill counts from the skills registry so the Agents panel can
        # show "this agent can see N skills" alongside its model config.
        try:
            overview = skills_service.agent_overview()
            skill_counts = overview.get("skill_counts", {})
        except Exception:
            skill_counts = {}
        self._json_response({
            "registry": registry, "config": config,
            "skill_counts": skill_counts,
        })

    # ── Skills (Live Dashboard "Skills" tab) ─────────────────
    def _api_skills_list(self):
        # Parse query string from self.path (may contain ?agent=...&q=...)
        qs = self.path.split("?", 1)[1] if "?" in self.path else ""
        try:
            payload = skills_service.list_skills(qs)
            self._json_response(payload)
        except Exception as e:
            self._json_response({"error": str(e)}, 500)

    def _api_skills_detail(self, name: str):
        # Guard against path traversal — skill names are kebab-case identifiers.
        if "/" in name or ".." in name or not name:
            self._json_response({"error": "invalid skill name"}, 400)
            return
        try:
            skill = skills_service.get_skill(name)
            if skill is None:
                self._json_response({"error": f"skill '{name}' not found"}, 404)
                return
            # Lazy changelog loading via ?changelog=1
            from urllib.parse import parse_qs
            qs = self.path.split("?", 1)[1] if "?" in self.path else ""
            params = parse_qs(qs)
            if params.get("changelog", ["0"])[0] in ("1", "true", "yes"):
                skill["history"] = skills_service.skill_history(name, include_changelog=True)
            self._json_response(skill)
        except Exception as e:
            self._json_response({"error": str(e)}, 500)

    def _api_skills_graph(self):
        """GET /api/skills/graph?domain=&phase=&all=1 — skill relationship graph for vis-network."""
        from urllib.parse import parse_qs
        qs = self.path.split("?", 1)[1] if "?" in self.path else ""
        params = parse_qs(qs)
        try:
            payload = skills_service.skill_graph(
                domain=params.get("domain", [None])[0],
                phase=params.get("phase", [None])[0],
                all_skills=params.get("all", ["0"])[0] in ("1", "true", "yes"),
                limit=int(params.get("limit", ["500"])[0]),
            )
            self._json_response(payload)
        except Exception as e:
            self._json_response({"error": str(e)}, 500)

    def _api_skills_cycles(self):
        """GET /api/skills/cycles — detect circular dependencies in the skill graph."""
        try:
            g = skills_service.skill_graph(all_skills=True, limit=500)
            result = skills_service.detect_cycles(g.get("edges", []))
            self._json_response(result)
        except Exception as e:
            self._json_response({"error": str(e)}, 500)

    def _api_skills_matrix(self):
        """GET /api/skills/matrix — skills × agents visibility matrix."""
        try:
            self._json_response(skills_service.agent_skill_matrix())
        except Exception as e:
            self._json_response({"error": str(e)}, 500)

    def _api_skills_recommend(self):
        """GET /api/skills/recommend?q=<text>&limit=5 — text-based skill recommendation."""
        from urllib.parse import parse_qs
        qs = self.path.split("?", 1)[1] if "?" in self.path else ""
        params = parse_qs(qs)
        try:
            payload = skills_service.recommend_skills(
                query=params.get("q", [""])[0],
                limit=int(params.get("limit", ["5"])[0]),
            )
            self._json_response(payload)
        except Exception as e:
            self._json_response({"error": str(e)}, 500)

    def _api_skills_edit(self, name: str):
        """POST /api/skills/<name>/edit — inline editor write-back.

        Body: {"field": "th_description", "value": "..."}
        Security: field allowlist enforced in update_skill_field().
        """
        # Guard against path traversal.
        if "/" in name or ".." in name or not name:
            self._json_response({"ok": False, "error": "invalid skill name"}, 400)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length > 3000:
                self._json_response({"ok": False, "error": "request too large"}, 413)
                return
            raw = self.rfile.read(length).decode("utf-8") if length else "{}"
            body = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            self._json_response({"ok": False, "error": f"invalid JSON: {e}"}, 400)
            return
        field = body.get("field", "")
        value = body.get("value", "")
        result = skills_service.update_skill_field(name, field, value)
        if result["ok"]:
            self._json_response(result)
        else:
            self._json_response(result, 400)

    # ── Walkthroughs (multi-skill flow templates) ──────────────
    def _api_walkthroughs_list(self):
        """Return all walkthrough flows (without _meta) — title, summary, level, duration, step count."""
        try:
            data = self._load_walkthroughs()
            flows = []
            for key, flow in data.items():
                if key == "_meta":
                    continue
                flows.append({
                    "id": key,
                    "title_th": flow.get("title_th", key),
                    "summary_th": flow.get("summary_th", ""),
                    "level_th": flow.get("level_th", ""),
                    "duration_th": flow.get("duration_th", ""),
                    "step_count": len(flow.get("steps", [])),
                    "difficulty": skills_service.walkthrough_difficulty(flow),
                })
            self._json_response({"flows": flows, "total": len(flows)})
        except Exception as e:
            self._json_response({"error": str(e)}, 500)

    def _api_walkthroughs_detail(self, flow_id: str):
        """Return one walkthrough flow with full step details + resolved skill metadata."""
        if "/" in flow_id or ".." in flow_id or not flow_id:
            self._json_response({"error": "invalid flow id"}, 400)
            return
        try:
            data = self._load_walkthroughs()
            flow = data.get(flow_id)
            if flow is None or flow_id == "_meta":
                self._json_response({"error": f"flow '{flow_id}' not found"}, 404)
                return
            # Resolve each step's skill metadata so the client doesn't need a
            # second round-trip per step.
            steps_resolved = []
            for step in flow.get("steps", []):
                skill = skills_service.get_skill(step["skill"])
                steps_resolved.append({
                    "skill": step["skill"],
                    "label_th": step.get("label_th", ""),
                    "icon": step.get("icon", "🔧"),
                    "skill_th_description": (skill or {}).get("th_description", ""),
                    "skill_invocation": (skill or {}).get("invocation", "manual"),
                })
            self._json_response({
                "id": flow_id,
                "title_th": flow.get("title_th", flow_id),
                "summary_th": flow.get("summary_th", ""),
                "level_th": flow.get("level_th", ""),
                "duration_th": flow.get("duration_th", ""),
                "difficulty": skills_service.walkthrough_difficulty(flow),
                "steps": steps_resolved,
            })
        except Exception as e:
            self._json_response({"error": str(e)}, 500)

    def _load_walkthroughs(self) -> dict:
        """Lazy-load skill-walkthroughs.json. mtime-cached so edits show up without restart."""
        import os
        path = DASHBOARD_DIR / "skill-walkthroughs.json"
        mtime = os.path.getmtime(path) if path.exists() else 0
        cache = getattr(self, "_walkthroughs_cache", None)
        cache_mtime = getattr(self, "_walkthroughs_mtime", 0)
        if cache is None or mtime != cache_mtime:
            with open(path, "r", encoding="utf-8") as f:
                cache = json.load(f)
            self._walkthroughs_cache = cache
            self._walkthroughs_mtime = mtime
        return cache

    def _api_agents_post(self):
        data = self._read_body()
        try:
            AGENT_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            AGENT_CONFIG_FILE.write_text(json.dumps(data, indent=2))
            self._json_response({"ok": True})
        except Exception as e:
            self._json_response({"error": str(e)}, 500)

    def _api_agents_reorder(self):
        data = self._read_body()
        order = data.get("order", [])
        try:
            existing = {}
            if AGENT_CONFIG_FILE.exists():
                existing = json.loads(AGENT_CONFIG_FILE.read_text())
            existing["agent_order"] = order
            AGENT_CONFIG_FILE.write_text(json.dumps(existing, indent=2))
            self._json_response({"ok": True})
        except Exception as e:
            self._json_response({"error": str(e)}, 500)

    # -- Chat --
    def _api_chat_post(self):
        data = self._read_body()
        message = data.get("message", "").strip()
        if not message:
            self._json_response({"error": "message required"}, 400)
            return

        # Log incoming message
        evt = {"ts": round(time.time(), 3), "type": "chat_message", "message": message[:4000], "from": data.get("from", "dashboard")}
        try:
            CHAT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CHAT_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(evt, ensure_ascii=False) + "\n")
            broadcast(json.dumps(evt, ensure_ascii=False))
        except Exception:
            pass

        # Call Hermes API
        api_key = os.environ.get("API_SERVER_KEY", "")
        if not api_key:
            self._json_response({"error": "API_SERVER_KEY not set", "response": "⚠️ API key not configured"}, 500)
            return

        try:
            import urllib.request
            hermes_payload = json.dumps({
                "model": "deepseek-v4-pro",
                "messages": [{"role": "user", "content": message}],
                "max_tokens": 2000
            }).encode("utf-8")
            req = urllib.request.Request(
                "http://127.0.0.1:8501/v1/chat/completions",
                data=hermes_payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            reply = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not reply:
                reply = json.dumps(result, ensure_ascii=False)
        except Exception as e:
            reply = f"❌ Hermes API error: {e}"

        self._json_response({"ok": True, "response": reply})

    # -- Upload --
    def _api_upload_post(self):
        ctype = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in ctype:
            self._json_response({"error": "multipart/form-data required"}, 400)
            return
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        boundary = ctype.split("boundary=")[1].strip()
        parts = body.split(b"--" + boundary.encode())
        for part in parts:
            if b"filename=" in part:
                header, data = part.split(b"\r\n\r\n", 1)
                data = data.rsplit(b"\r\n--", 1)[0]
                fname = "upload_" + str(int(time.time()))
                for line in header.decode(errors="ignore").split("\r\n"):
                    if "filename=" in line:
                        fn = line.split("filename=")[1].strip(chr(34))
                        if fn:
                            fname = fn
                UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
                dest = UPLOAD_DIR / fname
                dest.write_bytes(data)
                evt = {"ts": round(time.time(), 3), "type": "file_uploaded", "filename": fname, "size": len(data), "path": str(dest.relative_to(REPO_ROOT))}
                broadcast(json.dumps(evt, ensure_ascii=False))
                self._json_response({"ok": True, "filename": fname, "size": len(data)})
                return
        self._json_response({"error": "no file found"}, 400)

    def _serve_upload(self, path):
        fname = path.split("/api/uploads/", 1)[1]
        if ".." in fname or "/" in fname:
            self.send_error(403, "Invalid path")
            return
        fpath = UPLOAD_DIR / fname
        if not fpath.exists():
            self.send_error(404, "Not found")
            return
        fc = fpath.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(fc)))
        self._cors()
        self.end_headers()
        self.wfile.write(fc)

    def _serve_html(self):
        html_path = DASHBOARD_HTML if DASHBOARD_HTML.exists() else DASHBOARD_HTML_FALLBACK
        if html_path.exists():
            content = html_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Dashboard HTML not found. Check exports/html/ or scripts/live-dashboard/")

    def _serve_static_file(self, filename: str, content_type: str):
        """Serve a static file from the dashboard directory (sw.js, manifest.json)."""
        file_path = DASHBOARD_DIR / filename
        if file_path.is_file():
            content = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(404)
            self.end_headers()

    def _clear_log(self):
        try:
            LOG_FILE.write_text("", encoding="utf-8")
            broadcast('{"type":"log_cleared","ts":' + str(round(time.time(), 3)) + '}')
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self._cors()
            self.end_headers()
            self.wfile.write(b"cleared")
        except Exception as e:
            self.send_error(500, str(e))

    def _status(self):
        data = json.dumps({
            "status": "running",
            "port": PORT,
            "clients": _stats["clients_connected"],
            "events_sent": _stats["events_sent"],
            "log_file": str(LOG_FILE),
            "log_exists": LOG_FILE.exists(),
            "uptime_s": round(time.time() - _stats["started"]),
        }).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self._cors()
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="A-Wiki Live Dashboard server")
    ap.add_argument("--daemonize", action="store_true",
                    help="Detach and run as background daemon (writes PID to .tmp/live-dashboard.pid)")
    ap.add_argument("--no-browser", action="store_true",
                    help="Skip opening browser tab after daemonize")
    ap.add_argument("--run", action="store_true", help="Foreground mode (default; explicit flag)")
    args = ap.parse_args()

    if args.daemonize:
        # On Windows the detached child re-enters with this marker — it must
        # skip the guard + re-spawn and go straight to serving.
        if os.environ.get("_AWIKI_DASH_CHILD") == "1":
            PID_FILE.write_text(str(os.getpid()))
        else:
            if is_already_running():
                sys.exit(0)  # Already running — idempotent
            if not _is_port_free(PORT):
                sys.stderr.write(
                    f"⚠️  Port {PORT} is busy (non-dashboard process). "
                    f"Kill it or use a different port.\n"
                )
                sys.exit(1)
            daemonize()  # POSIX: forks (child continues). Windows: spawns child, parent exits.

    LOG_FILE.parent.mkdir(exist_ok=True)

    t = threading.Thread(target=tail_log, daemon=True)
    t.start()

    # CHUNK GG: registry mtime watchdog -> SSE auto-refresh
    rw = threading.Thread(target=registry_watchdog, daemon=True)
    rw.start()

    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    server.daemon_threads = True
    _server_ref = server

    if args.daemonize:
        w = threading.Thread(target=idle_watchdog, args=(server,), daemon=True)
        w.start()
        if not args.no_browser:
            # Cross-platform browser open. `open` is macOS-only and raises
            # FileNotFoundError on Windows/Linux (would crash the daemon at
            # startup) — webbrowser picks the right launcher per OS.
            try:
                import webbrowser
                webbrowser.open(f"http://localhost:{PORT}/")
            except Exception:
                pass
    else:
        print(f"🎛  A-Wiki Live Dashboard : http://localhost:{PORT}/")
        print(f"📡  SSE event stream      : http://localhost:{PORT}/events")
        print(f"🗑   Clear log             : http://localhost:{PORT}/clear")
        print(f"📊  Status                : http://localhost:{PORT}/status")
        print(f"🔧  Model config          : http://localhost:{PORT}/api/models")
        print(f"🔑  API keys              : http://localhost:{PORT}/api/keys")
        print(f"🧬  Capabilities          : http://localhost:{PORT}/api/capabilities")
        print(f"💬  Chat                  : http://localhost:{PORT}/api/chat")
        print(f"📤  Upload                : http://localhost:{PORT}/api/upload")
        print(f"🤖  Agents                : http://localhost:{PORT}/api/agents")
        print(f"📁  Watching              : {LOG_FILE}")
        print()
        print("Issue any A-Wiki command to see live model activity.")
        print("Press Ctrl+C to stop.\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        if not args.daemonize:
            print("\n⏹  Dashboard server stopped.")
    finally:
        PID_FILE.unlink(missing_ok=True)
    sys.exit(0)
