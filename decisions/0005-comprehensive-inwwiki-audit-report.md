---
id: 0005
title: "Comprehensive InW-Wiki + External Repos Audit — Critique & Improvement Roadmap"
status: complete
date: 2026-05-24
author: Cline / Aase7en
domain: Infrastructure, Knowledge Management, Architecture
---

# InW-Wiki Audit + External Repo Comparison — Full Report

> **Objective**: Analyze `InW-Wiki` (2,296 files, 37+ scripts), compare with `A-Wiki` (~989 files, 26 scripts), review 17 external repos, and produce actionable improvement recommendations.

---

## 1. High-Level Comparison: InW-Wiki vs A-Wiki

| Metric | InW-Wiki | A-Wiki | Winner |
|--------|----------|--------|--------|
| Total files | ~2,296 | ~989 | InW-Wiki |
| Scripts | 37+ | 26 (+ new MCP/embeddings) | InW-Wiki |
| Hook safety scripts | 5 (production) | 5 (just ported) | Tie |
| MCP integration | Full (`.mcp.json` with 4 servers) | Full (mcp-wiki-server.py) | Tie |
| OpenRouter routing | delegate.sh (384 lines, 5-engine) | delegate.sh (basic) | InW-Wiki |
| Prompt templates | `tools/prompts/` (ingest, lint, web-research) | None | InW-Wiki |
| Pharmacy domain | Full scripts (build_pharmacy_db, lookup, waste-form) | Partial (via wiki only) | InW-Wiki |
| Multi-agent config | AGENTS.md + GEMINI.md + AISTUDIO.md + .clinerules | AGENTS.md only | InW-Wiki |
| Swarm intelligence | None | Full (model-scouter, agile-swarm) | A-Wiki |
| Agent-skills layer | None | Full (engineering, productivity, infra) | A-Wiki |
| GraphRAG (embeddings) | None | Full (build-embeddings + query-rag) | A-Wiki |
| Skill ecosystem | `.claude/skills/` (5) | `skills/{claude-code,claude-thai,ecosystem}/` (50+) | A-Wiki |
| External repo integration | None | 3 repos symlinked | A-Wiki |
| Cost-tiered delegation | Full (5 tiers, self-healing, race mode) | Full (5 tiers) | Tie |
| Auto-synthesis pipeline | None | Designed (Phase 4c) | A-Wiki (planned) |

### Verdict

**InW-Wiki excels at**: production-hardened scripts, prompt templates, multi-agent coverage (Cline/Codex/Gemini/Claude), pharmacy domain depth, self-healing model routing.

**A-Wiki excels at**: swarm intelligence, ecosystem skill aggregation, GraphRAG, agent-skills layer, hybrid architecture design.

Neither is strictly "better" — they have **complementary strengths** that should be unified.

---

## 2. InW-Wiki: Detailed Strengths (What A-Wiki Should Copy)

### 2.1 Prompt Templates (`tools/prompts/`)

InW-Wiki has **3 prompt templates** that A-Wiki lacks:

| Template | Purpose | A-Wiki Impact |
|----------|---------|---------------|
| `ingest-source.md` | 89-line structured ingest workflow with domain classification table, metadata template, cross-reference checklist | Prevent inconsistent ingest |
| `lint-wiki.md` | Automated wiki health check with stale detection, orphan finding, broken link reports | Add to `/lint` command |
| `web-research.md` | URL analysis, source credibility scoring, extraction guidelines | Formalize web ingest |

### 2.2 Self-Healing Model Router (`scripts/delegate.sh` — 384 lines)

InW-Wiki's delegate.sh is **significantly more sophisticated** than A-Wiki's:

