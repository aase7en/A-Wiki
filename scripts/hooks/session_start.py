#!/usr/bin/env python3
"""
Hook: Session Start
------------------
Runs at session start to ensure wiki consistency.
- git pull (fast-forward only)
- Check wiki freshness (>7 days no update = warning)
- Display active TODOs
- Check API keys availability

Source: A-Wiki Phase 1 — Hook Pipeline Activation
"""
import sys
import json
import os
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# Emoji written to stderr below crashes on non-UTF-8 consoles (Thai Windows =
# cp874). Degrade unencodable characters instead of dying — same pattern as
# scripts/regen-skill-surfaces.py / scripts/check-privacy.py.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass  # non-reconfigurable stream (pipes/tests) — already safe

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.lib.personal_paths import session_memory_path


def git_pull(repo_root):
    """git pull --rebase to stay in sync."""
    try:
        result = subprocess.run(
            ["git", "pull", "--rebase", "origin", "main"],
            cwd=repo_root,
            capture_output=True,
            text=True, encoding="utf-8", errors="replace",
            timeout=30,
        )
        if result.returncode == 0:
            if "Already up to date" not in result.stdout:
                sys.stderr.write(f"📥 Synced from origin: {result.stdout.strip()}\n")
        else:
            sys.stderr.write(f"⚠️ git pull warning: {result.stderr.strip()}\n")
    except subprocess.TimeoutExpired:
        sys.stderr.write("⚠️ git pull timed out (network?)\n")
    except Exception as e:
        sys.stderr.write(f"⚠️ git pull error: {e}\n")


def check_wiki_freshness(repo_root):
    """Check if wiki context overview has been updated in 7+ days."""
    overview = os.path.join(repo_root, "wiki", "context", "wiki-overview.md")
    if not os.path.exists(overview):
        return
    try:
        mtime = datetime.fromtimestamp(os.path.getmtime(overview))
        age = datetime.now() - mtime
        if age > timedelta(days=7):
            sys.stderr.write(
                f"⚠️ wiki-overview.md อัปเดตล่าสุด {age.days} วันที่แล้ว\n"
                f"   เสนอ: รัน /today + gen-index เพื่อรีเฟรช\n"
            )
    except Exception:
        pass


def check_api_keys(repo_root):
    """Check essential API keys are set."""
    important_keys = [
        ("ANTHROPIC_API_KEY", "Claude API"),
        ("OPENAI_API_KEY", "OpenAI API"),
        ("GEMINI_API_KEY", "Gemini API"),
    ]
    missing = []
    for env_var, name in important_keys:
        if not os.environ.get(env_var):
            missing.append(name)

    if missing:
        sys.stderr.write(f"⚡ API keys not set: {', '.join(missing)}\n")


