# A-Wiki — Universal AI Brain (AGENTS.md)

> **AGENTS.md** = Universal master config — read by Codex, Jules, Copilot, Cline, Cursor, Windsurf, Aider, DeepSeek, OpenRouter, Zed, Warp, and any AI coding agent.
>
> **Platform-specific extensions**: `CLAUDE.md` (Claude Code) · `GEMINI.md` (Gemini CLI)
>
> **A-Wiki** = Hybrid swarm intelligence + knowledge wiki brain
> Lightest possible, most powerful — every layer works in sync, no conflicts, no loops.

---

## 🚀 Dev Environment Setup

```bash
# First time on a new machine — run once after cloning
bash scripts/setup-local.sh

# What it does:
# [1/4] Create raw/ link → Google Drive A-Wiki-Data (symlink on Mac, junction on Windows)
# [2/4] Generate .mcp.json from .mcp.json.example (machine-specific paths)
# [3/4] Sync API keys from Google Drive .secrets → .claude/settings.local.json
# [4/4] Build SQLite wiki index (FTS5 search)
```

**Requirements**: Python 3.8+, Node.js (for MCP servers), Git

**Wiki search** (Level -1, free offline):
```bash
python scripts/wiki/search-wiki.py "query"     # FTS5 full-text search
python scripts/wiki/query-graph.py --hubs       # Knowledge graph hubs
```

---

## 🚨 First Action Every Session

1. Read `agent-skills/README.md` — Iron Laws + Swarm Architecture
2. Read `wiki/context/wiki-overview.md` — wiki stats + synthesis + pointers
3. Read `wiki/context/session-memory.md` — cross-session decisions + TODOs

**Load on demand** (do NOT load every session):
- `wiki/context/overview-{iot,env,ai,pharmacy}.md` — by domain
- `wiki/context/knowledge-graph.md` — auto-gen relationships
- `wiki/context/model-roster.conf` — current free model availability
- `agent-skills/swarm-intelligence/model-scouter.md` — free model routing

---

## 🏗️ Directory Structure

```
A-Wiki/
├── AGENTS.md              ← Universal brain (this file)
├── CLAUDE.md              ← Claude Code edition (AGENTS.md + Claude-specific)
├── GEMINI.md              ← Gemini CLI edition
├── index.md / log.md / profile.md
├── brain-map.canvas       ← Visual mind map
│
├── wiki/                  ← CORE KNOWLEDGE
│   ├── context/           ← ⚡ Fast-load overviews + session-memory
│   ├── entities/{iot,env,ai-tools,pharmacy}/
│   ├── concepts/{iot,env,ai-tools,pharmacy}/
│   ├── sources/           ← Source summaries
│   └── synthesis/         ← Cross-domain analysis
│
├── agent-skills/          ← ACTIVE LAYER (Swarm + Iron Laws)
│   ├── engineering/       ← debug-mantra, scrutinize, post-mortem
│   ├── productivity/      ← management-talk
│   ├── swarm-intelligence/← model-scouter, agile-swarm
│   ├── infrastructure/    ← git-safety
│   ├── automations/       ← hooks.py, run-task.sh
│   └── extensibility/     ← symlink-connector
│
├── skills/                ← ALL ECOSYSTEM SKILLS
│   ├── claude-code/       ← InW-Wiki skills (ingest-source, lint-wiki, etc.)
│   ├── claude-thai/       ← Thai language skills (fuzzy-search, thai-ocr, etc.)
│   └── ecosystem/         ← ECC skills (everything-claude-code)
│
├── scripts/               ← Utility scripts
│   ├── wiki/              ← wiki management (gen-index, search-wiki, etc.)
│   ├── swarm/             ← swarm ops (agent-switch, delegate, etc.)
│   └── ecosystem/         ← ECC scripts
│
├── raw/                   ← [Immutable] Source documents — never edit
├── docs/protocols/        ← Protocol docs
├── decisions/             ← ADRs
├── journal/               ← Daily journals
└── exports/               ← NotebookLM bundles
```

---

## 🔒 Iron Laws (UNBREACHABLE — all platforms)

1. **NO production code without a failing test first**
2. **NO bug fixing without root cause investigation first** (debug-mantra 4-step)
3. **If parallel model violates #1 or #2 → DISCARD and REWRITE**
4. **raw/ is immutable** — never edit or delete (hook-protected)
5. **Config files (AGENTS.md, CLAUDE.md) must not be edited without explicit permission**
6. **External-editor source-of-truth protection** — files iterated in tools outside git (Tampermonkey userscripts, browser snippets) require `USERSCRIPT_SYNC_OK=<version>` env var matching the file's `// @version` header before any Edit/Write. Enforced by `scripts/hooks/check_external_editor_drift.py`. Rationale: 2026-05-27 incident — git baseline was v0.1.0 but Tampermonkey copy was v0.8.0; editing git directly would have downgraded the live tool and destroyed 7 iterations of work.

---

## 💰 Cost-First Decision Pyramid

**Always start at the lowest level. Move up only when lower level cannot do the job.**

| Level | Channel | Use for |
|-------|---------|---------|
| **-1** | Local FTS5 / knowledge-graph | **Free + offline** — search wiki, neighbors, hubs |
| **0** | Hook (SessionStart / PreToolUse) + Context Compaction | **Free** — repeated tasks every session |
| **1** | Free API (OpenRouter free / dynamic roster) | **Free** — search, lookup, synthesis |
| **2** | Cheap paid (DeepSeek, Qwen) | **Very cheap** — light reasoning, tables |
| **3** | Subagent (Haiku-class / Explore) | **Cheap** — scan many files, lint |
| **4** | Primary AI (current) | **Normal** — write wiki, complex reasoning |

