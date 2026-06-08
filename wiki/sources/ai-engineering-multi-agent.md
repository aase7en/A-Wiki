---
type: source
title: "Multi-Agent Theory — rohitg00/ai-engineering-from-scratch Phase 16 (subtopics 01-13)"
slug: ai-engineering-multi-agent
date_ingested: 2026-06-08
original_file: raw/ai-engineering-multi-agent.md
tags: [multi-agent, swarm, fipa, a2a, supervisor, orchestrator, role-specialization, handoffs, blackboard]
domain: ai-tools
---

# Multi-Agent Theory — Phase 16 (Subtopics 01-13)

**ประเภท**: curriculum / theory  
**วันที่**: 2026  
**ผู้เขียน**: Rohit Ghumare (MIT License)  
**Source repo**: `rohitg00/ai-engineering-from-scratch`

## ประเด็นหลัก

1. **4 Pattern พื้นฐาน**: Pipeline, Fan-out/Fan-in, Orchestrator-Worker, Peer Swarm — แต่ละแบบมี use case ต่างกันชัดเจน
2. **FIPA-ACL heritage**: 20 performatives ที่เป็นรากฐาน; MCP/A2A = modern FIPA-lite
3. **4 Protocol landscape (2025)**: MCP (tools), A2A (agent delegation), ACP (enterprise), ANP (decentralized)
4. **Supervisor pattern**: Lead+Workers, fresh context per subagent → Anthropic Research +90.2%
5. **Hierarchical**: depth-2 ceiling, 3 failure modes, canary question pattern
6. **Role specialization**: Planner/Executor/Critic/Verifier; Critic≠Verifier; 7× accuracy gain from verifier
7. **Swarm/parallel**: No orchestrator, shared queue, Matrix framework (pub/sub event mesh)
8. **Handoffs+Routines**: OpenAI Swarm → 2 primitives (routine + handoff tool); stateless trade-off
9. **Shared memory**: Message pool vs Blackboard; memory poisoning = hallucination propagation
10. **A2A Protocol**: Agent Cards at `/.well-known/agent.json`, Task lifecycle, 150+ orgs adoption

## ข้อมูลที่น่าสนใจ

- Anthropic Research: supervisor pattern gave +90.2% over single-agent (Sonnets under Opus lead)
- MAST study (Cemri 2025): 21.3% of 1642 multi-agent failures = verification gaps
- PwC CrewAI: adding validation loop → accuracy 10%→70% (7× gain)
- Token dominance: 80% of cost variance = token usage, not model choice
- Depth-2 ceiling: 3+ hierarchical levels collapse observability (empirical finding)
- FIPA-ACL (1990s) → MCP (2024) → A2A (2025): communication protocol evolution
- OpenAI Swarm source fits in "a few hundred lines" — entire abstraction = routine + handoff

## ข้อโต้แย้งหรือความขัดแย้ง

- A2A (Google) vs MCP (Anthropic): ไม่ใช่คู่แข่งกัน — MCP=vertical (agent→tool), A2A=horizontal (agent↔agent); production ใช้ทั้งคู่
- Hierarchical vs Sequential: paper recommend "sequential ก่อน ถ้าไม่มี independent sub-teams จริง อย่าใช้ hierarchical"
- Swarm vs Supervisor: Anthropic Research เลือก supervisor over swarm อย่างตั้งใจ (coherent plan > throughput)
- Critic vs Verifier: ต่างกันชัด — Critic=LLM (subjective), Verifier=deterministic code (objective)

## หน้า Wiki ที่ได้รับการอัปเดต / สร้างใหม่

- [[concepts/ai-tools/multi-agent-theory]] — สร้างใหม่ (chunk P2a)
- [[concepts/ai-tools/ai-glossary]] — cross-ref เพิ่ม
- [[agent-skills/swarm-intelligence/agile-swarm]] — เพิ่ม cross-ref ไปที่ theory pages
