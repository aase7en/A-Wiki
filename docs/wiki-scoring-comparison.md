# A-Wiki Scoring Comparison Matrix

> เปรียบเทียบ A-Wiki กับ 15 Repos + InW-Wiki  
> 10 Dimensions × 1-10 scale  
> วันที่: 2026-05-25

---

## Scoring Dimensions

| # | Dimension | น้ำหนัก | คำอธิบาย |
|---|-----------|---------|----------|
| 1 | **Wiki Core** | ⭐⭐⭐ | Knowledge graph, FTS5 search, indexing, entity management, synthesis pipeline |
| 2 | **Agent Layer** | ⭐⭐⭐ | Agent orchestration, delegation, multi-model routing, subagent, swarm |
| 3 | **Hooks/Automation** | ⭐⭐⭐ | Pre/post lifecycle hooks, automated workflows, CI/CD integration |
| 4 | **Skills** | ⭐⭐⭐ | Skill library breadth, ecosystem integration, domain-specific skills |
| 5 | **Cost Optimization** | ⭐⭐⭐ | Free tier models, token saving, model routing, cost pyramid |
| 6 | **Domain Depth** | ⭐⭐ | IoT, pharmacy, environment, AI-tools specialization |
| 7 | **Cross-Device** | ⭐⭐ | Sync daemon, multi-machine, collaboration |
| 8 | **External Integration** | ⭐⭐ | GitHub, arXiv, Google Drive, MCP, NotebookLM |
| 9 | **Code Quality** | ⭐⭐ | Tests, linting, error handling, maintainability |
| 10 | **Documentation** | ⭐ | README, protocols, runbooks, getting-started quality |

---

## Scoring Table

| Rank | Repo | Wiki Core | Agent Layer | Hooks | Skills | Cost Opt. | Domain Depth | Cross-Device | Ext. Integration | Code Quality | Docs | **TOTAL** |
|------|------|:---------:|:-----------:|:-----:|:------:|:---------:|:------------:|:------------:|:---------------:|:------------:|:----:|:---------:|
| 1 | **A-Wiki** 🏆 | **9** | **8** | 7 | **9** | 7 | **9** | 5 | **8** | 7 | **9** | **78** |
| 2 | OmegaWiki | **10** | 6 | 7 | 5 | 6 | 5 | 5 | 7 | **9** | **9** | 69 |
| 3 | InW-Wiki | 7 | 7 | **9** | 6 | **8** | 7 | **7** | 6 | 6 | 7 | 70 |
| 4 | ECC (everything-claude-code) | 4 | **10** | **9** | **9** | 6 | 3 | **7** | 8 | 8 | 7 | 71 |
| 5 | LLM-Wiki-Skilled | 8 | 7 | 6 | 8 | 5 | 5 | 5 | 6 | 7 | 8 | 65 |
| 6 | ai-modules (theafh) | 8 | 7 | 8 | 6 | 4 | 4 | 5 | 5 | 8 | 7 | 62 |
| 7 | MiroFish | 7 | 5 | 4 | 4 | 3 | 4 | 6 | 6 | 5 | 4 | 48 |
| 8 | GitNexus | 3 | 4 | 5 | 3 | 2 | 2 | **7** | 5 | 6 | 5 | 42 |
| 9 | long-term-agent-memory | 5 | 6 | 5 | 4 | 4 | 3 | 4 | 4 | 5 | 4 | 44 |
| 10 | 9arm-skills | 2 | 3 | 2 | 7 | 2 | 1 | 2 | 2 | 4 | 3 | 28 |
| 11 | obsidian-llm-wiki-local | 7 | 4 | 3 | 4 | 3 | 3 | 5 | 5 | 6 | 6 | 46 |
| 12 | synto | 5 | 5 | 4 | 3 | 4 | 2 | 3 | 3 | 5 | 4 | 38 |
| 13 | FrameCode-VibeWork | 3 | 5 | 4 | 3 | 3 | 2 | 3 | 4 | 5 | 3 | 35 |
| 14 | synthadoc | 6 | 4 | 3 | 3 | 3 | 2 | 3 | 3 | 5 | 4 | 36 |
| 15 | link | 3 | 2 | 2 | 2 | 2 | 1 | 2 | 3 | 4 | 3 | 24 |
| 16 | llm-wiki-manager | 6 | 5 | 4 | 3 | 3 | 2 | 4 | 5 | 5 | 4 | 41 |
| 17 | LLM-WIKI-MCP | 7 | 4 | 5 | 3 | 5 | 2 | 3 | **8** | 6 | 6 | 49 |
| 18 | LLM-Wiki-Agent-Workflow-Demo | 4 | 5 | 6 | 3 | 3 | 2 | 4 | 4 | 5 | 5 | 41 |

