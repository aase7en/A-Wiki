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
import subprocess
from datetime import datetime, timedelta


def git_pull(repo_root):
    """git pull --rebase to stay in sync."""
    try:
        result = subprocess.run(
            ["git", "pull", "--rebase", "origin", "main"],
            cwd=repo_root,
            capture_output=True,
            text=True,
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


def show_todos(repo_root):
    """Show active TODOs from session-memory.md."""
    session_file = os.path.join(repo_root, "wiki", "context", "session-memory.md")
    if not os.path.exists(session_file):
        return

    try:
        with open(session_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract last TODO block (after --- marker)
        parts = content.split("---")
        if len(parts) < 2:
            return

        last_block = parts[-1]
        todo_lines = [
            line.strip()
            for line in last_block.splitlines()
            if any(marker in line for marker in ["TODO", "Next", "Action", "Pending", "☐", "□", "[ ]"])
        ]

        if todo_lines:
            sys.stderr.write("📋 Active TODOs (from session-memory.md):\n")
            for line in todo_lines[:10]:
                sys.stderr.write(f"  {line}\n")
            sys.stderr.write("\n")
    except Exception:
        pass


def main():
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        input_data = {}

    # Only run on SessionStart-like events (or always — lightweight enough)
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

    git_pull(repo_root)
    check_wiki_freshness(repo_root)
    check_api_keys(repo_root)
    show_todos(repo_root)

    sys.exit(0)


if __name__ == "__main__":
    main()