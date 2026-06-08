---
type: source
title: "AI Myths Busted — rohitg00/ai-engineering-from-scratch"
slug: ai-engineering-myths
date_ingested: 2026-06-08
original_file: raw/ai-engineering-myths.md
tags: [ai-engineering, myths, misconceptions, llm, agents, fine-tuning, rag, scaling]
domain: ai-tools
license: MIT
upstream: https://github.com/rohitg00/ai-engineering-from-scratch/blob/main/glossary/myths.md
---

# AI Myths Busted (Source Summary)

**ประเภท**: reference / myth-busting
**วันที่**: 2026
**ผู้เขียน**: Rohit Ghumare (MIT License)
**จำนวน myths**: 20 ความเชื่อผิดๆ เกี่ยวกับ AI/ML

## ประเด็นหลัก

1. **Pattern Matching ≠ Understanding** — LLMs predict next token จาก statistical patterns ไม่ใช่ reasoning
2. **Size ≠ Intelligence** — Data quality สำคัญเท่ากับ parameter count (Chinchilla, Phi-2)
3. **AI Agents ≠ Autonomous** — Autonomy มาจาก loop ที่ developer เขียน ไม่ใช่ self-awareness
4. **Fine-tuning ≠ New Knowledge** — ใช้ RAG สำหรับ new facts, fine-tune สำหรับ behavior/style

## Myths ที่สำคัญสำหรับ A-Wiki Context

| Myth | Reality | Impact ต่อ A-Wiki |
|------|---------|------------------|
| "AI understands language" | Pattern matching | Design systems around this constraint |
| "Bigger context = better" | Lost-in-the-middle problem | RAG + targeted retrieval > stuffing full docs |
| "Agents are autonomous" | Loop + LLM decision-making | ออกแบบ loop, tools, guardrails ให้ดี |
| "Fine-tuning adds knowledge" | Only adjusts behavior | ใช้ RAG สำหรับ A-Wiki knowledge queries |
| "Temperature = creativity" | Randomness knob only | ปรับตามความต้องการ determinism |
| "Open source = open weights" | Training data/code อาจไม่รวม | ตรวจสอบ license ให้ครบ |

## ข้อมูลที่ขัดแย้งกับความเข้าใจทั่วไป

- "RLHF aligns AI with human values" → ผิด — align กับ preferences ของ raters เฉพาะกลุ่ม
- "Transformers understand order" → ผิด — positional encoding เป็น hack
- "Neural networks are black boxes" → ผิด (บางส่วน) — mechanistic interpretability กำลังพัฒนา

## หน้า Wiki ที่ได้รับการอัปเดต / สร้างใหม่

- [[concepts/ai-tools/ai-myths]] ← concept index สร้างใหม่
- [[concepts/ai-tools/ai-glossary]] ← cross-ref กับ glossary