---

## Detailed Scoring Breakdown

### 🥇 A-Wiki — 78/100

| Dimension | Score | Rationale |
|-----------|:-----:|-----------|
| Wiki Core | **9** | 5-edge typed knowledge graph (depends_on, implements, synthesizes, relates, deprecated_by), FTS5 search, 4 auto-generated domain indexes (IoT, env, AI-tools, pharmacy), embeddings JSON, graph JSON, 131 nodes, 168 edges, Canvas visualization. รองรับเฉพาะ typed edges |
| Agent Layer | **8** | delegate.sh 5-tier + race mode (3 parallel models), swarm intelligence directory (model-scouter, agile-swarm), subagent delegation, crew dispatch, 3 engineering skills (debug-mantra, post-mortem, scrutinize). ขาด OpenRouter direct integration |
| Hooks | **7** | 5 Python hooks (session_start, check_bash_destructive_git, check_bash_no_branch, check_claudemd_lock, check_raw_immutable), hooks_runner.py, post-wiki-edit-gen-index ขาด secret-leak check, apikey-check |
| Skills | **9** | 100+ ecosystem skills (ECC linked), 14 Thai skills, 15 claude-code skills, skill-creator skill, symlink connector. ใหญ่ที่สุดใน ecosystem |
| Cost Opt. | **7** | ask-notebooklm.py (Gemini free API), delegate.sh tier system, review-check.py reduces wasted tokens. ยังไม่มี cost pyramid enforcement ใน CLAUDE.md |
| Domain Depth | **9** | 4 domains (IoT, pharmacy, env, AI-tools) with domain-specific scripts: fetch-arxiv.py, review-check.py, pharmacy-order-lookup skill, env synthesis, ecosystem connectors. โดดเด่นกว่า repo อื่น |
| Cross-Device | **5** | GitHub Actions workflow (disabled due to PAT), Google Drive symlink for raw/. ไม่มี sync daemon |
| Ext. Integration | **8** | arXiv auto-fetch (4 domains), GitHub auto-sync, Google Drive raw storage, NotebookLM export, MCP server (mcp-wiki-server.py), Obsidian skills doc |
| Code Quality | **7** | review-check.py (6-layer health checker), test-zone with pytest, gen-index.py validation. Limited test coverage |
| Docs | **9** | 12 protocols, 3 runbooks, architecture.md, getting-started.md, OBSIDIAN_SKILLS.md, Home.md/index.md, 5 decisions. ละเอียดที่สุดใน ecosystem |

**Strengths**: Ecosystem skills, domain depth, documentation, wiki core  
**Weaknesses**: Cross-device sync, hooks incompleteness, code quality (test coverage)

---

### 🥈 ECC (everything-claude-code) — 71/100

| Dimension | Score | Rationale |
|-----------|:-----:|-----------|
| Wiki Core | 4 | Not a wiki — agent harness |
| Agent Layer | **10** | 60 agents, 232 skills, NanoClaw v2 orchestration, PM2 parallelization, cascade execution |
| Hooks | **9** | 1282 security tests, 102 rules, hook runtime with profile levels, AgentShield |
| Skills | **9** | 232 skills, 12 language ecosystems, skill evolution foundation |
| Cost Opt. | 6 | Model routing, but not wiki-specific |
| Domain Depth | 3 | General-purpose, no domain specialization |
| Cross-Device | 7 | PM2, Git worktrees, parallel execution |
| Ext. Integration | 8 | GitHub App marketplace, multi-harness support |
| Code Quality | 8 | 997+ internal tests, 1282 security tests, manifest-driven install |
| Docs | 7 | Extensive but scattered |

