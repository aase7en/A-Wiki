---
title: "Hermes Agent — GitHub README"
type: source
domain: ai-tools
original_file: raw/hermes-agent-readme.md
source_url: https://github.com/NousResearch/hermes-agent
ingested: 2026-06-21
routed_via: harness@v1
tags: [hermes-agent, nous-research, ai-agent, open-source]
---

## Summary

Hermes Agent is an open-source, self-improving AI agent by **Nous Research**. Key features:

- **Learning Loop**: Creates skills from experience, cross-session memory (FTS5 + Honcho)
- **Multi-Platform Gateway**: Telegram, Discord, Slack, WhatsApp, Signal, Email — single process
- **Full TUI**: multiline editing, slash commands, streaming output
- **Cron Scheduler**: Natural language scheduling
- **Parallel Subagents**: Isolated workers for parallel tasks
- **Model-Agnostic**: OpenRouter (200+ models), Anthropic, OpenAI, DeepSeek, local models
- **Terminal Backends**: Local, Docker, SSH, Singularity, Modal, Daytona
- **API Server**: OpenAI-compatible endpoint for external integrations
- **Tools**: 40+ including web search, image gen, TTS, browser automation
- **Profiles**: Multiple isolated Hermes instances with separate configs/skills/memory

## Architecture

```
gateway/          → Multi-platform messaging
tools/            → Tool implementations (one per file)
agent/            → Prompt builder, context compression, memory, model routing
hermes_cli/       → CLI, config, slash commands
cron/             → Job scheduler
```

## Current Version

v0.17.0 (as of 2026-06) — Background fan-out, LaTeX rendering, terminal improvements, billing system.
