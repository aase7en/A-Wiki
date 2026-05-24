# Model Roster — A-Wiki Model Inventory

> **Source:** Inspired by InW-Wiki `model-roster` script ecosystem.
> **Purpose:** Track which models are available, benchmarked, and preferred for specific tasks.

---

## Reference Models (External Repos)

| Model / Provider | Source | Strengths | A-Wiki Use Case |
|---|---|---|---|
| **claude-code** | A-Wiki primary | Reasoning, architecture, Thai skills, multi-step | All core operations |
| **claude-thai-skills** | [Boom-Vitt/claude-thai-skills](https://github.com/Boom-Vitt/claude-thai-skills) | Thai language, PDPA, gov forms, addresses | Thai-specific operations |
| **OmegaWiki** | [skyllwt/OmegaWiki](https://github.com/skyllwt/OmegaWiki) | Wiki knowledge graph, entity extraction | Knowledge graph enrichment |
| **MiroFish** | [666ghj/MiroFish](https://github.com/666ghj/MiroFish) | Multi-agent workflow | Swarm orchestration reference |
| **GitNexus** | [abhigyanpatwari/gitnexus](https://github.com/abhigyanpatwari/gitnexus) | Git workflow automation | CI/CD improvement reference |
| **everything-claude-code** | [affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code) | Comprehensive skill collection | Skill library expansion |
| **LLM-Wiki-Skilled** | [TrueHOOHA/LLM-Wiki-Skilled](https://github.com/TrueHOOHA/LLM-Wiki-Skilled) | Wiki skill system | Skill definition patterns |
| **LLM-Wiki-Agent-Workflow-Demo** | [WayneChou-bot/LLM-Wiki-Agent-Workflow-Demo](https://github.com/WayneChou-bot/LLM-Wiki-Agent-Workflow-Demo) | Agent workflow patterns | Workflow automation |
| **ai-modules** | [theafh/ai-modules](https://github.com/theafh/ai-modules) | Knowledge management plugins | Plugin architecture |
| **long-term-agent-memory** | [eslamgenio/long-term-agent-memory](https://github.com/eslamgenio/long-term-agent-memory) | Memory management | Session memory improvements |
| **FrameCode-VibeWork** | [Sistema2D/FrameCode-VibeWork](https://github.com/Sistema2D/FrameCode-VibeWork) | Vibe coding framework | Development workflow |
| **synto / synthadoc** | [kytmanov/synto](https://github.com/kytmanov/synto), [axoviq-ai/synthadoc](https://github.com/axoviq-ai/synthadoc) | Document synthesis | Documentation generation |
| **link** | [gowtham0992/link](https://github.com/gowtham0992/link) | Knowledge linking | Cross-reference system |
| **llm-wiki-manager** | [sametbrr/llm-wiki-manager](https://github.com/sametbrr/llm-wiki-manager) | Wiki management | Administration tools |
| **LLM-WIKI-MCP** | [Electro-resonance/LLM-WIKI-MCP](https://github.com/Electro-resonance/LLM-WIKI-MCP) | MCP integration | MCP server configuration |
| **9arm-skills** | [thananon/9arm-skills](https://github.com/thananon/9arm-skills) | Additional skill collection | Skill expansion |
| **obsidian-llm-wiki-local** | [kytmanov/obsidian-llm-wiki-local](https://github.com/kytmanov/obsidian-llm-wiki-local) | Obsidian integration | Obsidian sync reference |

---

## Task-to-Model Mapping

| Task | Recommended Model | Rationale |
|---|---|---|
| Architecture/design decisions | claude-code | Strong reasoning, context-aware |
| Thai language operations | claude-code + claude-thai-skills | Specialized Thai NLP skills |
| Wiki knowledge graph | claude-code + OmegaWiki patterns | Entity extraction + graph queries |
| Code generation | claude-code | Best-in-class code generation |
| Document synthesis | Synto/synthadoc patterns | Specialized doc gen |
| Memory management | long-term-agent-memory patterns | Cross-session context |
| CI/CD automation | GitNexus patterns | Git workflow specialization |
| Obsidian integration | obsidian-llm-wiki-local patterns | Vault sync |
| MCP integration | LLM-WIKI-MCP patterns | Tool server config |

---

## Benchmarking Notes

- All benchmarking is **informal** — based on observed performance
- Thai language tasks: claude-code outperforms others for nuanced Thai
- Long context: claude-code handles 200K tokens effectively
- For swarm delegation: use OpenRouter models via `delegate.sh`