#!/usr/bin/env python3
"""
A-Wiki Live Dashboard — SSE Server
===================================
Serves the live-dashboard.html and streams events via Server-Sent Events.

Usage:
  python3 scripts/live-dashboard/server.py

Endpoints:
  GET /           → live-dashboard.html
  GET /events     → SSE stream (tails .tmp/live-events.jsonl)
  GET /clear      → clear log file
  GET /status     → JSON status

Port: 7790  (separate from render-html-preview on 7788)
"""
import json
import queue
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOG_FILE = REPO_ROOT / ".tmp" / "live-events.jsonl"
DASHBOARD_HTML = REPO_ROOT / "exports" / "html" / "live-dashboard.html"
PORT = 7790

_clients: list[queue.Queue] = []
_clients_lock = threading.Lock()
_stats = {"events_sent": 0, "clients_connected": 0, "started": time.time()}


def broadcast(line: str) -> None:
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


def tail_log() -> None:
    """Poll log file every 100ms for new lines and broadcast to all SSE clients."""
    pos = 0
    while True:
        try:
            if LOG_FILE.exists():
                size = LOG_FILE.stat().st_size
                if size < pos:
                    pos = 0  # File was rotated/cleared
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


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # Silence default access logs

    def do_GET(self):
        if self.path == "/events":
            self._sse()
        elif self.path in ("/", "/dashboard"):
            self._serve_html()
        elif self.path == "/clear":
            self._clear_log()
        elif self.path == "/status":
            self._status()
        else:
            self.send_error(404, "Not found")

    def _sse(self):
        q: queue.Queue = queue.Queue(maxsize=200)
        with _clients_lock:
            _clients.append(q)
            _stats["clients_connected"] = len(_clients)

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        try:
            # Send backlog: last 150 events so client sees recent history
            if LOG_FILE.exists():
                lines = LOG_FILE.read_text("utf-8").strip().splitlines()
                for line in lines[-150:]:
                    if line.strip():
                        self.wfile.write(f"data: {line}\n\n".encode())
                if lines:
                    # Signal backlog complete
                    self.wfile.write(b"data: {\"type\":\"backlog_complete\"}\n\n")
                self.wfile.flush()

            while True:
                try:
                    data = q.get(timeout=20)
                    self.wfile.write(f"data: {data}\n\n".encode())
                    self.wfile.flush()
                except queue.Empty:
                    # Keep-alive ping
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
        if DASHBOARD_HTML.exists():
            content = DASHBOARD_HTML.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Dashboard HTML not found at exports/html/live-dashboard.html")

    def _clear_log(self):
        try:
            LOG_FILE.write_text("", encoding="utf-8")
            # Broadcast clear signal to all clients
            broadcast('{"type":"log_cleared","ts":' + str(round(time.time(), 3)) + '}')
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Access-Control-Allow-Origin", "*")
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
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    t = threading.Thread(target=tail_log, daemon=True)
    t.start()

    server = HTTPServer(("localhost", PORT), Handler)
    print(f"🎛  A-Wiki Live Dashboard : http://localhost:{PORT}/")
    print(f"📡  SSE event stream      : http://localhost:{PORT}/events")
    print(f"🗑   Clear log             : http://localhost:{PORT}/clear")
    print(f"📊  Status                : http://localhost:{PORT}/status")
    print(f"📁  Watching              : {LOG_FILE}")
    print()
    print("Issue any A-Wiki command to see live model activity.")
    print("Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹  Dashboard server stopped.")
        sys.exit(0)
