---
type: concept
tags: [a2a, agent-to-agent, agent-card, task-lifecycle, artifacts, grpc, opacity-principle, ap2-payments, linux-foundation]
sources: [ai-engineering-tools-protocols]
domain: ai-tools
created: 2026-06-08
updated: 2026-06-08
last_verified: 2026-06-08
verify_tool: WebFetch
---

# A2A Protocol

Agent-to-Agent Protocol — มาตรฐาน open สำหรับ agents ค้นหา สื่อสาร และ delegate งานให้กัน
[verified 2026-06-08] จาก `rohitg00/ai-engineering-from-scratch` Phase 13 (MIT)

---

## 1. Overview

A2A (Agent-to-Agent Protocol): open protocol สำหรับ agent-to-agent communication
- v1.0 released: **April 2026**
- Adoption: **150+ organizations** (Google, Microsoft, Salesforce, SAP, Workday, etc.)
- Governance: donated to Linux Foundation Agentic AI Foundation — Jun 2025

**Core idea**: ทำให้ agents เป็น building blocks ที่ interoperable — orchestrator เรียก sub-agent โดยไม่รู้ implementation ภายใน

---

## 2. Agent Card

Agent Card = "นามบัตร" ของ agent — published ที่ `/.well-known/agent.json`

```json
{
  "name": "DataAgent",
  "description": "Fetches and analyzes datasets",
  "version": "1.2.0",
  "capabilities": {
    "streaming": true,
    "pushNotifications": false
  },
  "skills": [
    {
      "id": "fetch-dataset",
      "name": "Fetch Dataset",
      "inputModes": ["text"],
      "outputModes": ["data", "file"]
    }
  ],
  "authentication": {"schemes": ["bearer"]},
  "defaultInputModes": ["text"],
  "defaultOutputModes": ["text", "data"]
}
```

**Orchestrator flow**: ค้นหา agent → fetch Agent Card → เลือก skill ที่เหมาะ → ส่ง task

---

## 3. Task Lifecycle

```
submitted ──→ working ──→ completed
                 │
                 ↓
           input-required ←──→ working (loop จนกว่า user ตอบ)
                 │
                 ├──→ failed
                 ├──→ canceled
                 └──→ rejected
```

| State | ความหมาย |
|---|---|
| **submitted** | Task received; ยังไม่เริ่ม |
| **working** | Agent กำลัง process |
| **input-required** | Agent หยุดรอ input จาก caller (human-in-the-loop) |
| **completed** | สำเร็จ; artifacts พร้อมใช้ |
| **failed** | Error ที่ recover ไม่ได้ |
| **canceled** | Caller ยกเลิก |
| **rejected** | Agent ปฏิเสธ (capability mismatch, policy) |

---

## 4. Messages และ Parts

Message ประกอบด้วย **Parts** หลายชิ้น:

| Part Type | ใช้สำหรับ |
|---|---|
| **TextPart** | Plain text หรือ markdown instructions |
| **FilePart** | Binary file พร้อม mimeType; inline bytes หรือ URI |
| **DataPart** | Structured JSON data |

Multi-part ช่วยให้ส่ง text instructions + structured data + file attachments ในข้อความเดียว

---

## 5. Artifacts

Artifacts = named outputs ที่ task ผลิตออกมา:
- Fields: `artifactId`, `name`, `mimeType`, `parts[]`
- **Immutable** เมื่อ produced (append-only)
- Downstream tasks อ้างอิงผ่าน `artifactId`

---

## 6. Transports

| Transport | Protocol | เหมาะกับ |
|---|---|---|
| **JSON-RPC over HTTP** | HTTP/1.1 + HTTP/2 | Standard web infra, load balancers, stateless |
| **gRPC** | HTTP/2 + protobuf | High-throughput, streaming, microsecond latency |

---

## 7. Opacity Preservation Principle

Agent internal state, reasoning, implementation = **opaque** to callers

- Caller เห็น: inputs → outputs (tasks + messages + artifacts)
- Caller ไม่เห็น: how agent processes, sub-agents ที่ใช้, internal memory

**"Orchestrators call agents as black boxes."** (A2A spec)

ประโยชน์: agents upgrade/swap internals โดยไม่กระทบ orchestrator; privacy/IP protection

---

## 8. AP2 Payments Extension (Sep 2025)

Signed Agent Cards พร้อม payment capability declarations:
- Agents ประกาศ price สำหรับ skills
- Micropayments via cryptographic attestation
- **Agent economy infrastructure** — agents เป็น revenue-generating services

---

## 9. Timeline

| วันที่ | เหตุการณ์ |
|---|---|
| เม.ย. 2025 | Google ประกาศ A2A ที่ Cloud Next |
| มิ.ย. 2025 | Donated to Linux Foundation Agentic AI Foundation |
| ส.ค. 2025 | A2A absorbs ACP (Agent Communication Protocol) |
| ก.ย. 2025 | AP2 payments extension published |
| เม.ย. 2026 | v1.0 finalized; 150+ orgs adopting |

---

## 10. MCP vs A2A — การแยกหน้าที่

| Protocol | Who talks | Direction | Scope |
|---|---|---|---|
| **MCP** | Agent ↔ Tool/Data | Agent calls tool | Tool use, data access |
| **A2A** | Agent ↔ Agent | Agent delegates to agent | Task delegation, orchestration |

**Analogy**: "MCP = agent's hands (จับ tools); A2A = agent's voice (คุยกับ agents อื่น)"

ใช้ทั้งคู่พร้อมกัน: orchestrator ใช้ A2A delegate task → sub-agent ใช้ MCP เรียก tools

---

## ความสัมพันธ์

- [[concepts/ai-tools/mcp-architecture]] — คู่กัน: MCP tool use + A2A agent delegation
- [[concepts/ai-tools/multi-agent-theory]] — A2A = modern implementation ของ agent communication protocols (FIPA-ACL legacy)
- [[concepts/ai-tools/agent-planning-loops]] — A2A enable orchestrator-worker pattern ข้าม agent boundaries
- [[concepts/ai-tools/swarm-optimization]] — A2A task lifecycle รองรับ HITL และ cascading failure recovery

## แหล่งข้อมูล
- [[sources/ai-engineering-tools-protocols]] — Phase 13 subtopic 19 A2A Protocol
