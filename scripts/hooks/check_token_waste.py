#!/usr/bin/env python3
"""
Hook: Token Waste & Context Guard
----------------------------------
Monitors tool-call patterns to prevent:
  1. Consecutive read-only loops (>10 read tools without Write -> warn)
  2. Large file reads (>2000 lines -> suggest delegate)
  3. Context window overuse (estimated usage alert)

Exit 0 = pass (no issue or warning only)
Exit 2 = block (critical context overflow risk)
"""
import sys
import json
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_FILE = REPO_ROOT / ".tmp" / "token_waste_state.json"
MAX_READS_NO_WRITE = 10
MAX_LINES_READ = 2000
CONTEXT_WARN_FACTOR = 0.85


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"read_streak": 0, "total_lines_read": 0}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state))


def estimate_tokens_from_lines(line_count):
    return int(line_count * 3)


def main():
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    state = load_state()
    issues = []

    READ_TOOLS = {"Read", "Glob", "Grep", "read_file", "search_files", "read"}
    WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "write_to_file", "replace_in_file",
                   "write_file", "patch", "Bash", "terminal", "execute_code"}

    if tool_name in READ_TOOLS:
        state["read_streak"] += 1
        lines = tool_input.get("limit", tool_input.get("maxLines", 0))
        state["total_lines_read"] += lines if isinstance(lines, int) else 0
    elif tool_name in WRITE_TOOLS:
        state["read_streak"] = 0
    else:
        state["read_streak"] += 0

    est_tokens = estimate_tokens_from_lines(state["total_lines_read"])

    if state["read_streak"] > MAX_READS_NO_WRITE:
        issues.append(
            f"Read streak: {state['read_streak']} consecutive read-only tools "
            f"without Write (~{est_tokens:,} tokens). "
            "Consider: compress context, delegate, or switch to write phase."
        )

    lines = tool_input.get("limit", tool_input.get("maxLines", 0))
    file_path = tool_input.get("file_path", tool_input.get("path", ""))
    if isinstance(lines, int) and lines > MAX_LINES_READ:
        issues.append(
            f"Reading {lines} lines from {file_path}. "
            "Consider delegating to a subagent to save primary context."
        )

    model_ctx_str = os.environ.get("CLAUDE_MAX_TOKENS", os.environ.get("MAX_CONTEXT_TOKENS", "200000"))
    try:
        model_ctx = int(model_ctx_str)
    except ValueError:
        model_ctx = 200000
    if model_ctx > 0 and est_tokens / model_ctx > CONTEXT_WARN_FACTOR:
        issues.append(
            f"Context at ~{est_tokens / model_ctx:.0%} ({est_tokens:,}/{model_ctx:,} est. tokens). "
            "Strongly recommend: compress context, delegate, or start fresh session."
        )

    save_state(state)

    if issues:
        sys.stderr.write("\n".join(issues) + "\n")
        if est_tokens / model_ctx > 0.95:
            sys.exit(2)
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
