---
type: concept
tags: [multi-agent, swarm, fipa, a2a, mcp, supervisor, hierarchical, role-specialization, handoffs, blackboard, orchestrator]
sources: [ai-engineering-multi-agent]
domain: ai-tools
created: 2026-06-08
updated: 2026-06-08
last_verified: 2026-06-08
verify_tool: WebFetch
---

# Multi-Agent Theory

ทฤษฎีพื้นฐานการออกแบบระบบ multi-agent: patterns, protocols, architectures, failure modes
[verified 2026-06-08] จาก `rohitg00/ai-engineering-from-scratch` Phase 16 (MIT)

---

## 1. 4 Pattern พื้นฐาน

| Pattern | รูปแบบ | ใช้เมื่อ |
|---------|--------|----------|
| **Pipeline** | A→B→C sequential | Sequential dependency, strict ordering |
| **Fan-out/Fan-in** | Orchestrator→[W1,W2,W3]→Aggregator | Independent parallel sub-tasks |
| **Orchestrator-Worker** | Dynamic dispatch based on state | Dynamic interdependent tasks |
| **Peer Swarm** | Shared queue, no central coordinator | Many independent tasks, throughput > determinism |

### เมื่อไม่ควรใช้ Multi-Agent
- งานง่าย (เพิ่ม complexity ไม่คุ้ม)
- Latency สำคัญมาก (coordination overhead)
- Debug-critical (trace ยากขึ้น)
- Context เล็ก (single call เร็วกว่าและถูกกว่า)

---

## 2. FIPA-ACL Heritage (รากฐาน Protocol)

FIPA-ACL (1990s) คือรากฐานของ protocol สื่อสาร agent ทุกตัว — มาจาก Speech-Act Theory (Austin/Searle)

### 20 Performatives ที่สำคัญ
`inform`, `request`, `query-if`, `query-ref`, `cfp`, `propose`, `accept-proposal`, `reject-proposal`, `agree`, `refuse`, `failure`, `confirm`, `disconfirm`, `subscribe`, `cancel`, `not-understood`

### Contract Net Protocol (FIPA-CNET)
Manager → CFP → Proposals → Accept best → Execute → Report
ยังใช้ในระบบ distributed agent สมัยใหม่

### Modern FIPA-lite
- **MCP** = FIPA Request (tool invocation) + FIPA Inform (result return)
- **A2A** = FIPA CFP/Propose/Accept cycle ใน HTTP+JSON

---

## 3. Protocol Landscape 2025

| Protocol | Owner | ปัญหาที่แก้ | Transport | Key Abstraction |
|----------|-------|------------|-----------|-----------------|
| **MCP** | Anthropic | Tool discovery + invocation | HTTP+SSE, stdio | Tool, Resource, Prompt |
| **A2A** | Google | Agent-to-agent task delegation | HTTP/2 + SSE | Agent Card, Task, Artifact |
| **ACP** | IBM | Enterprise audit + governance | HTTP REST | Message, Thread, Run |
| **ANP** | Alibaba | Decentralized trust / identity | DID + WebSub | DID Document, Agent URL |

### MCP vs A2A (ไม่ใช่คู่แข่งกัน — ใช้ร่วมกัน)
| Dimension | MCP | A2A |
|-----------|-----|-----|
| Direction | Vertical (agent→tool) | Horizontal (agent↔agent) |
| Relationship | Master/slave | Peer delegation |
| Abstraction | Tool/Resource/Prompt | Task/Artifact/AgentCard |
| Discovery | Tool listing | `/.well-known/agent.json` |

### A2A Specifics (April 2025)
- Agent Card อยู่ที่ `/.well-known/agent.json`
- Task lifecycle: `submitted → working → completed/failed/canceled/input-required`
- Artifacts: typed results (text, file, data, form)
- Streaming via SSE สำหรับ long-running tasks
- 150+ orgs ใน working group

---

## 4. Supervisor / Orchestrator Pattern

### Core Design
Lead (Opus/strongest model) + Workers (Sonnet/fast) ใน hub-and-spoke.
**Key**: Lead ให้ **fresh context** ต่อ subagent — ไม่มี context bleeding ระหว่าง workers.

### Anthropic Research Results
- +90.2% over single-agent baseline
- Workers: narrow task, fresh context, no cross-contamination
- Workers ไม่แชร์ context ระหว่างกัน

### Token Dominance
80% ของ cost variance = token usage ไม่ใช่ model choice.
Fresh-context subagents ป้องกัน context blowup.

### Failure Modes
1. Supervisor bottleneck — ทุก decision ผ่าน lead → latency สูง
2. Context explosion — supervisor สะสม worker outputs → token cost พุ่ง
3. Silent worker failure — worker คืนขยะ, supervisor ไม่ verify
4. Over-delegation — supervisor delegate สิ่งที่ควรตัดสินใจเอง

---

## 5. Hierarchical Architecture

### Shape: Manager → Sub-Mgr → Workers

### When It Shines
- Clear org-chart decomposition (legal/finance/engineering อิสระ)
- Local summarization ก่อนส่งขึ้น top

### 3 Failure Modes (2026 post-mortems)
1. **Task assignment error**: manager hallucinate decomposition → wrong sub-manager → error surfaced late
2. **Output misinterpretation**: meaning drifts at each level ("unable to verify" → "not confirmed")
3. **Consensus loops**: sub-managers disagree → top re-delegates → workers re-run → loop until budget exhausted

