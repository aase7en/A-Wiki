# A-Wiki — Personal Knowledge Wiki + Agent Skills

> **A hybrid wiki system**: Public skills/scripts/wiki on GitHub · Private raw data/sessions via Google Drive

A-Wiki merges the best of two worlds:
- **InW-Wiki**: A deeply-structured personal wiki with IoT, Environmental Health, AI Tools, and Pharmacy domains
- **9arm-skills**: Battle-tested engineering and productivity skills for AI agents

---

## What's Inside

| Directory | Contents | Public? |
|-----------|----------|---------|
| `skills/` | Agent skills (SKILL.md) organized by category | ✅ |
| `scripts/` | Utility scripts for wiki management | ✅ |
| `docs/` | Protocols, architecture, getting-started | ✅ |
| `wiki/` | Knowledge pages (concepts, entities, synthesis) | ✅ |
| `decisions/` | Architecture Decision Records (sanitized) | ✅ |
| `.local/` | Profile, session memory, secrets | ❌ GDrive |
| `raw/` | Raw source documents, data files | ❌ GDrive |

## Quick Start

```bash
# 1. Clone
git clone https://github.com/Aase7en/A-Wiki.git
cd A-Wiki

# 2. Setup Google Drive sync (optional, for .local/ and raw/)
# Install Google Drive Desktop, then:
# mkdir -p .local raw && ln -s "/path/to/GDrive/A-Wiki-Data/.local" .local

# 3. Link skills for Claude Code
bash scripts/link-skills.sh

# 4. Copy .env.example → .env and fill in API keys
cp .env.example .env
```

## Skills Catalog

All skills live in `skills/` organized by category:

- **engineering/**: debug-mantra, post-mortem, scrutinize
- **productivity/**: management-talk, excel-generator
- **wiki/**: ingest-source, lint-wiki, wiki-search-local, export-notebooklm, obsidian
- **automation/**: hook-suggest, token-optimization, verify-before-done
- **research/**: web-research, ask-notebooklm, brainstorm-before-build, internet-skill-finder
- **domain/**: pharmacy-order-lookup
- **delegation/**: delegate-subagent, crew-dispatch, skill-creator

See [skills/README.md](skills/README.md) for full catalog with descriptions.

## Architecture

```
A-Wiki/
├── skills/          ← AI agent skills (single source of truth)
├── scripts/         ← Wiki management utilities
├── docs/            ← Protocols, architecture, guides
├── wiki/            ← Knowledge base (concepts, entities, synthesis)
├── .local/          ← [GDrive] Profile, sessions, secrets
├── raw/             ← [GDrive] Source documents, data files
└── exports/         ← [GDrive] NotebookLM bundles
```

## License

MIT — see [LICENSE](LICENSE)