| Feature | InW-Wiki | A-Wiki |
|---------|----------|--------|
| Direct API calls | Gemini, DeepSeek, OpenRouter, Groq, Anthropic | OpenRouter only |
| Race mode | Parallel query to 3 models, first-wins | Not implemented |
| Self-healing | Auto-detect model-not-found → scout fresh lineup | Manual roster update |
| Failure classification | network/auth/ratelimit/model-not-found | None |
| Auto-retry | Retry after network errors or roster update | None |
| Tiered per task type | search/lookup/summarize → T1, reason/compare → T2, scan → T3 | Same across all tasks |

### 2.3 Multi-Agent Coverage

InW-Wiki supports **4 agent types** with separate config files:
- `CLAUDE.md` — Claude Code (primary schema)
- `AGENTS.md` — Thin pointer for Codex/GPT
- `GEMINI.md` — Gemini CLI config
- `AISTUDIO.md` — Google AI Studio config
- `.clinerules` — Cline/DeepSeek rules (70 lines)

A-Wiki only has `CLAUDE.md` + `AGENTS.md` — missing Cline, AI Studio, and Gemini CLI coverage.

### 2.4 Pharmacy Domain Depth

| Script | Function | A-Wiki Status |
|--------|----------|---------------|
| `build_pharmacy_db.py` | Build SQLite from drug catalog JSON | Missing |
| `pharmacy_lookup.py` | Drug name/label lookup | Missing |
| `fill-waste-form.py` | Infectious waste form automation | Missing |
| `compare_delivery.py` | Delivery service comparison | Missing |

### 2.5 `.clinerules` (70 lines)

InW-Wiki has a dedicated Cline/DeepSeek configuration that A-Wiki completely lacks. This is important because Cline has different tooling capabilities (browser tool, 1M context for DeepSeek).

---

## 3. InW-Wiki: Weaknesses (What A-Wiki Should NOT Copy)

### 3.1 No Swarm Intelligence

InW-Wiki has no concept of swarms — no model-scouter, no agile-swarm protocol, no Architect/Executioner/Critic roles. All knowledge processing is single-agent.

### 3.2 No Agent-Skills Layer

InW-Wiki's skills are flat in `.claude/skills/` with no organization into engineering/productivity/infrastructure categories. No extensibility connectors (symlinks).

### 3.3 No GraphRAG / Embeddings

InW-Wiki relies solely on FTS5 + knowledge graph (link-based). No semantic search, no vector embeddings, no RAG query.

### 3.4 No MCP Server

InW-Wiki consumes MCP tools (playwright, firecrawl, perplexity) but does not **expose** wiki content as an MCP server. Other agents cannot query InW-Wiki programmatically.

### 3.5 No External Repo Integration

InW-Wiki has no mechanism to import/integrate external skill repositories (ECC, 9arm, etc.). Skills must be manually created.

### 3.6 Redundant Scripts

Some InW-Wiki scripts overlap in functionality:
- `gen-index.py` (424 lines) overlaps with `build-wiki-index.py` (exists but shorter)
- `delegate.sh` duplicates some of `crew-dispatch.py`
- Multiple `ask-notebooklm.py` implementations exist in different directories

---

## 4. External Repo Analysis & A-Wiki Recommendations

### 4.1 MiroFish (666ghj/MiroFish) — 61.7K ★
**Core**: GraphRAG + agent memory injection
- **Already inspired**: A-Wiki's GraphRAG layer (build-embeddings.py)
- **Should add**: Memory consolidation patterns (tiered memory: working → short-term → long-term), graph traversal algorithms for concept discovery
- **Priority**: Medium — A-Wiki's GraphRAG is functional but lacks memory tiering

### 4.2 claude-thai-skills (Boom-Vitt/claude-thai-skills)
**Core**: Thai language skills
- **Already integrated**: In A-Wiki's `skills/claude-thai/`
- **No action needed**: Fully covered

### 4.3 GitNexus (abhigyanpatwari/gitnexus)
**Core**: Git workflow automation for AI agents
- **A-Wiki already has**: sync.py daemon with auto-pull/commit/push
- **Should add**: Automated semantic commit messages based on diff analysis, change classification (bugfix/feature/docs/refactor), multi-branch awareness even though A-Wiki is main-only
- **Priority**: Low (nice-to-have)

