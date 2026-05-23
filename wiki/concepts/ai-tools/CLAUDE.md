> **Cost-First**: ก่อนให้ Claude ทำงานใดๆ ใน domain นี้ → ดู [Cost-First Pyramid](/CLAUDE.md#-cost-first-decision-pyramid-บังคับคิดก่อนทุกงาน)
> Hook → Free API → Cheap paid (DeepSeek/Qwen) → Subagent Haiku → Claude Sonnet
> **Prompt ส่งออกนอก: ใช้ภาษาอังกฤษเสมอ** (ประหยัด token ~30%)

---


# Scoped Context — AI Tools Concepts

> **โดเมน**: AI Tools — Concepts  
> **Last updated**: 2026-05-09  
> **ไฟล์นี้เป็น nested context สำหรับ Claude/Cline — อ่านเมื่อทำงานใน concepts/ai-tools/ เท่านั้น**

---

## Concepts ที่มีอยู่ (5)

| Slug | Abstract |
|------|----------|
| `agent-framework-tradeoffs` | 3 styles: Lean (thClaws/Claude Code) vs Autonomous (Hermes) vs Orchestrator (OpenClaw) |
| `context-management` | /compact vs /clear — session lifecycle, plan-before-code, model matching สำหรับลด token 40-60% |
| `local-llm-routing` | Auto-route query → local model (free, slower) vs cloud API (cost, smarter) |
| `openrouter-claude-code` | Claude Code = "mask" — swap engine via 3 env vars |
| `session-setup` | Wiki ใช้สองระบบขนาน: Claude Code + Gemini CLI |

---

## Key Technical Concepts

### Agent Styles
| Style | Example | Use Case |
|-------|---------|----------|
| Lean | Claude Code, thClaws | Wiki editing, reasoning |
| Autonomous | Hermes Agent | Background tasks, skills |
| Orchestrator | OpenClaw | Multi-agent, complex pipeline |

### LLM Routing Decision
```
Query มาถึง
  ├─ ง่าย/ประจำ (≥70%) → Ollama local (ฟรี)
  └─ ซับซ้อน/ต้องการ reasoning → Claude API (จ่ายต่องาน)
```

---

## Rules

1. **frontmatter บังคับ**: `type`, `tags`, `sources`, `created`, `updated`
2. **confidence markers** ทุกครั้ง
3. **ข้อมูล time-sensitive** (model version, API changes) → delegate เสมอ
4. **Cross-reference**: เชื่อมโยง synthesis (dual-ai-workflow, digital-legacy-ai-architecture)

---

## ความสัมพันธ์

| Concept | Entity ที่เกี่ยวข้อง | Synthesis |
|---------|---------------------|-----------|
| agent-framework-tradeoffs | hermes-agent, telegram-ai-router | dual-ai-workflow |
| context-management | — | — |
| local-llm-routing | telegram-ai-router | dual-ai-workflow |
| openrouter-claude-code | — | — |
| session-setup | — | — |