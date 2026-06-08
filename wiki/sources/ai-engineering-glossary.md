---
type: source
title: "AI Engineering Glossary — rohitg00/ai-engineering-from-scratch"
slug: ai-engineering-glossary
date_ingested: 2026-06-08
original_file: raw/ai-engineering-glossary.md
tags: [ai-engineering, glossary, llm, embeddings, rag, agents, transformers, fine-tuning]
domain: ai-tools
license: MIT
upstream: https://github.com/rohitg00/ai-engineering-from-scratch/blob/main/glossary/terms.md
---

# AI Engineering Glossary (Source Summary)

**ประเภท**: reference / glossary
**วันที่**: 2026
**ผู้เขียน**: Rohit Ghumare (MIT License)
**ขนาด**: ~50 คำศัพท์ ครอบคลุม A–Z

## ประเด็นหลัก

1. **คำจำกัดความที่แม่นยำ** — แต่ละคำอธิบาย 3 ระดับ: สิ่งที่คนพูด / ความหมายจริง / เหตุผลที่เรียกแบบนั้น
2. **ครอบคลุม LLM Stack ทั้งหมด** — ตั้งแต่ Tensor, Autograd → Transformer, Attention → RAG, RLHF, Agents, MCP
3. **เน้น implementation reality** ไม่ใช่ marketing language เช่น "Temperature ≠ creativity, คือ randomness knob"

## คำสำคัญที่ A-Wiki ควรรู้

| Term | ความหมายสั้น |
|------|-------------|
| **Agent** | while loop: LLM + tools + loop |
| **RAG** | Retrieve docs → augment prompt → generate |
| **Fine-tuning** | ปรับ behavior, ไม่ใช่เพิ่ม knowledge ใหม่ |
| **KV Cache** | Cache keys/values → fast autoregressive inference |
| **MCP** | JSON-RPC protocol สำหรับ AI ← tools/resources |
| **Swarm** | Multi-agent + emergent behavior จาก simple rules |
| **LoRA / QLoRA** | Low-rank adapters for efficient fine-tuning |
| **Temperature** | Randomness knob for token selection |
| **Prompt Injection** | SQL injection equivalent for LLMs |

## ข้อมูลที่น่าสนใจ

- "More parameters ≠ smarter" — Phi-2 (2.7B) beat 70B models on benchmarks
- Fine-tuning ≠ adding new knowledge → ใช้ RAG แทน ถ้าต้องการ new facts
- Transformer treats input as SET not sequence → positional encoding เป็น workaround
- "AI agents are autonomous" = myth — autonomy มาจาก loop ที่ developer สร้าง ไม่ใช่ LLM

## หน้า Wiki ที่ได้รับการอัปเดต / สร้างใหม่

- [[concepts/ai-tools/ai-glossary]] ← concept index สร้างใหม่
- [[concepts/ai-tools/multi-agent-theory]] ← เสริม (planned P2a)
- [[entities/ai-tools/openrouter-api]] ← cross-ref เพิ่มเติม
