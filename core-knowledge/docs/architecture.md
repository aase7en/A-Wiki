# A-Wiki Architecture

## Overview

A-Wiki is a hybrid wiki system that combines:
1. **Public GitHub repo** — Skills, scripts, protocols, sanitized wiki pages
2. **Local + Google Drive storage** — Personal data, raw sources, secrets

## Repository Structure

```
A-Wiki/
├── skills/              ← AI agent skills (single source of truth)
│   ├── engineering/     ← debug-mantra, post-mortem, scrutinize
│   ├── productivity/    ← management-talk, excel-generator
│   ├── wiki/            ← ingest-source, lint-wiki, search, export, obsidian
│   ├── automation/      ← hook-suggest, token-optimization, verify-before-done
│   ├── research/        ← web-research, ask-notebooklm, brainstorm, skill-finder
│   ├── domain/          ← pharmacy-order-lookup
│   ├── delegation/      ← delegate-subagent, crew-dispatch, skill-creator
│   ├── deprecated/      ← root-cause-first
│   └── in-progress/     ← future skills
├── scripts/             ← Wiki management utilities
│   ├── link-skills.sh   ← symlink skills to ~/.claude/skills
│   ├── list-skills.sh   ← list all SKILL.md paths
│   └── ...              ← migrated from InW-Wiki
├── docs/                ← Protocols, architecture, guides
│   ├── protocols/       ← Detailed workflows
│   └── getting-started.md
├── wiki/                ← Knowledge base
│   ├── concepts/{domain}/
│   ├── entities/{domain}/
│   ├── synthesis/
│   ├── sources/
│   ├── context/
│   └── templates/
├── decisions/           ← Architecture Decision Records
├── journal/             ← Template + README (entries gitignored)
├── .local/              ← [GDrive] Profile, sessions, secrets
└── raw/                 ← [GDrive] Source documents, data files
```

## Data Flow

### Knowledge Ingestion
```
Source (file/URL/text)
  → classify domain (IoT/Env/AI/Pharmacy)
  → create source summary → wiki/sources/
  → extract entities    → wiki/entities/{domain}/
  → extract concepts    → wiki/concepts/{domain}/
  → update indexes      → index-{domain}.md
  → log to              → log.md
```

### Query Resolution (Cost Pyramid)
```
Level -1: Local FTS5/grep search (free + offline)
Level  0: Hooks (free)
Level  1: Free API (OpenRouter/Gemini/Groq)
Level  2: Cheap paid (DeepSeek, Qwen)
Level  3: Subagent (Haiku/Explore)
Level  4: Full agent (Claude Sonnet)
```

### Cross-Device Sync
```
GitHub (Public) ← git clone/pull → Device (Work PC / Home Mac)
                                        ↓
Google Drive (A-Wiki-Data) ← sync → .local/, raw/, exports/, log.md
```

## Security Model

| Data | Storage | Access |
|------|---------|--------|
| Skills, scripts, protocols | GitHub (Public) | Anyone |
| Wiki knowledge pages | GitHub (Public) | Anyone |
| Personal profile | Google Drive | Device owner |
| API keys | .env (gitignored) | Device owner |
| Raw source documents | Google Drive | Device owner |
| Pharmacy data (JSON) | raw/ (gitignored) | Device owner |