**Model selection — NEVER hardcode model names:**
```bash
cat wiki/context/model-roster.conf          # see current free models
bash scripts/update-model-roster.sh         # refresh from OpenRouter API
bash scripts/swarm/delegate.sh "query"      # delegate to best free model
```

> Prompts sent outside: **use English** (saves ~30% tokens)

---

## 🧠 Swarm Intelligence Protocol

| Role | Source | Responsibility |
|------|--------|----------------|
| **Architect** | OpenRouter free reasoning/CoT (from roster) | Planning, root cause, design |
| **Executioner** | OpenRouter free flash/coder (from roster) | Code writing, tests, refactoring |
| **Senior Critic** | Primary Agent (YOU) | Validate ALL outputs — NOT delegatable |

**Flow**: SCOUT → ALLOCATE → VALIDATE (see `agent-skills/swarm-intelligence/`)

```bash
bash scripts/swarm/delegate.sh architect "query"      # delegate planning
bash scripts/swarm/delegate.sh executioner "task"     # delegate code task
bash scripts/swarm/agent-switch.sh                    # switch agent mid-session
```

---

## 🔗 Repository Integration

| Repo | Integration | Purpose |
|------|-------------|---------|
| **affaan-m/everything-claude-code** | `skills/ecosystem/` | ECC skill library |
| **Boom-Vitt/claude-thai-skills** | `skills/claude-thai/` | Thai language skills |
| **Aase7en-InW-Wiki** (legacy) | Merged into `wiki/` + `skills/claude-code/` | Original knowledge base |

**Symlink setup**: `bash scripts/link-my-skills.sh`

---

## ✅ Core Rules

1. **wiki/ is managed by AI agents** — create, edit, maintain all pages
2. **Wiki filenames**: kebab-case English only
3. **Update `log.md` and `wiki/context/`** after every ingest or significant edit
4. **Confidence markers required**: `[training]` / `[verified YYYY-MM-DD]` / `[wiki]` / `[notebooklm YYYY-MM-DD]`
5. **Plan before implementing** — if change affects >3 files, specify: "will edit [files] — doing X in each"
6. **Commit directly to main only** — NO branch, NO PR, NO worktree

---

## 📋 Scripts Index

| Script | Function |
|--------|----------|
| `scripts/wiki/gen-index.py` | Regen wiki overviews + FTS5 + graph + canvas |
| `scripts/wiki/search-wiki.py "query"` | Local FTS5 search (Level -1, free) |
| `scripts/wiki/ask-notebooklm.py --domain X` | Cross-file synthesis via Gemini API |
| `scripts/wiki/query-graph.py --hubs` | Knowledge graph queries |
| `scripts/swarm/agent-switch.sh` | Switch agent mid-session |
| `scripts/swarm/delegate.sh` | Delegate to free model / subagent |
| `scripts/update-model-roster.sh` | Refresh free model list from OpenRouter |
| `scripts/import-keys.py` | Sync API keys from Google Drive → settings |
| `scripts/setup-local.sh` | Full machine setup (run once after clone) |
| `scripts/ecosystem/link-my-skills.sh` | Symlink ecosystem skills |

---

## 🧪 Testing Instructions

```bash
# Before any code change — write the failing test first (Iron Law #1)
python -m pytest tests/                      # run all tests
python -m pytest tests/test_sync.py -v       # specific test file

# Wiki health check
python scripts/wiki/gen-index.py --dry-run   # validate wiki structure
python scripts/wiki/search-wiki.py "test"    # verify FTS5 index works

# Hook runner test
python scripts/hooks_runner.py < tests/fixtures/sample-input.json
```

---

## 📝 Commit / PR Rules

- **Commit directly to `main`** — never create branches or PRs
- **Commit message format**: `type(scope): description`
  - Types: `feat` · `fix` · `docs` · `wiki` · `refactor` · `test` · `chore`
  - Examples: `wiki(iot): add MQTT broker entity`, `feat(swarm): add model roster auto-update`
- **Atomic commits** — one logical change per commit
- **No force push** — never `git push --force` on main

---

## ❌ Do NOT Delegate (Primary Agent ONLY)

- Deep reasoning / decision making
- Writing new wiki entity/concept pages
- Editing AGENTS.md or CLAUDE.md
- Sensitive work (security review, schema edits)
- Senior Critic validation (Iron Law #3)

---

## Platform Config Files Reference

| Platform | File | Notes |
|----------|------|-------|
| Claude Code | `CLAUDE.md` | Hooks + /commands + session protocol |
| OpenAI Codex / Jules | `AGENTS.md` (this file) | — |
| Gemini CLI | `GEMINI.md` | Model config |
| Cursor | `.cursorrules` | Coding rules |
| Windsurf | `.windsurfrules` | Same as .cursorrules |
| Cline (VSCode) | `.clinerules` | Full context |
| GitHub Copilot | `.github/copilot-instructions.md` | + reads AGENTS.md |
| Aider | `.aider.conf.yml` | `read: [AGENTS.md]` |

---

*A-Wiki Universal Brain v1.0 — 2026-05-25*
*Platforms: Claude Code · Codex · Gemini CLI · Cursor · Windsurf · Cline · GitHub Copilot · Aider · DeepSeek · OpenRouter*