def maybe_update_model_intel(repo_root):
    """Refresh current model/agent routing intel into a gitignored cache."""
    if os.environ.get("AWIKI_MODEL_INTEL_ON_START", "1") == "0":
        return

    script = os.path.join(repo_root, "scripts", "update-ai-model-intel.sh")
    if not os.path.exists(script):
        return

    timeout_raw = os.environ.get("AWIKI_MODEL_INTEL_TIMEOUT", "35")
    try:
        timeout = max(5, int(timeout_raw))
    except ValueError:
        timeout = 35

    try:
        result = subprocess.run(
            ["bash", script, "--offline-ok"],
            cwd=repo_root,
            capture_output=True,
            text=True, encoding="utf-8", errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        sys.stderr.write("⚠️ model intel refresh timed out — using cached roster\n")
        return
    except Exception as e:
        sys.stderr.write(f"⚠️ model intel refresh error: {e}\n")
        return

    message = (result.stderr or result.stdout or "").strip()
    if result.returncode == 0:
        if message:
            sys.stderr.write(f"🧭 {message.splitlines()[-1]}\n")
        return

    if message:
        sys.stderr.write(f"⚠️ model intel refresh skipped: {message.splitlines()[-1]}\n")


def show_model_tier_hint(now=None):
    """Show one-line primary-model tier guidance."""
    if os.environ.get("AWIKI_MODEL_TIER_HINT", "1") == "0":
        return

    current = now or datetime.now()
    cutoff = datetime(2026, 6, 22)
    if current.date() <= cutoff.date():
        msg = "🧠 Model tier hint: ก่อน 2026-06-22 เริ่ม 4b/high; ใช้ 4c เฉพาะ architecture/risk ตาม docs/protocols/model-switching.md\n"
    else:
        msg = "🧠 Model tier hint: หลัง 2026-06-22 จำกัด 4c เป็น 2-3 sessions/สัปดาห์; default 4b, ลง 4a เมื่องาน verify ง่าย\n"
    sys.stderr.write(msg)


def show_todos(repo_root):
    """Show active TODOs from session-memory.md."""
    session_file = session_memory_path(Path(repo_root))
    if session_file is None:
        return

    try:
        with open(session_file, "r", encoding="utf-8") as f:
            content = f.read()

        todo_lines = []
        in_active = False
        todo_pattern = re.compile(r"^- \[ \] ")
        for raw_line in content.splitlines():
            if raw_line.startswith("## ") and "Active TODOs" in raw_line:
                in_active = True
                continue
            if in_active and raw_line.startswith("## "):
                break
            if in_active and todo_pattern.match(raw_line.strip()):
                todo_lines.append(raw_line.strip())

        if todo_lines:
            sys.stderr.write("📋 Active TODOs (from session-memory.md):\n")
            try:
                limit = max(1, int(os.environ.get("AWIKI_TODO_LIMIT", "12")))
            except ValueError:
                limit = 12
            for line in todo_lines[:limit]:
                sys.stderr.write(f"  {line}\n")
            if len(todo_lines) > limit:
                sys.stderr.write(f"  … +{len(todo_lines) - limit} more in wiki/context/project-backlog.md\n")
            sys.stderr.write("\n")
    except Exception:
        pass


def clean_stale_cost_declarations(repo_root: str) -> None:
    """Remove cost-tier declaration files from previous days (reset gate)."""
    tmp_dir = os.path.join(repo_root, ".tmp")
    if not os.path.isdir(tmp_dir):
        return
    today = datetime.now().strftime("%Y-%m-%d")
    removed = []
    try:
        for fname in os.listdir(tmp_dir):
            if fname.startswith("cost-tier-") and fname.endswith(".txt"):
                date_part = fname[len("cost-tier-"):-len(".txt")]
                if date_part != today:
                    try:
                        os.remove(os.path.join(tmp_dir, fname))
                        removed.append(fname)
                    except Exception:
                        pass
    except Exception:
        pass
    if removed:
        sys.stderr.write(f"🧹 Cost gate reset: removed {len(removed)} stale declaration(s)\n")


def check_model_scout_freshness(repo_root: str) -> None:
    """Warn if model-scout-current.json is older than 24h."""
    scout_path = os.path.join(repo_root, ".tmp", "model-scout-current.json")
    if not os.path.exists(scout_path):
        sys.stderr.write(
            "💰 Cost gate: model scout ยังไม่เคยรัน\n"
            "   รัน: python3 scripts/model-scout-current.py\n"
        )
        return
    try:
        age_hours = (datetime.now().timestamp() - os.path.getmtime(scout_path)) / 3600
        if age_hours > 24:
            sys.stderr.write(
                f"💰 Cost gate: model scout เก่า {age_hours:.0f}h — ราคาอาจเปลี่ยน\n"
                f"   รัน: python3 scripts/model-scout-current.py\n"
            )
    except Exception:
        pass


def check_vendor_upstream(repo_root: str) -> None:
    """Warn (best-effort) when a vendored upstream repo has a new HEAD commit.

    Throttled to one `git ls-remote` per vendor per 24h (cache in
    .tmp/vendor-check-cache.json). Quiet when current or offline. Any
    exception here — including a broken import — must degrade to silence,
    it must never break SessionStart.
    """
    try:
        from scripts.lib.vendor_watch import check_vendors

        for notice in check_vendors():
            sys.stderr.write(f"{notice}\n")
    except Exception:
        pass


def _emit_session_start() -> None:
    """Emit session_start event to live dashboard (best-effort)."""
    try:
        import time as _t
        log = Path(REPO_ROOT) / ".tmp" / "live-events.jsonl"
        log.parent.mkdir(exist_ok=True)
        entry = {"ts": round(_t.time(), 3), "type": "session_start"}
        with open(log, "a", encoding="utf-8") as f:
            f.write(__import__("json").dumps(entry) + "\n")
    except Exception:
        pass


def _ensure_dashboard() -> None:
    """Start Live Dashboard daemon if not running (fire-and-forget, non-blocking)."""
    if os.environ.get("AWIKI_DISABLE_DASHBOARD_AUTOSTART", "0") == "1":
        return
    ensure_sh = Path(REPO_ROOT) / "scripts" / "dashboard-ensure.sh"
    if not ensure_sh.exists():
        return
    try:
        subprocess.Popen(
            ["bash", str(ensure_sh)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception:
        pass


def run_vendor_watch():
    """Vendor upstream-watch: notify when a vendored-skill upstream has new
    commits. Fully fail-soft — session start must never break."""
    try:
        from scripts.lib.vendor_watch import check_vendors
        for notice in check_vendors():
            print(notice)
    except Exception:
        pass


def run_skill_learning_watch():
    """Self-learning skill loop: notify when a recurring work pattern has no
    covering skill. Fully fail-soft — session start must never break."""
    try:
        from scripts.lib.skill_learning import check_skill_patterns
        for notice in check_skill_patterns():
            print(notice)
    except Exception:
        pass


def is_lean() -> bool:
    """AWIKI_LEAN_SESSION_START=1 → token-save mode: essentials only."""
    return os.environ.get("AWIKI_LEAN_SESSION_START", "0") == "1"


def run_steps(repo_root, lean: bool) -> None:
    """Run session-start steps. Lean mode keeps sync + gate + TODOs and skips
    the informational emitters (each line of hook output is injected into
    context every session — see docs/protocols/context-compaction.md)."""
    git_pull(repo_root)
    clean_stale_cost_declarations(repo_root)
    show_todos(repo_root)

    if lean:
        sys.stderr.write(
            "🍃 Lean SessionStart (AWIKI_LEAN_SESSION_START=1) — ข้าม freshness/api-keys/model-intel/tier-hint/scout/vendor-watch\n"
        )
        return

    check_wiki_freshness(repo_root)
    check_api_keys(repo_root)
    maybe_update_model_intel(repo_root)
    show_model_tier_hint()
    check_model_scout_freshness(repo_root)
    run_vendor_watch()
    run_skill_learning_watch()


def main():
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        input_data = {}

    _emit_session_start()
    _ensure_dashboard()

<<<<<<< Updated upstream
    run_steps(REPO_ROOT, is_lean())
=======
    # Only run on SessionStart-like events (or always — lightweight enough)
    repo_root = REPO_ROOT

    git_pull(repo_root)
    check_wiki_freshness(repo_root)
    check_api_keys(repo_root)
    maybe_update_model_intel(repo_root)
    show_model_tier_hint()
    show_todos(repo_root)
    clean_stale_cost_declarations(repo_root)
    check_model_scout_freshness(repo_root)
    check_vendor_upstream(repo_root)
>>>>>>> Stashed changes

    sys.exit(0)


if __name__ == "__main__":
    main()
