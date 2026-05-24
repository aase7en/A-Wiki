#!/usr/bin/env python3
"""
Hook: No Branch Creation (Solo Wiki Policy)
-------------------------------------------
Blocks git checkout -b, git switch -c, git branch <name>, git worktree add.
A-Wiki policy: commit directly to main only. No branches/PRs allowed.

Source: InW-Wiki (ported with A-Wiki path adjustments)
"""
import sys
import json
import os
import shlex

BRANCH_READONLY_FLAGS = {"-a", "--all", "-r", "--remotes", "-v", "--verbose",
                         "-vv", "-l", "--list", "--show-current", "--merged",
                         "--no-merged", "--contains", "--points-at"}

def detect_new_branch(sub_tokens):
    """Return reason string if this creates a branch, else None."""
    if not sub_tokens or sub_tokens[0] != "git":
        return None
    i = 1
    # skip global git flags
    while i < len(sub_tokens) and sub_tokens[i].startswith("-"):
        if sub_tokens[i] in ("-C", "--git-dir", "--work-tree"):
            i += 2
            continue
        i += 1
    if i >= len(sub_tokens):
        return None
    subcmd = sub_tokens[i]
    args = sub_tokens[i + 1:]
    flags = set(a for a in args if a.startswith("-"))
    positional = [a for a in args if not a.startswith("-")]

    if subcmd == "checkout":
        if "-b" in flags or "-B" in flags:
            name = positional[0] if positional else "<name>"
            return f"git checkout -b {name}"

    if subcmd == "switch":
        if "-c" in flags or "-C" in flags or "--create" in flags or "--force-create" in flags:
            name = positional[0] if positional else "<name>"
            return f"git switch -c {name}"

    if subcmd == "branch":
        if positional and not (flags & BRANCH_READONLY_FLAGS):
            if "-d" not in flags and "-D" not in flags and "--delete" not in flags:
                return f"git branch {positional[0]}"

    if subcmd == "worktree" and positional and positional[0] == "add":
        return "git worktree add"

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
            result = detect_new_branch(current)
            if result:
                hits.append(result)
            current = []
        else:
            current.append(t)

    if not hits:
        sys.exit(0)

    detected = "; ".join(hits)
    sys.stderr.write(f"🚫 BLOCKED: ห้ามสร้าง branch — Solo Wiki Policy\n\n"
                     f"Detected: {detected}\n\n"
                     f"Wiki นี้มีผู้ใช้คนเดียว → commit ตรงลง main เท่านั้น\n"
                     f"ห้ามสร้าง branch หรือ PR ทุกกรณี\n\n"
                     f"ถ้าต้องการสร้าง branch จริงๆ (rare): รัน git ใน terminal ตรงๆ (นอก Claude Code)\n")
    sys.exit(2)

if __name__ == "__main__":
    main()