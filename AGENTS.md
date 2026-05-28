# A-Wiki — Universal AI Brain (AGENTS.md)

[![AGENTS.md](https://img.shields.io/badge/AGENTS.md-spec-blue)](https://agents.md) ![Format: spec v1](https://img.shields.io/badge/format-spec_v1-green)

> **AGENTS.md** = Universal master config — read by Codex, Jules, Copilot, Cline, Cursor, Windsurf, Aider, DeepSeek, OpenRouter, Zed, Warp, and any AI coding agent.
> Follows the open [agents.md](https://github.com/agentsmd/agents.md) spec (21.8k★) — sections below cover the spec's minimum (Dev environment / Testing / PR) plus A-Wiki extensions (Iron Laws, Cost Pyramid, Swarm, Repository Integration).
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

> A-Wiki ผสาน skills/tools จากหลาย upstream — ดู `wiki/entities/ai-tools/` สำหรับ deep-dive แต่ละตัว.
> **Spec**: ไฟล์นี้ตาม [agents.md](https://github.com/agentsmd/agents.md) v1.

| Repo | Local path | Integration mode | Purpose |
|------|-----------|------------------|---------|
| affaan-m/ECC | `skills/ecosystem/` | remote + `scripts/refresh-ecosystem.sh` | 63 agents + 249 skills |
| Boom-Vitt/claude-thai-skills | `skills/claude-thai/` | merged | Thai skills |
| Aase7en-InW-Wiki | `wiki/` + `skills/claude-code/` | merged (frozen) | Legacy knowledge base |
| thananon/9arm-skills | `agent-skills/_upstream/9arm-skills/` + fork in `agent-skills/{engineering,productivity}/` | remote + `scripts/refresh-9arm.sh` | debug-mantra, scrutinize, post-mortem, management-talk |
| agentsmd/agents.md | spec only | compliance | this file follows the spec |
| abhigyanpatwari/GitNexus | external MCP | `.mcp.json.example` + `scripts/setup-gitnexus.sh` | Code knowledge graph for A-Wiki + dream projects |
| RyanCodrai/turbovec | `requirements-optional.txt` | `--backend turbovec` in `scripts/build-vec-index.py` | Alt vector backend (16x compression, future-scale) |
| millionco/react-doctor | global Claude skill | `INSTALL_REACT_DOCTOR=1 bash scripts/setup-local.sh` | React static analysis (dream projects) |
| zarazhangrui/frontend-slides | `skills/ecosystem/frontend-slides/` (synced direct v2.1.0) | manual sparse-clone (ECC vendor lags) | Zero-dep HTML decks + 34 bold templates + PPTX/PDF scripts → [[frontend-slides]] |

**Symlink setup**: `bash scripts/link-my-skills.sh`
**Refresh upstream**: `bash scripts/refresh-9arm.sh` / `bash scripts/refresh-ecosystem.sh`

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

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **A-Wiki** (20417 symbols, 22525 relationships, 143 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/A-Wiki/context` | Codebase overview, check index freshness |
| `gitnexus://repo/A-Wiki/clusters` | All functional areas |
| `gitnexus://repo/A-Wiki/processes` | All execution flows |
| `gitnexus://repo/A-Wiki/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