### Guardrails บังคับ
- **Depth-2 ceiling**: 3+ levels ทำลาย observability
- **Reconciliation budget**: max 2 rounds
- **Canary question**: worker ถามคำถาม original เสมอ — detect decomposition drift
- **Provenance chain**: synthesis cite source leaf outputs

---

## 6. Role Specialization

### 4 Canonical Roles
| Role | Output | Tools | Type |
|------|--------|-------|------|
| Planner | Spec / step list | Knowledge retrieval | LLM |
| Executor | Artifact | Work tools (compiler, shell, API) | LLM |
| Critic | Accept/reject + reasons | Read-only artifact, static analysis | LLM (subjective) |
| Verifier | Pass/fail + evidence | Test runner, type checker, schema validator | **Deterministic** |

**Critic ≠ Verifier**: Critic=LLM (can be fooled by plausible prose); Verifier=code (objective, gives evidence).

### MetaGPT SOP Pattern (arXiv:2308.00352)
`Code = SOP(Team)` — strict I/O schemas encode roles as system prompts.
Product Manager → Architect → Project Manager → Engineer → QA Engineer.

### ChatDev Communicative Dehallucination (arXiv:2307.07924)
Executor asks Planner when a detail is missing — never invent it.
ป้องกัน plausible-invention failure mode.

### Impact Data
- MAST (Cemri 2025, arXiv:2503.13657): 21.3% of 1642 failures = verification gaps
- PwC CrewAI: +validation loop → accuracy 10% → 70% **(7× gain)**

### Anti-Pattern
ทุก role เป็น LLM, ทุก output = "looks good to me" → MAST failure mode.
ต้องมี **อย่างน้อยหนึ่ง deterministic verifier**.

---

## 7. Swarm / Parallel Architecture

### Shape
Shared queue → Workers pull → Results pool (no orchestrator).

### When Swarm Fits
- Tasks อิสระจำนวนมาก (scraping, classifying, transforming)
- Variable-duration work (swarm auto-balances load)
- Throughput > determinism

### When Swarm Fails
- Ordered workflows (step 3 needs step 2's output)
- Global-plan tasks (ต้องการ coherent report)
- Debug-heavy (no central log)

### Matrix Framework (arXiv:2511.21686)
ทั้ง control flow + data flow = serialized messages บน distributed queues.
Programming model: "subscribe to which topic?" แทน "supervisor picks who?"

### Failure Modes
- **Starvation**: long tasks never picked → priority queues with aging
- **Hot-spotting**: load imbalance → detection alert
- **Back-pressure**: queue grows faster than drain

### Production Requirements
- Durable queue (Kafka/Redis Streams, ไม่ใช่ in-memory)
- Idempotent workers (task processed twice = same result)
- Per-task trace ID

---

## 8. Handoffs and Routines (OpenAI Swarm)

### 2 Primitives
- **Routine**: system prompt + tool list = defines role + available handoffs
- **Handoff**: tool that returns a new Agent object → runtime switches active agent

### Why Viral
ใช้ tool-calling ที่ model ทำอยู่แล้ว; API เล็ก (2 concepts); ไม่ต้องเรียน DSL.

### Stateless Trade-off
Swarm = stateless between runs. Memory = caller's responsibility.

### When Handoffs Fit
- Triage (front-line → specialist)
- Skill-based routing (code → coder, research → researcher)
- Short bounded conversations (customer support, FAQ-to-ticket)

### OpenAI Agents SDK (March 2025)
Production successor เพิ่ม: session state, guardrails, tracing, handoff filters.
Handoff primitive คงอยู่.

### Swarm vs GroupChat
- Swarm: current agent picks successor (via handoff tool call)
- GroupChat: external manager/selector picks next speaker

### Failure Modes
- Handoff loops (A→B→A→B) — detect with last-K ring check
- Context blowup on handoff — use summarize-on-handoff
- Prompt injection → forced handoff — authenticate handoff tools

---

## 9. Shared Memory / Blackboard

### 2 Patterns
| Pattern | Visibility | Use when |
|---------|-----------|----------|
| Message Pool | All agents see all messages | Small teams, full transparency needed |
| Blackboard | Topic-keyed pub/sub | Large teams, need noise reduction |

### Memory Poisoning
= Hallucination propagation through shared state.
Agent A writes hallucinated fact → Agents B, C, D build on it → error amplifies.

### Defenses
- **Provenance tracking**: every write tagged with source + confidence
- **Append-only**: facts never overwritten, only superseded with explicit confidence
- **Unwritable verifier**: agent that reads but never writes, catches contradictions
- **Confidence thresholds**: claims below threshold = flagged, not used

---

## ความสัมพันธ์

- [[concepts/ai-tools/ai-glossary]] — คำศัพท์พื้นฐาน: agent, tool, context window, token
- [[concepts/ai-tools/ai-myths]] — myth: "AI agents are autonomous" (section 5)
- [[concepts/ai-tools/swarm-optimization]] — P2b: PSO, ACO, MARL, BFT (ดู [[sources/ai-engineering-multi-agent]])
- [[concepts/ai-tools/a2a-protocol]] — P5: A2A deep dive
- [[agent-skills/swarm-intelligence/agile-swarm]] — A-Wiki swarm design ใช้ Supervisor pattern + Role specialization

## แหล่งข้อมูล
- [[sources/ai-engineering-multi-agent]] — Phase 16 subtopics 01-13
- [[sources/ai-engineering-glossary]] — companion glossary