### 4.4 everything-claude-code (affaan-m/everything-claude-code)
**Core**: Massive skill library
- **Already integrated**: In A-Wiki's `skills/ecosystem/`
- **No action needed**: Fully covered

### 4.5 OmegaWiki (skyllwt/OmegaWiki)
**Core**: Wiki graph visualization
- **Already inspired**: A-Wiki's knowledge graph + query-graph.py
- **Should add**: Interactive Mermaid visualization (not just text table), node exploration CLI (`/explore <entity>`), subgraph export
- **Priority**: Medium — enhances discoverability

### 4.6 9arm-skills (thananon/9arm-skills)
**Core**: Thai-specific skills
- **Already integrated**: In A-Wiki's `skills/claude-thai/`
- **No action needed**: Fully covered

### 4.7 LLM-Wiki-Skilled (TrueHOOHA/LLM-Wiki-Skilled)
**Core**: Wiki management with vector search
- **Similar to**: A-Wiki's GraphRAG + FTS5
- **Should add**: Skill-based wiki querying (query wiki using "skills" as meta-layer), confidence-scored answers from wiki
- **Priority**: Medium — adds query sophistication

### 4.8 ai-modules (theafh/ai-modules) — knowledge_management
**Core**: Plugins for knowledge management
- **Should add**: Plugin architecture for wiki operations (pre/post hooks for ingest, search, synthesis)
- **Priority**: Low — A-Wiki already has hooks system

### 4.9 LLM-Wiki-Agent-Workflow-Demo (WayneChou-bot)
**Core**: Visual workflow for wiki operations
- **Should add**: Workflow automation for multi-step wiki tasks (ingest → source → entity → concept → synthesis), progress tracking for long operations
- **Priority**: Low — nice visualization but not critical

### 4.10 obsidian-llm-wiki-local (kytmanov/obsidian-llm-wiki-local)
**Core**: Private, offline wiki with local LLMs
- **Should add**: Local LLM integration (Ollama/LM Studio) for offline wiki operations, no-API-needed confidence marker
- **Priority**: High! — This is a major gap. A-Wiki has no offline mode.

### 4.11 long-term-agent-memory (eslamgenio/long-term-agent-memory)
**Core**: Embedding-based memory with forgetting mechanisms
- **Already inspired**: A-Wiki's embeddings
- **Should add**: Memory consolidation (importance scoring → auto-prune/archive), session-to-session memory decay, retrieval-augmented generation with memory weighting
- **Priority**: Medium

### 4.12 FrameCode-VibeWork (Sistema2D/FrameCode-VibeWork)
**Core**: Context-aware coding framework with vibe-based task routing
- **Unique idea**: Energy-aware scheduling (match task complexity to model capability), "vibe" detection (user mood/energy → suggest easier or harder tasks)
- **Should add**: Energy-aware delegation (route simple tasks to cheap models when user is tired), task effort estimation
- **Priority**: Low — experimental/novelty

### 4.13 synto (kytmanov/synto)
**Core**: Document → wiki synthesis
- **Already inspired**: A-Wiki's Phase 4c (auto-synthesis pipeline)
- **Should add**: Structure extraction (auto-detect sections, tables, code blocks), cross-document merge during synthesis
- **Priority**: Medium — validated by A-Wiki's existing design

### 4.14 synthadoc (axoviq-ai/synthadoc)
**Core**: AI-powered documentation synthesis with quality scoring
- **Already inspired**: A-Wiki's quality scoring rubric (Phase 4c)
- **Should add**: Automated quality improvement suggestions (not just scoring), iterative refinement loop for low-scoring pages
- **Priority**: Low — Phase 4c design is sufficient for v1

### 4.15 link (gowtham0992/link)
**Core**: Explicit link/relationship management between knowledge nodes
- **Different from**: A-Wiki's auto-generated graph links
- **Should add**: User-defined relationship types