**Unique**: Agent layer unmatched — 60 agents, 232 skills, NanoAgent orchestration  
**Weakness**: ไม่ใช่ wiki — ขาด knowledge graph, synthesis, entity management

---

### 🥉 InW-Wiki — 70/100

| Dimension | Score | Rationale |
|-----------|:-----:|-----------|
| Wiki Core | 7 | FTS5 search, graph build, but fewer typed edges |
| Agent Layer | 7 | delegate.sh (5-tier + race mode), subagent delegation |
| Hooks | **9** | 16 hooks across 5 lifecycle events — มากที่สุดใน ecosystem |
| Skills | 6 | 4 skills only (ask-notebooklm, delegate-subagent, lint-wiki, search-local) |
| Cost Opt. | **8** | Cost pyramid (Level -1 to 4), ask-notebooklm (Gemini free), OpenRouter free/cheap, race mode |
| Domain Depth | 7 | Pharmacy depth (6 scripts), IoT |
| Cross-Device | 7 | sync.py daemon (file watcher + pull/push), device detection |
| Ext. Integration | 6 | GitHub, limited |
| Code Quality | 6 | Fewer tests, manual lint |
| Docs | 7 | Good but less comprehensive than A-Wiki |

**Unique**: Cost pyramid enforcement + 16 hooks + sync daemon  
**Weakness**: Skills ecosystem, cross-device maturity

---

### 4. OmegaWiki — 69/100

| Dimension | Score | Rationale |
|-----------|:-----:|-----------|
| Wiki Core | **10** | Best in class — 9 entities, 18 edges, 3 visualization modes (web SPA, Obsidian, Canvas), auto-backlinks via xref.yaml |
| Agent Layer | 6 | Agent-guided pipeline but no swarm |
| Hooks | 7 | Lifecycle hooks but fewer |
| Skills | 5 | Skill definitions but limited scope |
| Cost Opt. | 6 | Tiered model use but no race mode |
| Domain Depth | 5 | Academic papers focus |
| Cross-Device | 5 | Git-based sync |
| Ext. Integration | 7 | API, web search, arXiv |
| Code Quality | 9 | Well-structured Python, clean architecture |
| Docs | 9 | Excellent documentation |

**Takeaway**: OmegaWiki เหนือกว่า A-Wiki ตรง Wiki Core (entity model, visualization, auto-backlinks) — ควรศึกษา

---

### 5. LLM-Wiki-Skilled — 65/100

| Dimension | Score | Rationale |
|-----------|:-----:|-----------|
| Wiki Core | 8 | Obsidian wikilinks, BM25/vector search (qmd), synthesis, 6 lint checks |
| Agent Layer | 7 | Skill orchestration layer |
| Hooks | 6 | Lint checks automation |
| Skills | 8 | 25+ skill definitions |
| Cost Opt. | 5 | No explicit cost tier |
| Domain Depth | 5 | General purpose |
| Cross-Device | 5 | Git sync |
| Ext. Integration | 6 | Obsidian, LLM |
| Code Quality | 7 | Well-structured |
| Docs | 8 | Good documentation |

**Takeaway**: Skill orchestration + linting system ควรศึกษา

---

### 6-18. Remaining Repos

#### 6. ai-modules (theafh) — 62/100
Karpathy wiki pattern, sha256 drift detection, wiki_auto_shaper agent  
**A-Wiki ควรเรียน**: auto_shaper concept + SHA256 provenance

#### 7. LLM-WIKI-MCP — 49/100
MCP server + local Ollama + SQLite FTS  
**A-Wiki ควรเรียน**: MCP protocol integration (A-Wiki มี mcp-wiki-server.py อยู่แล้ว)

#### 8. MiroFish — 48/100
Git-based knowledge mesh, interesting but complex  
**A-Wiki ควรเรียน**: Git workflow patterns

#### 9. obsidian-llm-wiki-local — 46/100
Obsidian integration best practices  
**A-Wiki ควรเรียน**: Obsidian workflow refinement

