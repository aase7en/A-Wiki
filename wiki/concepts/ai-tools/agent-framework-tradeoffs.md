---
type: concept
tags: [agent-framework, system-prompt, context-injection, local-llm, prompt-engineering, tradeoff]
sources: [agent-frameworks-local-debug-2026, wiki/sources/ai-tools/langchain-framework.md]
created: 2026-05-02
updated: 2026-05-02
---

# Agent Framework Tradeoffs — Lean vs Autonomous

## นิยาม

Tradeoff ระหว่าง 3 แกนของ AI agent design — **ขนาด system prompt**, **context injection strategy**, และ **resource requirement** — ที่กำหนดว่า agent จะเหมาะกับ deployment แบบไหน (local-first, cloud-first, embedded)

## ทำไมถึงสำคัญ

ในยุคที่ทุกคน build agent กันเอง ความเชื่อผิดที่พบบ่อย: "agent ซับซ้อนกว่า = ดีกว่า" — จริงๆ แล้ว agent ที่ดีคือ agent ที่ match กับ **environment** + **task** ไม่ใช่ agent ที่ feature เยอะที่สุด

## 3 Style หลัก (Spectrum)

### A. Lean / Surgical — เช่น thClaws, Claude Code minimal config

- **System prompt**: สั้น, tool definitions + instruction ขั้นต่ำ
- **Context injection**: เฉพาะกิจ (อ่านไฟล์ก็ใส่เฉพาะไฟล์, รัน command ก็ใส่ env เฉพาะ)
- **Pros**: token ต่ำ, รัน local model quantized + ctx เล็กได้, predictable
- **Cons**: ไม่คิดแทนเรามาก, dev ต้องกำกับ direction
- **เหมาะ**: tool runner, code execution, local production บน Q4/Q5 + ctx 8-16k

### B. Autonomous Specialist — เช่น Hermes Agent

- **System prompt**: ใหญ่ — persona + decision rules + skill metadata + memory preload + few-shot
- **Context injection**: preload memory (preferences, durable facts, session summary) ก่อน user พิมพ์
- **Pros**: ลด round-trip, error ระยะยาวต่ำ, ทำงาน autonomous ได้
- **Cons**: กิน ctx ตั้งแต่ token แรก, ถ้า ctx <16k อาจ "เปิดไม่ขึ้น"
- **เหมาะ**: long-running assistant, multi-session memory, hardware แรงหรือ cloud LLM

### C. Heavy Orchestrator — เช่น OpenClaw

- **System prompt**: หลาย layer (planner / executor / tool wrapper) — แต่ละ layer add tokens แอบๆ
- **Context injection**: prompt overhead หลายหมื่นตัวอักษร, memory file accumulate ตลอด
- **Pros**: plan-reflect-act-verify flow, ทำ task ซับซ้อนได้
- **Cons**: prefill phase นาน (อาจ ~1 นาทีบน local), idle timeout ตัด, silent failure บ่อย
- **เหมาะ**: cloud-only, GPU แรง, task ที่ต้อง multi-step planning จริงๆ

## Decision Matrix

| ปัจจัย | Lean | Autonomous | Orchestrator |
|---|---|---|---|
| Local + Q4/Q5 quantized | ✅ | ⚠️ ต้อง 16k+ | ❌ |
| Local + GPU แรง / ctx 32k+ | ✅ | ✅ | ⚠️ |
| Cloud LLM (Claude/GPT) | ⚠️ underused | ✅ | ✅ |
| Latency-critical | ✅ | ⚠️ | ❌ |
| Multi-step complex task | ❌ ต้องช่วย | ✅ | ✅✅ |
| Memory long-term | ❌ | ✅ | ✅ |
| Privacy-first | ✅ | ⚠️ | ❌ |

## ข้อสังเกต / ข้อขัดแย้งกับบทความต้นฉบับ

- บทความเสนอว่า "lean = local-first" — จริงเฉพาะกรณี hardware จำกัด ถ้ามี M3 Ultra / RTX 4090 → autonomous ก็ local ได้
- "Rust runtime → ดีกว่า Python" — bottleneck จริงของ local agent คือ **inference latency** ไม่ใช่ orchestration overhead
- ไม่พูดถึง **dynamic context management** (compaction, RAG, summarization) — ซึ่งสำคัญกว่าทั้ง system prompt design และ context injection ใน production ระยะยาว

## Pattern ที่แนะนำใน production

> **"Hybrid stack"** — แต่ละ layer ใช้ style ที่เหมาะ
>
> - **Execution layer**: lean (Claude Code / thClaws) — รัน tool, edit file
> - **Reasoning layer**: autonomous (Hermes / Claude API กับ thinking) — วางแผน, ตัดสินใจ
> - **Orchestration layer**: เท่าที่จำเป็น (cron, webhook) — ไม่ต้อง full orchestrator

## ความสัมพันธ์

- Implement: [[entities/ai-tools/hermes-agent]] — ตัวอย่าง Autonomous Specialist
- เปรียบเทียบ: [[concepts/ai-tools/openrouter-claude-code]] — Claude Code = lean execution layer
- Cross-domain: pattern เดียวกันใช้กับ Claude+Gemini delegation workflow ใน [[CLAUDE.md]]

## แหล่งข้อมูล

- [[sources/agent-frameworks-local-debug-2026]]
