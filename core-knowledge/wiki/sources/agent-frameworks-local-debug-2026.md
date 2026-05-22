---
type: source
title: "Insights จากการ debug agent framework บน local LLM (thClaws/Hermes/OpenClaw)"
slug: agent-frameworks-local-debug-2026
date_ingested: 2026-05-02
original_file: (social media post — ผู้ใช้ paste มา 2026-05-02)
tags: [agent-framework, local-llm, ollama, system-prompt, context-injection, prompt-engineering]
---

# Agent Framework Insights — thClaws / Hermes / OpenClaw บน Local LLM

**ประเภท**: experience-based article (Thai dev community)
**วันที่**: ~2026-05 (ผู้ใช้ paste เข้ามา 2026-05-02)
**ผู้เขียน**: ไม่ทราบชื่อ — Thai AI dev (สาย local-first / privacy-first)

## ประเด็นหลัก

1. **แก่นของ agent design มี 2 อย่าง**: System Prompt Design + Context Injection Strategy — กำหนดว่า agent จะเบา/เร็ว vs ฉลาด/autonomous
2. **thClaws = lean & surgical** — system prompt สั้น, tool-only, inject context เฉพาะกิจ → token ต่ำ, รัน Q4/Q5 quantized + ctx เล็กได้
3. **Hermes = autonomous specialist** — system prompt ใหญ่ (persona + skills + memory preload + few-shot) → ฉลาด autonomous แต่กิน ctx ตั้งแต่ token แรก ถ้า ctx <16k อาจ "เปิดไม่ขึ้น"
4. **OpenClaw = orchestrator หนัก** — multi-layer prompts (planner → executor → tool wrapper), prompt overhead หลายหมื่นตัวอักษร, prefill นาน, memory accumulate → silent failure บ่อยใน local environment ที่ resource ไม่พอ
5. **Tool-calling compatibility ของ local model** ยังเป็นปัญหา — JSON schema fail → loop/retry/timeout

## ข้อมูลที่น่าสนใจ

- thClaws ใช้ Rust ในบาง runtime layer → memory/latency/concurrency ดีกว่า Python-only frameworks
- OpenClaw มี idle timeout ~60s ถ้า model ไม่ส่ง token แรกทัน → ดูเหมือน "ไม่ตอบ"
- ถ้า model ไม่ pin ใน Ollama memory → reload ทุก request = latency พุ่ง

## ข้อโต้แย้ง / มุมมองเพิ่มเติม (Claude)

- "lean = local-first เสมอ" oversimplify — ถ้ามี hardware แรงพอ (RTX 4090, M3 Ultra + 32k+ ctx) Hermes ก็รัน local ได้สบาย
- ผู้เขียนไม่พูดถึง **dynamic context management** (compaction, RAG, summarization) ซึ่งสำคัญพอกัน
- "Rust runtime → performance ดีกว่า" จริงสำหรับ orchestration overhead แต่ bottleneck ที่แท้จริงของ local agent คือ inference latency ไม่ใช่ runtime
- thClaws "คล้าย Claude Code" — เพราะ Anthropic เปิด Claude Agent SDK แล้ว pattern นี้ converge กันทั่ววงการ ไม่ใช่ exclusive

## คำคมที่นำมาอ้างอิงได้

> "Agent design สำคัญพอ ๆ กับ model — model ดีแต่ prompt architecture ไม่ดี ผลลัพธ์ก็แย่"

> "Agent ที่ซับซ้อนกว่า ไม่ได้แปลว่าดีกว่าเสมอไป มันจะดีก็ต่อเมื่อ environment ของคุณรองรับมันได้"

> "execution ใช้แบบ lean / reasoning ใช้แบบมี brain / orchestration ใช้เท่าที่จำเป็น"

## หน้า Wiki ที่ได้รับการอัปเดต

- [[concepts/ai-tools/agent-framework-tradeoffs]] — สร้างใหม่
- [[entities/ai-tools/hermes-agent]] — เพิ่ม caveat เรื่อง ctx requirement
