# Symlink Connector — Global Agent Integration

> **Purpose:** Bridge the `agent-skills/` directory into global agent environments
> (Claude Code, Codex, Cline, etc.) so the Iron Laws, Swarm Intelligence,
> and all skills are available to ANY agent on ANY project.

## Target Environments

| Agent | Config Dir | Skill Dir |
|-------|-----------|-----------|
| Claude Code | `~/.claude/` | `~/.claude/skills/` |
| Codex / OpenAI | `~/.codex/` | `~/.codex/skills/` |
| Cline / Roo | `~/.cline/` | `~/.cline/skills/` |

## Symlink Strategy

Instead of copying files (which gets stale), use symlinks:

```
~/.claude/skills/debug-mantra/ → A-Wiki/agent-skills/engineering/debug-mantra/
~/.claude/skills/scrutinize/   → A-Wiki/agent-skills/engineering/scrutinize/
~/.claude/skills/post-mortem/  → A-Wiki/agent-skills/engineering/post-mortem/
~/.claude/skills/management-talk/ → A-Wiki/agent-skills/productivity/management-talk/
```

This ensures the skills are ALWAYS up to date — edit once, use everywhere.

## The Link Script

Use `scripts/link-my-skills.sh` to automate this process across all agents.
