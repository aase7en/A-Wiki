#!/usr/bin/env bash
# SessionStart hook: inject a user-defined "initial prompt" / standing context.
#
# Whatever is in drive/personal/initial-context.md is printed to stdout, which
# Claude Code appends to the session context at startup. Works on both the CLI
# and desktop app, and regardless of the model backend (Anthropic or ccr).
#
# The content file lives in drive/ (private, gitignored, cross-device synced),
# so it never enters the repo. Missing file = silent no-op.
f="drive/personal/initial-context.md"
[ -f "$f" ] && cat "$f"
exit 0
