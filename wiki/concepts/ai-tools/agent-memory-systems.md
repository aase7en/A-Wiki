---
type: concept
tags: [memory, memgpt, virtual-context, agent-memory, rag, episodic-memory, semantic-memory, mem0, letta]
sources: [ai-engineering-agent-patterns]
domain: ai-tools
created: 2026-06-08
updated: 2026-06-08
last_verified: 2026-06-08
verify_tool: WebFetch
---

# Agent Memory Systems

MemGPT virtual context, memory tiers, Letta, Mem0 — ระบบ memory สำหรับ AI agents
[verified 2026-06-08] จาก `rohitg00/ai-engineering-from-scratch` Phase 14 (MIT)

---

## 1. ปัญหาของ Context Window

| ปัญหา | คำอธิบาย | ผลกระทบ |
|---|---|---|
| **Overflow** | Multi-turn conversation ยาวกว่า window | Content สิ้นสุดของ window หายไป |
| **Dilution** | ยัด context ที่ไม่เกี่ยวข้อง → attention diluted | Quality ลดลงแม้ context ไม่เกิน limit |
| **Persistence** | Session ใหม่ = empty window | ไม่จำข้าม session |

Mem0 (2025): 128k-window baseline ยังพลาด long-horizon facts ที่ 4k-window + external memory จำได้.

---

## 2. MemGPT: Virtual Memory OS Analogy

(Packer et al., arXiv:2310.08560, Feb 2024)

| OS concept | MemGPT concept | Production analog |
|---|---|---|
| **RAM** | Main context (prompt) | Context window |
| **Disk** | External context | Vector DB, KV, Graph store |
| **Page fault** | Memory tool call | `memory.search`, `memory.write` |
| **OS kernel** | Agent control loop | ReAct loop with memory tools |

### 2 Tiers
- **Main context**: fixed-size prompt, always visible, always in-scope
- **External context**: unbounded, searchable via tools, retrieved on demand

### Interrupt Pattern
Agent issues memory tool → runtime executes → result splices into next turn as observation.
= Unix `read()` syscall: block → execute → return bytes → continue.

---

## 3. Memory Tool Surface

| Tool | Action |
|---|---|
| `core_memory_append(section, text)` | Write to persistent prompt section |
| `core_memory_replace(section, old, new)` | Edit persistent section |
| `archival_memory_insert(text)` | Write to external searchable store |
| `archival_memory_search(query, top_k)` | Retrieve from external store |
| `conversation_search(query)` | Scan past turns |

---

## 4. Memory Taxonomy (2026)

| Type | Storage | Access pattern | Example |
|---|---|---|---|
| **In-context (working)** | Prompt/context window | Always visible | Current conversation |
| **Episodic (conversation)** | KV/DB by session | Retrieve by session ID | Past chat turns |
| **Semantic (factual)** | Vector DB | Retrieve by similarity | User preferences, facts |
| **Procedural (skills)** | System prompt / tool definitions | Always loaded | Available tools, role |

---

## 5. Evolution: MemGPT → Letta → Mem0

### MemGPT (2023)
2-tier, explicit thought tokens, interrupt-based memory tools.
Research origin: OS virtual memory analogy.

### Letta (Sep 2024)
MemGPT production successor. 3 tiers:
- **Core memory**: pinned prompt sections (persona, human, task)
- **Recall memory**: episodic conversation history
- **Archival memory**: unbounded semantic store

Plus: native reasoning (no explicit thought tokens), sleep-time async compute (consolidation, summarization runs offline).

### Mem0 (arXiv:2504.19413)
Vector + KV + graph fused with a scoring layer.
- Conflict detector: resolves contradictions between new and stored facts
- Automatic extraction: identifies what to remember from conversation
- Hybrid retrieval: semantic similarity + recency + user-defined importance

---

## 6. Memory Failure Modes

| Failure | Cause | Fix |
|---|---|---|
| **Memory rot** | Writes > reads; stale facts drown retrieval | Periodic consolidation (Letta sleep-time); explicit invalidation |
| **Memory poisoning** | Attacker content in archival → re-ingested | Scan retrievals for directive text → mark untrusted |
| **Citation loss** | Agent recalls fact, can't cite source | Store `(session_id, turn_id, source_url)` with every archival write |

Memory poisoning = Greshake et al. prompt-injection attack restated over time. Related: [[concepts/ai-tools/multi-agent-theory#9-shared-memory--blackboard]].

---

## 7. Production Memory Systems

| System | Type | Best for |
|---|---|---|
| **Letta** | 3-tier, self-hosted | Long-running agents, sleep-time compute |
| **Mem0** | Hybrid (vector+KV+graph) | User personalization, cross-session continuity |
| **OpenAI Assistants** | Managed threads + files | Simple persistence without infrastructure |
| **Claude Agent SDK** | Session store + skills | Claude ecosystem integration |

**Selection rule**: operational shape (self-hosted vs managed, framework integration) — core pattern is MemGPT.

---

## ความสัมพันธ์

- [[concepts/ai-tools/agent-planning-loops]] — planning ต้องการ memory เพื่อ track state ข้าม steps
- [[concepts/ai-tools/multi-agent-theory]] — shared memory / blackboard ใน multi-agent systems
- [[concepts/ai-tools/llm-rag-architecture]] — RAG = external memory retrieval pattern สำหรับ LLM
- [[concepts/ai-tools/ai-myths]] — myth: "bigger context window = better" — external memory คือคำตอบที่แท้จริง

## แหล่งข้อมูล
- [[sources/ai-engineering-agent-patterns]] — Phase 14 subtopics 07
