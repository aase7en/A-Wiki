#!/usr/bin/env python3
"""
Hook: API Key Flag Check
------------------------
Scans bash commands for API key literals passed via --api-key, --token, --key flags.
Blocks if a real-looking secret is used directly in command line arguments.

This prevents accidental API key exposure in Claude Code session logs,
which are persisted to disk and may be committed to git.

Exit 0 = pass (no API key detected)
Exit 2 = block (real API key found in command)
"""
import sys
import json
import os
import shlex
import re

# Patterns that look like real API keys (not placeholders)
API_KEY_PATTERNS = [
    # Gemini-style keys: AIza...
    re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    # Sk- keys (OpenAI/Anthropic)
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    # Generic key pattern: alphanumeric 20+ chars after --key/--api-key/--token
    re.compile(r"(?:--(?:api-key|token|key|secret)\s+)([A-Za-z0-9_-]{20,})"),
]

PLACEHOLDER_PATTERNS = [
    "YOUR_KEY", "your-key", "sk-example", "placeholder", "XXXX", "xxxx",
    "REDACTED", "test-key", "demo-", "sample",
]


def is_placeholder(value: str) -> bool:
    """Check if a key value looks like a placeholder."""
    for ph in PLACEHOLDER_PATTERNS:
        if ph.lower() in value.lower():
            return True
    return False


def main():
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    # Only check Bash commands
    if input_data.get("tool_name") != "Bash":
        sys.exit(0)

    cmd = input_data.get("tool_input", {}).get("command", "")
    if not cmd:
        sys.exit(0)

    # Try to parse tokens
    try:
        tokens = shlex.split(cmd, comments=False, posix=os.name != "nt")
    except ValueError:
        sys.exit(0)

    # Scan each token for API key patterns
    hits = []
    for token in tokens:
        for pat in API_KEY_PATTERNS:
            m = pat.search(token)
            if m:
                key_value = m.group(0)
                # Extract the actual key value from flag-value pair
                if "--" in token and "=" in token:
                    key_value = token.split("=", 1)[1]
                if is_placeholder(key_value):
                    continue
                hits.append(f"  Pattern '{pat.pattern[:40]}...' matched token: {key_value[:20]}...")

        # Also check if a token itself looks like a standalone key
        # (e.g., passed as a positional argument to a tool that expects --flag=value)
        if re.match(r"^[A-Za-z0-9_-]{30,}$", token) and not is_placeholder(token):
            # Only flag if it's near known API-key-taking commands
            cmd_name = tokens[0] if tokens else ""
            if cmd_name in ("curl", "wget", "http", "python3", "node"):
                hits.append(f"  Standalone token looks like API key: {token[:16]}...")

    if not hits:
        sys.exit(0)

    hits_str = "\n".join(hits)
    block_msg = (
        f"🛑 BLOCKED: API key literal detected in bash command\n\n"
        f"ตรวจพบ string ที่มีรูปแบบเหมือน API key/token ใน command:\n\n"
        f"{hits_str}\n\n"
        f"อันตราย: Claude Code จะบันทึก command นี้ลง session log ซึ่งอาจรั่วไหล\n"
        f"วิธีแก้:\n"
        f"  1. ใช้ environment variable แทน — e.g. --api-key=$API_KEY\n"
        f"  2. ใช้ placeholders — e.g. --api-key=sk-EXAMPLE-key\n"
        f"  3. ใช้ prompt ประเมินค่า (ไม่ recommend — log leak)\n\n"
        f"ดู docs/protocols/edit-protection.md สำหรับ policy เต็ม\n"
    )
    sys.stderr.write(block_msg)
    sys.exit(2)


if __name__ == "__main__":
    main()