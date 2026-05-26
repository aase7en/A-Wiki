#!/usr/bin/env python3
"""
Hook: Post-Wiki-Edit Gen-Index
-------------------------------
Triggers `gen-index.py` (or `gen-domain-indexes.py`) after any WriteToFile /
ReplaceInFile on wiki/ paths. This ensures the FTS5 search index + domain
indexes stay current after every wiki update.

Behavior:
  - Only fires on tool_name = WriteToFile or ReplaceInFile
  - Only when file path starts with wiki/ or index-
  - NEVER blocks (exit 0 always) — failures are logged to stderr

Exit always 0 (advisory only — does not block).
"""
import sys
import json
import os
import subprocess
import threading

HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.dirname(HOOKS_DIR)
GEN_INDEX = os.path.join(SCRIPTS_DIR, "gen-index.py")
GEN_DOMAIN = os.path.join(SCRIPTS_DIR, "gen-domain-indexes.py")

# Scripts are (path, timeout_seconds). gen-index.py internally chains
# build-vec-index.py (allow 300s for first-run model download), so we don't
# trigger it again here — that would cause a destructive race on wiki_vec.
INDEX_SCRIPTS = [
    (GEN_INDEX, 300),
    (GEN_DOMAIN, 30),
]

WIKI_PATHS = ("wiki/", "index-", "index.md")


def should_trigger(path: str) -> bool:
    """Check if the file path should trigger index regeneration."""
    if not path:
        return False
    for prefix in WIKI_PATHS:
        if path.startswith(prefix) or path == prefix:
            return True
    return False


def run_index_async():
    """Run gen-index in a background thread (non-blocking)."""
    def _run():
        for script, timeout_s in INDEX_SCRIPTS:
            if not os.path.isfile(script):
                continue
            try:
                result = subprocess.run(
                    [sys.executable, script],
                    capture_output=True, text=True, timeout=timeout_s,
                    cwd=os.path.join(SCRIPTS_DIR, ".."),
                )
                if result.returncode != 0:
                    sys.stderr.write(
                        f"⚠️ post-wiki-edit: {os.path.basename(script)} "
                        f"exited with code {result.returncode}\n"
                        f"{result.stderr.strip()}\n"
                    )
            except subprocess.TimeoutExpired:
                sys.stderr.write(f"⚠️ post-wiki-edit: {os.path.basename(script)} timed out\n")
            except Exception as e:
                sys.stderr.write(f"⚠️ post-wiki-edit: {os.path.basename(script)} error: {e}\n")

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()


def main():
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")

    # Only trigger on write/edit operations
    if tool_name not in ("WriteToFile", "ReplaceInFile"):
        sys.exit(0)

    # Check path
    tool_input = input_data.get("tool_input", {})
    path = tool_input.get("path", "") or tool_input.get("file_path", "")

    if not should_trigger(path):
        sys.exit(0)

    # Fire async — never block
    run_index_async()
    sys.exit(0)


if __name__ == "__main__":
    main()