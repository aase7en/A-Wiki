---
type: source
title: "Tools & Protocols — rohitg00/ai-engineering-from-scratch Phase 13 (subtopics 06 MCP, 19 A2A)"
slug: ai-engineering-tools-protocols
date_ingested: 2026-06-08
original_file: raw/ai-engineering-tools-protocols.md
tags: [mcp, model-context-protocol, a2a, agent-to-agent, json-rpc, tools-and-protocols, agent-card, task-lifecycle]
domain: ai-tools
---

# Tools & Protocols — Phase 13

**ประเภท**: curriculum / theory  
**วันที่**: 2026  
**ผู้เขียน**: Rohit Ghumare (MIT License)

## ประเด็นหลัก

1. **MCP 6 Primitives**: Server-side (Tools, Resources, Prompts) + Client-side (Roots, Sampling, Elicitation)
2. **MCP 3-Phase Lifecycle**: Initialize (capability negotiation) → Operation → Shutdown
3. **MCP Wire Format**: JSON-RPC 2.0; 15 key methods; capability negotiation ทำให้ forward compatible
4. **MCP Scale**: 110M monthly SDK downloads; 10,000+ public servers; Linux Foundation stewardship
5. **A2A Agent Card**: Published at `/.well-known/agent.json`; declares skills, capabilities, auth
6. **A2A Task Lifecycle**: submitted → working → input-required ↔ working → completed/failed/canceled/rejected
7. **A2A Messages/Parts**: TextPart + FilePart + DataPart; multi-part mixed content
8. **A2A Opacity Principle**: Orchestrators call agents as black boxes (internal state opaque)

## ข้อมูลที่น่าสนใจ

- MCP spec 2025-11-25: เพิ่ม Streamable HTTP transport ทดแทน HTTP+SSE เดิม
- Elicitation primitive: server สามารถขอ user input ผ่าน client — ทำให้ agent loop มี human-in-the-loop built-in
- A2A v1.0 (Apr 2026): 150+ orgs รวม Google, Microsoft, Salesforce, SAP, Workday — table stakes แล้ว
- AP2 extension (Sep 2025): signed Agent Cards + micropayments = agent economy infrastructure
- "MCP = agent's hands; A2A = agent's voice" — แยกชัด: MCP สำหรับ tool use, A2A สำหรับ agent delegation

## หน้า Wiki ที่ได้รับการอัปเดต / สร้างใหม่

- [[concepts/ai-tools/mcp-architecture]] — สร้างใหม่ (chunk P5)
- [[concepts/ai-tools/a2a-protocol]] — สร้างใหม่ (chunk P5)
