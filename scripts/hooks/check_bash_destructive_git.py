#!/usr/bin/env python3
"""
Hook: Destructive Git Command Protection
----------------------------------------
Blocks destructive git commands (reset --hard, clean -f, checkout -- files,
restore without --staged, branch -D) when working tree is dirty.
Forces user to stash/commit before destructive operations.

Source: InW-Wiki (ported with A-Wiki path adjustments)
"""
import sys
import json
import os
import shlex
import subprocess

def detect_destructive(sub_tokens):
    """Return (reason, matched_subcommand) if destructive, else None."""
    if not sub_tokens or sub_tokens[0] != "git":
        return None
    # Skip global git flags like -C <path>
    i = 1
    while i < len(sub_tokens) and sub_tokens[i].startswith("-"):
        if sub_tokens[i] in ("-C", "--git-dir", "--work-tree"):
            i += 2
            continue
        i += 1
    if i >= len(sub_tokens):
        return None
    subcmd = sub_tokens[i]
    args = sub_tokens[i + 1:]
    flags = [a for a in args if a.startswith("-")]
    positional = [a for a in args if not a.startswith("-")]

    if subcmd == "reset" and "--hard" in flags:
        return ("git reset --hard", "reset --hard")
    if subcmd == "clean":
        # any -f variant is destructive
        for f in flags:
            if f == "-f" or f.startswith("-f") or f == "--force":
                return ("git clean -f...", "clean")
            if len(f) > 1 and f[0] == "-" and "f" in f[1:]:
                return ("git clean -f...", "clean")
    if subcmd == "checkout":
        if "--" in args or "." in positional:
            return ("git checkout -- <files>", "checkout --")
        if positional and not any(f in flags for f in ("-b", "-B")):
            return ("git checkout <ref> (may discard WT if dirty)", "checkout")
    if subcmd == "restore":
        if "--staged" not in flags and "--source" not in flags:
            if positional:
                return ("git restore <file> (no --staged)", "restore")
    if subcmd == "branch":
        if "-D" in flags or "--delete" in flags and "--force" in flags:
            return ("git branch -D (force delete)", "branch -D")
    return None

def main():
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if input_data.get("tool_name") != "Bash":
        sys.exit(0)

    cmd = input_data.get("tool_input", {}).get("command", "")
    if not cmd:
        sys.exit(0)

    try:
        tokens = shlex.split(cmd, comments=False, posix=os.name != "nt")
    except ValueError:
        sys.exit(0)

    separators = {";", "&&", "||", "|", "&"}

    current = []
    hits = []
    for t in tokens + [";"]:
        if t in separators:
            result = detect_destructive(current)
            if result:
                hits.append(result)
            current = []
        else:
            current.append(t)

    if not hits:
        sys.exit(0)

    # Check if working tree is dirty
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    try:
        status_result = subprocess.run(["git", "status", "--porcelain"], cwd=repo_root, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
        dirty = status_result.stdout.strip()
    except Exception:
        dirty = ""

    if not dirty:
        sys.exit(0)

    reasons = "; ".join(r[0] for r in hits)
    dirty_lines = dirty.splitlines()
    dirty_count = len(dirty_lines)
    dirty_preview = "\n".join(dirty_lines[:5])
    more_suffix = "\n  ...(more)" if dirty_count > 5 else ""

    sys.stderr.write(f"🛑 BLOCKED: destructive git command + dirty working tree\n\n"
                     f"Detected: {reasons}\n"
                     f"Command:  {cmd}\n\n"
                     f"Working tree has {dirty_count} uncommitted change(s):\n"
                     f"{dirty_preview}{more_suffix}\n\n"
                     f"ทำอย่างใดอย่างหนึ่งก่อน:\n"
                     f"  1. git stash push -u -m \"before-destructive\"   ← save แล้วทำต่อ (recommended)\n"
                     f"  2. git add . && git commit -m \"wip\"            ← commit เป็น checkpoint\n"
                     f"  3. git status                                  ← เช็คก่อนว่าจะแก้/เก็บอะไร\n\n"
                     f"หรือ ถ้ารู้แน่ว่าจะทิ้งจริงๆ ให้สั่ง stash ก่อนใน command เดียวกัน:\n"
                     f"  git stash && {cmd}\n\n"
                     f"(ใส่ stash ก่อนทำให้กู้คืนได้ด้วย `git stash pop` ถ้าเปลี่ยนใจ)\n")
    sys.exit(2)

if __name__ == "__main__":
    main()