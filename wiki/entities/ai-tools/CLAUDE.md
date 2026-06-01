> **Cost-First**: ก่อนให้ Claude ทำงานใดๆ ใน domain นี้ → ดู [Cost-First Pyramid](/CLAUDE.md#-cost-first-decision-pyramid-บังคับคิดก่อนทุกงาน)
> Hook → Free API → Cheap paid (DeepSeek/Qwen) → Subagent Haiku → Claude Sonnet
> **Prompt ส่งออกนอก: ใช้ภาษาอังกฤษเสมอ** (ประหยัด token ~30%)

---


# Scoped Context — AI Tools Entities

> **โดเมน**: AI Tools
> **Last updated**: 2026-06-02
> **ไฟล์นี้เป็น nested context สำหรับ Claude/Cline — อ่านเมื่อทำงานใน entities/ai-tools/ เท่านั้น**

---

## Entities ที่มีอยู่ (2)

| Slug | Abstract |
|------|----------|
| `hermes-agent` | Open-source AI agent framework — CLI, ต่อ LLM หลาย provider, messaging gateway (Telegram, Discord) |
| `telegram-ai-router` | Bot Telegram ส่วนตัวบน Mac Mini — gateway รับข้อความ → route ไป AI model อัตโนมัติ |

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