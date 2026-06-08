---
type: source
title: "Agent Engineering Patterns — rohitg00/ai-engineering-from-scratch Phase 14 (subtopics 01, 02, 07, 12)"
slug: ai-engineering-agent-patterns
date_ingested: 2026-06-08
original_file: raw/ai-engineering-agent-patterns.md
tags: [agent-loop, react, rewoo, plan-and-execute, memory, memgpt, workflow-patterns, anthropic]
domain: ai-tools
---

# Agent Engineering Patterns — Phase 14

**ประเภท**: curriculum / theory  
**วันที่**: 2026  
**ผู้เขียน**: Rohit Ghumare (MIT License)

## ประเด็นหลัก

1. **Agent Loop (ReAct)**: Observe→Think→Act loop; 5 ingredients บังคับ; ทุก framework ใช้ ReAct ภายใน
2. **ReWOO**: แยก Plan ออกจาก Execute; 5x fewer tokens, +4% accuracy; planner distillation ได้
3. **MemGPT Virtual Memory**: 2-tier (main context = RAM, external = disk); memory tools = page fault pattern
4. **Anthropic 5 Patterns**: Prompt chaining, Routing, Parallelization, Orchestrator-workers, Evaluator-optimizer
5. **Workflow vs Agent**: Engineer-owned graph vs Model-owned graph; ใช้ workflow ก่อนเสมอ

## ข้อมูลที่น่าสนใจ

- ReAct: +34 pts on ALFWorld, +10 pts WebShop (with 1-2 examples only)
- ReWOO: ~5x fewer tokens, +4% HotpotQA vs ReAct
- Agents run 40-400 steps per task in 2026 (Anthropic computer-use announcement)
- Mem0 2025: 128k-window baseline still misses long-horizon facts that 4k-window+external memory catches
- Planner distillation: 7B model can match 175B planner by fine-tuning on planner traces

## หน้า Wiki ที่ได้รับการอัปเดต / สร้างใหม่

- [[concepts/ai-tools/agent-planning-loops]] — สร้างใหม่ (chunk P3)
- [[concepts/ai-tools/agent-memory-systems]] — สร้างใหม่ (chunk P3)
