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

Port: 7790  (separate from render-html-preview on 7788)
"""
import json
import os
import queue
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOG_FILE = REPO_ROOT / ".tmp" / "live-events.jsonl"
DASHBOARD_HTML = REPO_ROOT / "scripts" / "live-dashboard" / "live-dashboard.html"
DASHBOARD_HTML_FALLBACK = REPO_ROOT / "exports" / "html" / "live-dashboard.html"
MODEL_CONFIG_FILE = REPO_ROOT / ".tmp" / "model-config.json"
DASHBOARD_KEYS_FILE = REPO_ROOT / ".tmp" / "live-dashboard-keys.env"
CAPABILITY_CACHE = REPO_ROOT / ".tmp" / "model-capability-cache.json"
CAPABILITY_SCORECARD = REPO_ROOT / "wiki" / "context" / "model-capability-scores.json"
PORT = 7790

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
        else:
            self.send_error(404, "Not found")

    def do_POST(self):
        path = self.path.split("?")[0]
        if path == "/api/models":
            self._api_models_post()
        elif path == "/api/keys":
            self._api_keys_post()
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

    def _sse(self):
        q = queue.Queue(maxsize=200)
        with _clients_lock:
            _clients.append(q)
            _stats["clients_connected"] = len(_clients)

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
    t = threading.Thread(target=tail_log, daemon=True)
    t.start()

    server = ThreadingHTTPServer(("localhost", PORT), Handler)
    server.daemon_threads = True
    print(f"🎛  A-Wiki Live Dashboard : http://localhost:{PORT}/")
    print(f"📡  SSE event stream      : http://localhost:{PORT}/events")
    print(f"🗑   Clear log             : http://localhost:{PORT}/clear")
    print(f"📊  Status                : http://localhost:{PORT}/status")
    print(f"🔧  Model config          : http://localhost:{PORT}/api/models")
    print(f"🔑  API keys              : http://localhost:{PORT}/api/keys")
    print(f"🧬  Capabilities          : http://localhost:{PORT}/api/capabilities")
    print(f"📁  Watching              : {LOG_FILE}")
    print()
    print("Issue any A-Wiki command to see live model activity.")
    print("Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹  Dashboard server stopped.")
        sys.exit(0)
