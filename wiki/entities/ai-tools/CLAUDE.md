> **Cost-First**: ก่อนให้ Claude ทำงานใดๆ ใน domain นี้ → ดู [Cost-First Pyramid](/CLAUDE.md#-cost-first-decision-pyramid-บังคับคิดก่อนทุกงาน)
> Hook → Free API → Cheap paid (DeepSeek/Qwen) → Subagent Haiku → Claude Sonnet
> **Prompt ส่งออกนอก: ใช้ภาษาอังกฤษเสมอ** (ประหยัด token ~30%)

---


# Scoped Context — AI Tools Entities

> **โดเมน**: AI Tools
> **Last updated**: 2026-07-21
> **ไฟล์นี้เป็น nested context สำหรับ Claude/Cline — อ่านเมื่อทำงานใน entities/ai-tools/ เท่านั้น**

---

## Entities ที่มีอยู่ (33)

| Slug | Abstract |
|------|----------|
| `ag2-orchestrator` | AG2 Goal Orchestrator — Planner→Executor→Validator loop; free-model executors via delegate.sh; wiki_search() ก่อนเสมอ |
| `hermes-agent` | Open-source AI agent framework — CLI, ต่อ LLM หลาย provider, messaging gateway (Telegram, Discord) |
| `telegram-ai-router` | Bot Telegram ส่วนตัวบน Mac Mini — gateway รับข้อความ → route ไป AI model อัตโนมัติ |
| `ecc` | ECC — Everything Claude Code: 249 skills + 63 agents สำหรับ optimize agent workflow ข้าม harness |
| `9arm-skills` | claude-thai-skills: 12 Thai language skills — fuzzy-search, thai-ocr, line-bot |
| `anthropic-skills` | Official Anthropic skill collection: 17 skills (docx/pdf/xlsx/pptx + creative + claude-api) ที่ `skills/anthropic-skills/` |
| `gitnexus` | Code knowledge graph MCP — 16 tools, impact analysis, symbol navigation (PolyForm Noncommercial) |
| `turbovec` | Alt vector backend (turbovec) — 16x compression vs sqlite-vec, future-scale option |
| `react-doctor` | React static analysis Claude skill — ตรวจ component health สำหรับ dream projects |
| `agents-md-spec` | AGENTS.md format standard (21.8k★) — multi-agent config spec สำหรับ Claude/Codex/Gemini/Cursor |
| `frontend-slides` | frontend-slides v2.1.0 — Zero-dep HTML deck generator + 34 bold templates + PPTX/PDF export |
| `social-media-skills` | Social media content creation skills collection |
| `hyperframes` | Hyperframes — อ้างอิงในบริบท AI/agent framework |
| `ollama` | Ollama — local LLM runtime สำหรับรัน model บน Mac Mini M4 |
| `pocketbase` | PocketBase — lightweight backend-as-a-service สำหรับ IoT + dream projects |
| `graphify` | Graphify — แปลงไฟล์ (code/PDF/image) เป็น interactive knowledge graph, 71.5x token reduction, MCP server |
| `openmed` | OpenMed v1.5.5 — on-device healthcare AI: drug/disease NER, HIPAA PII detection, de-identification, 1000+ models |
| `taste-skill` | Taste Skill (59.4k★) — anti-slop frontend taste layer, 11 variants — candidate ยังไม่ติดตั้ง |
| `ui-ux-pro-max` | UI UX Pro Max — searchable design DB (161 palettes/57 font pairs/99 UX rules, 10 stacks) — candidate |
| `transitions-dev` | Transitions.dev — 18 CSS transitions + audit workflow, framework-agnostic — candidate |
| `claude-mem` | Claude-Mem (87k★) — auto-capture memory (SQLite+vector) — ประเมินก่อน เทียบ gbrain/session-memory |
| `superpowers` | Superpowers (253k★, obra) — methodology framework — track upstream, keep ours |
| `context7` | Context7 (59k★, Upstash) — live version-specific library docs MCP — candidate opt-in |
| `a-wiki-skill-architecture` | A-Wiki's universal 5-layer skill architecture — one registry, every agent surface auto-updates |
| `deer-flow` | DeerFlow (ByteDance) — full agent harness on LangGraph/LangChain — evaluated, rejected/not integrated |
| `gbrain` | GBrain (Garry Tan) — memory layer with synthesis + self-wiring knowledge graph, opt-in MCP |
| `live-dashboard` | Live Dashboard v2.2 — A-Wiki's own real-time HTTP+SSE monitor, auto-starts every session on :7790 |
| `mattpocock-skills` | Matt Pocock / AI Hero skills — grilling, TDD enforcement, deep-module architecture, upstream-tracked |
| `model-capability-bench` | Capability-based model ranking (SWE-bench/Terminal-Bench/NL2RepoBench) for swarm task allocation |
| `news-intelligence-pipeline` | News collection → filtering → light analysis → deep prediction, live on Hermes cron (Pi5), ~$0.50/mo |
| `omniroute` | OmniRoute — open-source multi-provider LLM gateway, 17 routing strategies, RTK+Caveman compression |
| `pake` | Pake — converts any webpage into a ~5MB native desktop app (Rust/Tauri), 20x lighter than Electron |
| `zai-glm` | Z.ai / GLM series — cost-first direct-API provider (OpenAI-compatible), reasoning/coding/agentic |
| `gamedev-skills` | gamedev-skills/awesome-gamedev-agent-skills — 6-skill Phaser/PixiJS/three.js subset, vendored 2026-07-14 |

---

## Agent stack ที่ใช้

```yaml
primary: Claude Code (Anthropic) — wiki agent, reasoning, synthesis
secondary: Gemini CLI (Google, free tier) — web search, lookup
alternative: Hermes Agent — autonomous tasks, skills
hardware: Mac Mini M4 (local LLM), Pi 5 (IoT frontend)
```

---

## Rules

1. **frontmatter บังคับ**: `type`, `category`, `tags`, `sources`, `created`, `updated`, `last_verified`, `verify_tool`
2. **confidence markers** ทุกครั้ง
3. **ข้อมูล time-sensitive** (API version, model release, ราคา) → delegate เสมอ ห้ามเดาจาก training
4. **OpenRouter routing**: Claude Code สามารถเปลี่ยน engine ผ่าน env var ได้

---

## ความสัมพันธ์กับ domains อื่น

| Domain | ความเกี่ยวข้อง |
|--------|---------------|
| IoT | AI agent ควบคุม/วิเคราะห์ IoT data, TinyML |
| Environmental Health | AI วิเคราะห์ข้อมูลสิ่งแวดล้อม |
| Pharmacy | Claude API สำหรับ OCR + drug validation |