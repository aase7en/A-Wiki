# ADR-0003: A-Wiki Improvement Plan (InW-Wiki Post-Mortem)

**Status:** Accepted  
**Date:** 2026-05-24  
**Author:** A-Wiki Agent  
**Domain:** Infrastructure, Security, Knowledge Management

---

## Context

After a comprehensive audit of `/Users/aase7en/Desktop/InW-Wiki` — a sister wiki with shared ancestry (same CLAUDE.md base, same `wiki/` entity/concept structure, same 224 wiki pages) — we identified **9 critical gaps** where A-Wiki lags behind in safety, automation, and knowledge infrastructure.

InW-Wiki has evolved independently with:
- 2,296 total files (vs A-Wiki's 989)
- 37 scripts (vs 26)
- 5 hook safety scripts (vs 0)
- Full MCP server integration (vs 0)
- Tiered free model routing via OpenRouter (vs document-only)
- Domain-specific index pages (vs 1 generic index)
- Raw document pipeline with 52 source files (vs 0)

Additionally, 17 external repos were reviewed for novel capabilities.

---

## Decision

Adopt a **4-phase improvement roadmap** with explicit priority ordering:

### Phase 1 — Security & Safety (Priority: Critical)

**1.1 Port Hook Safety Infrastructure** — Copy and adapt 5 hook scripts from InW-Wiki:

| Hook | Function | A-Wiki Adaptation Needed |
|------|----------|--------------------------|
| `check_claudemd_lock.py` | Password-protect CLAUDE.md | Use `.claude/lock.txt` path |
| `check_bash_destructive_git.py` | Block destructive git on dirty tree | Same logic, adjust repo root |
| `check_bash_no_branch.py` | Enforce "commit to main only" | Same logic |
| `check_raw_immutable.py` | Block writes to `raw/` | Create `raw/` dir first |
| `check_secret_leak.py` | Detect API keys in output | Same regex patterns |

**Integration:** These hooks work with `scripts/hooks_runner.py` (already exists in A-Wiki) via stdin JSON protocol.

**1.2 Setup MCP Configuration** — Create `.mcp.json` with:

| Server | Tool | Purpose |
|--------|------|---------|
| `playwright` | browser automation | E2E testing, web scraping |
| `firecrawl` | web scraping | Source ingestion |
| `perplexity` | AI search | Web research augmentation |
| `markitdown` | doc conversion | Convert PDF/DOCX → markdown |

**1.3 Create `raw/` Directory** — Protected by `check_raw_immutable.py`:
```
raw/
raw/README.md        — explain raw/ policy
raw/iot/             — raw IoT documents
raw/environment/     — raw environmental docs
raw/pharmacy/        — raw pharmacy docs
raw/it/              — raw IT docs
raw/ai/              — raw AI docs
```

### Phase 2 — Intelligence & Routing (Priority: High)

**2.1 Tiered Free Model Routing**

Create `wiki/context/model-roster.md` with OpenRouter free-tier models:

| Tier | Task | Champion Model |
|------|------|----------------|
| T1 | search / lookup / summarize | `deepseek/deepseek-chat-v3-0324:free` |
| T2 | reason / compare / analyze | `deepseek/deepseek-r1:free` |
| T3 | scan / long-context | `qwen/qwen3-30b-a3b:free` |

Create `scripts/update-model-roster.sh` — queries OpenRouter API for top-5 free models.

**2.2 Parallel Race Mode**

Add to `scripts/delegate.sh`:
```bash
# Race mode: send prompt to top-3 free models simultaneously
# Use first response that returns (timeout: 30s per model)
delegate_sh race "<prompt>"  # runs deepseek, qwen, llama in parallel
```

**2.3 Domain Index Pages**

Create `index-{domain}.md` files for:
- `index-iot.md` — Internet of Things knowledge
- `index-env.md` — Environmental monitoring
- `index-ai.md` — AI/ML concepts
- `index-pharmacy.md` — Pharmacy domain
- `index-it.md` — IT support knowledge

Each auto-generated from `scripts/gen-index.py --domain <name>`.

### Phase 3 — Knowledge Infrastructure (Priority: Medium)

**3.1 Port `scripts/sync.py` Daemon Mode**

Features to add:
- `--daemon` flag for continuous sync
- 10s scan interval with 5s debounce
- Auto `git stash` / `pull` / `rebase` / `push`
- Device-aware config from `~/.wiki-device`
- Periodic pull every 5 minutes
- Conflict resolution with `diff3` merge

**3.2 Wiki Context Files**

Create these tracking docs:
```
wiki/context/now.md           — Current focus & active tasks
wiki/context/wiki-state.md    — Health metrics (file count, stale pages, orphans)
wiki/context/wiki-guide.md    — Agent wiki writing guide
wiki/context/device-session.md— Multi-device session tracking
```

**3.3 Fill `wiki/sources/` and `wiki/synthesis/`**

| Directory | Current | Target |
|-----------|---------|--------|
| `wiki/sources/` | empty | 70 source summaries |
| `wiki/synthesis/` | empty | 26 cross-domain syntheses |

### Phase 4 — External Innovation (Priority: Low, Long-term)

**4.1 GraphRAG Layer** — Inspired by MiroFish (61.7K ★) and OmegaWiki
- Overlay knowledge graph on existing wiki entities
- Graph traversal for related concept discovery
- Mermaid visualization via `/graph` command

**4.2 MCP Wiki Server** — Inspired by LLM-WIKI-MCP
- Expose wiki search via MCP protocol
- Enable other agents to query wiki programmatically
- Standardized semantic search endpoint

**4.3 Auto-Synthesis Pipeline** — Inspired by synto/synthadoc
- `raw/` → structured markdown → wiki entity
- Automated cross-reference detection
- Quality scoring for generated content

---

## Consequences

### Positive
- **Hard safety guarantees** — hooks enforce Iron Laws at code level, not just documentation
- **Zero-cost intelligence** — OpenRouter free models eliminate API costs for 80% of tasks
- **Faster iteration** — sync daemon eliminates manual git workflow
- **Better discoverability** — domain indexes + graph visualization
- **Future-proof** — MCP server enables integration with any MCP-compatible agent

### Negative
- **Setup overhead** — each new device needs `.claude/lock.txt` and `WIKI_UNLOCK` env var
- **Learning curve** — team members must understand hook system
- **Free model reliability** — OpenRouter free tier models may have rate limits or go offline
- **Maintenance burden** — sync daemon adds complexity to git workflow

### Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Hook blocks legitimate work | `WIKI_UNLOCK` env var for CLAUDE.md; `git stash` fallback for destructive git |
| MCP servers break | `.mcp.json` has no dependencies on external servers — graceful degradation |
| Free model quality drops | Model roster auto-updates; fallback chain (T1 → T1-FB → T1-FB2) |
| Raw directory grows stale | Regular pruning via `scripts/lint-wiki/` pipeline |

---

## Implementation Notes

- **Hook scripts go in:** `scripts/hooks/` (new directory)
- **Hook runner already exists:** `scripts/hooks_runner.py`
- **MCP config at:** `.mcp.json` (root)
- **Lock file at:** `.claude/lock.txt` (create from `.claude/lock.example`)
- **Sync daemon:** `scripts/sync.py --daemon`
- **Model roster:** `wiki/context/model-roster.md` + `wiki/context/model-roster.conf`

---

## References

- [InW-Wiki](https://github.com/aase7en/InW-Wiki) — Sister wiki with full implementation
- [OmegaWiki](https://github.com/skyllwt/OmegaWiki) — Graph visualization approach
- [LLM-WIKI-MCP](https://github.com/Electro-resonance/LLM-WIKI-MCP) — MCP protocol for wikis
- [MiroFish](https://github.com/666ghj/MiroFish) — GraphRAG + agent memory injection (61.7K ★)
- [synto](https://github.com/kytmanov/synto) — Document → wiki synthesis
- [long-term-agent-memory](https://github.com/eslamgenio/long-term-agent-memory) — Embedding-based retrieval