#### 10. long-term-agent-memory — 44/100
Episodic + semantic memory layer  
**A-Wiki ควรเรียน**: Memory architecture for agent persistence

#### 11. GitNexus — 42/100
Git repository integration  
**A-Wiki ควรเรียน**: Multi-repo workflow

#### 12. llm-wiki-manager — 41/100
API-first wiki management  
**A-Wiki ควรเรียน**: API design patterns

#### 13. LLM-Wiki-Agent-Workflow-Demo — 41/100
Workflow demonstration  
**A-Wiki ควรเรียน**: CI/CD pipeline design

#### 14. synto — 38/100
Synthesis tool  
**A-Wiki ควรเรียน**: Synthesis workflow (A-Wiki มีแล้วผ่าน ask-notebooklm.py)

#### 15. synthadoc — 36/100
Synthetic documentation  
**A-Wiki ควรเรียน**: Documentation generation patterns

#### 16. FrameCode-VibeWork — 35/100
Productivity framework  
**A-Wiki ควรเรียน**: Productivity workflow patterns

#### 17. 9arm-skills — 28/100
Skill collection  
**A-Wiki มีแล้ว**: Thai skills ครบถ้วนกว่า

#### 18. link — 24/100
Link management  
**A-Wiki ควรเรียน**: Link management patterns

---

## Radar Chart Values (for visualization)

```
A-Wiki:        [9, 8, 7, 9, 7, 9, 5, 8, 7, 9]  → 78
ECC:           [4, 10, 9, 9, 6, 3, 7, 8, 8, 7] → 71
InW-Wiki:      [7, 7, 9, 6, 8, 7, 7, 6, 6, 7]  → 70
OmegaWiki:     [10, 6, 7, 5, 6, 5, 5, 7, 9, 9]  → 69
LLM-Wiki-Sk:   [8, 7, 6, 8, 5, 5, 5, 6, 7, 8]  → 65
```

---

## Gap Analysis: A-Wiki → 100

| Dimension | Current | Target | Gap | What to Add |
|-----------|:-------:|:------:|:---:|-------------|
| Wiki Core | 9 | 10 | 1 | OmegaWiki-style 9 entity types + 18 edge types + auto-backlinks via xref.yaml |
| Agent Layer | 8 | 10 | 2 | ECC-style 60 agents scale, NanoAgent orchestration, AgentShield security |
| Hooks | 7 | 10 | 3 | InW-Wiki 16 hooks (secret-leak, apikey-check, no-branch enforcement, post-wiki-edit-gen-index) |
| Skills | 9 | 10 | 1 | ECC-style skill evolution, ai-modules auto_shaper |
| Cost Opt. | 7 | 10 | 3 | InW-Wiki cost pyramid enforcement, OpenRouter integration, Groq/DeepSeek free tier |
| Domain Depth | 9 | 10 | 1 | InW-Wiki pharmacy automation scripts (6 scripts) |
| Cross-Device | 5 | 10 | 5 | **Biggest gap** — sync.py daemon, device detection, conflict resolution |
| Ext. Integration | 8 | 10 | 2 | LLM-WIKI-MCP MCP protocol depth, multi-repo GitNexus |
| Code Quality | 7 | 10 | 3 | ECC 997+ tests, ai-modules SHA256 drift detection, typed Python |
| Docs | 9 | 10 | 1 | OmegaWiki-style interactive visualization + auto-generated docs |

---

## Summary

```
🏆 A-Wiki:         78/100  — Best overall (domain depth + skills + docs)
🥈 ECC:            71/100  — Best agent layer (60 agents, 232 skills)
🥉 InW-Wiki:       70/100  — Best hooks + cost pyramid + sync daemon
   OmegaWiki:      69/100  — Best wiki core (9 entities, 18 edges)
   LLM-Wiki-Sk:    65/100  — Best skill orchestration + linting
```

**A-Wiki อยู่อันดับ 1 จาก 18 Repos** ด้วยคะแนน 78/100  
แต่มี gap ชัดเจนใน Cross-Device (5/10), Hooks (7/10), Cost Optimization (7/10), Code Quality (7/10)

---

*วิเคราะห์โดย Cline — 2026-05-25*