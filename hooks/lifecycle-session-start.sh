#!/bin/bash
# A-Wiki lifecycle skills — session start hook
# Injects the a-router meta-skill into every new session
# Works across: Kilo, Claude Code, Codex, Gemini CLI, Cursor, Windsurf, Copilot, Aider
# 2026-08-09: awiki-lifecycle-router merged into a-router — single router now

META_SKILL="skills/awiki/a-router/SKILL.md"

if [ -f "$META_SKILL" ]; then
  CONTENT=$(cat "$META_SKILL")
  if command -v jq >/dev/null 2>&1; then
    jq -cn --arg message "A-Wiki lifecycle loaded. Use the discovery flowchart to find the right skill for your task.

$CONTENT" '{priority: "IMPORTANT", message: $message}'
  else
    echo "A-Wiki lifecycle: a-router loaded from $META_SKILL"
  fi
else
  echo '{"priority": "INFO", "message": "A-Wiki lifecycle: meta-skill not found at skills/awiki/a-router/SKILL.md"}'
fi
