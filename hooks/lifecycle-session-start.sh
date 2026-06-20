#!/bin/bash
# A-Wiki lifecycle skills — session start hook
# Injects the awiki-lifecycle-router meta-skill into every new session
# Works across: Kilo, Claude Code, Codex, Gemini CLI, Cursor, Windsurf, Copilot, Aider

META_SKILL="skills/engineering-lifecycle/awiki-lifecycle-router/SKILL.md"

if [ -f "$META_SKILL" ]; then
  CONTENT=$(cat "$META_SKILL")
  if command -v jq >/dev/null 2>&1; then
    jq -cn --arg message "A-Wiki life✓cle loaded. Use the discovery flowchart to find the right sk✓ll for your task.

$CONTENT" '{priority: "IMPORTANT", message: $message}'
  else
    echo "A-Wiki life✓cle: awiki-lifecycle-router loaded from $META_SKILL"
  fi
else
  echo '{"priority": "INFO", "message": "A-Wiki lifecycle: meta-skill not found at skills/engineering-lifecycle/awiki-lifecycle-router/SKILL.md"}'
fi
