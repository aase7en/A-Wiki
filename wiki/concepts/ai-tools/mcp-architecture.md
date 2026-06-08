---
type: concept
tags: [mcp, model-context-protocol, json-rpc, tools, resources, prompts, sampling, elicitation, roots, capability-negotiation]
sources: [ai-engineering-tools-protocols]
domain: ai-tools
created: 2026-06-08
updated: 2026-06-08
last_verified: 2026-06-08
verify_tool: WebFetch
---

# MCP Architecture

Model Context Protocol — มาตรฐานเปิดสำหรับเชื่อมต่อ AI agents กับ tools และ data
[verified 2026-06-08] จาก `rohitg00/ai-engineering-from-scratch` Phase 13 (MIT)

---

## 1. Overview

MCP (Model Context Protocol): open standard ที่ Anthropic สร้างและ donate ให้ Linux Foundation
- Spec version: **2025-11-25** (latest stable)
- Downloads: **110M monthly** SDK downloads
- Ecosystem: **10,000+** public MCP servers
- Governance: Linux Foundation Agentic AI Foundation (Jun 2025)

**Core idea**: Standardize how AI applications (hosts/clients) connect to external capabilities (servers) — เหมือน USB-C สำหรับ AI tools.

---

## 2. 6 Primitives

### Server-side (capabilities ที่ server expose ให้ client)

| Primitive | Controller | Description | ตัวอย่าง |
|---|---|---|---|
| **Tools** | Model-controlled | Functions ที่ model เรียกได้; model ตัดสินใจเรียก | `search_web(query)`, `run_code(code)` |
| **Resources** | App-controlled | Data ที่ server expose; application เลือกให้ | `file://README.md`, `db://users/123` |
| **Prompts** | User-controlled | Reusable prompt templates; user เลือกใช้ | `summarize_code(language)` |

### Client-side (capabilities ที่ client provide ให้ server)

| Primitive | Description | ตัวอย่าง |
|---|---|---|
| **Roots** | File system boundaries ที่ server อนุญาตให้เข้าถึง | `/project/src`, `/data/readonly` |
| **Sampling** | Server ขอให้ client สร้าง model inference | Recursive agentic loops |
| **Elicitation** | Server ขอ user input ผ่าน client | Security confirmations, ambiguity resolution |

**สำคัญ**: Elicitation = built-in human-in-the-loop — server สามารถหยุดและถาม user โดยไม่ต้องออกแบบ HITL เอง

---

## 3. 3-Phase Lifecycle

```
Initialize
  client → server: initialize {capabilities, protocolVersion, clientInfo}
  server → client: {capabilities, protocolVersion, serverInfo}
  client → server: initialized (notification — ack)

Operation
  ← normal work: tool calls, resource reads, prompt gets, sampling requests →

Shutdown
  client → server: shutdown request
  server: drain in-flight requests
  connection closes
```

---

## 4. Wire Format: JSON-RPC 2.0

ทุก message: `jsonrpc: "2.0"`, `id`, plus one of:
- **Request**: `method` + `params`
- **Response**: `result` หรือ `error`
- **Notification**: `method` + `params` (ไม่มี id, ไม่ต้องรอ response)

---

## 5. 15 Key Methods

| Method | Direction | หน้าที่ |
|---|---|---|
| `initialize` | C→S | Handshake + capability exchange |
| `tools/list` | C→S | Discover available tools |
| `tools/call` | C→S | Invoke a tool |
| `resources/list` | C→S | List available resources |
| `resources/read` | C→S | Read resource content |
| `resources/subscribe` | C→S | Watch resource for changes |
| `prompts/list` | C→S | List prompt templates |
| `prompts/get` | C→S | Retrieve a prompt template |
| `sampling/createMessage` | S→C | Request model inference |
| `elicitation/create` | S→C | Request user input |
| `roots/list` | S→C | Request accessible roots |
| `logging/setLevel` | C→S | Set log verbosity |
| `notifications/tools/list_changed` | S→C | Push: tools changed |
| `notifications/resources/updated` | S→C | Push: resource changed |
| `ping` | Either | Health check |

---

## 6. Capability Negotiation

During `initialize`:
1. Client sends `capabilities` object (what client supports)
2. Server responds with `capabilities` object (what server offers)
3. Both sides only use methods/notifications declared by the other

**Forward compatibility**: unknown capabilities silently ignored — เพิ่ม features ใหม่โดยไม่ break ของเดิม

---

## 7. Transports

| Transport | ใช้กับ | หมายเหตุ |
|---|---|---|
| **stdio** | Local tools, subprocess | Client write JSON-RPC → stdin; read ← stdout |
| **HTTP+SSE** | Remote server | HTTP POST for requests; SSE stream for notifications |
| **Streamable HTTP** | Remote server (spec 2025-11-25) | Single bidirectional endpoint; ทดแทน SSE transport |

---

## 8. MCP vs เดิม

| เดิม | MCP |
|---|---|
| Custom plugin ต่อ tool | Standard interface ทำครั้งเดียว, ใช้ได้ทุก host |
| Hard-coded capabilities | Capability negotiation; server-driven discovery |
| No HITL standard | Elicitation primitive built-in |
| No resource subscription | `resources/subscribe` = reactive updates |

---

## ความสัมพันธ์

- [[concepts/ai-tools/a2a-protocol]] — A2A คู่กัน: MCP = agent↔tool; A2A = agent↔agent
- [[concepts/ai-tools/agent-planning-loops]] — MCP tools = tool registry ใน ReAct loop
- [[concepts/ai-tools/multi-agent-theory]] — MCP = modern FIPA-lite สำหรับ tool access
- [[concepts/ai-tools/agent-memory-systems]] — MCP Resources = access pattern สำหรับ external memory

## แหล่งข้อมูล
- [[sources/ai-engineering-tools-protocols]] — Phase 13 subtopic 06 MCP Fundamentals
