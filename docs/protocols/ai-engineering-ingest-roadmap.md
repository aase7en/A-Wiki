---
type: protocol
title: "AI Engineering Integration Roadmap"
source_repo: "https://github.com/rohitg00/ai-engineering-from-scratch"
source_license: MIT
started: 2026-06-08
last_updated_by: claude-sonnet-4-6
---

# AI Engineering Integration Roadmap

> **Source**: [`rohitg00/ai-engineering-from-scratch`](https://github.com/rohitg00/ai-engineering-from-scratch) (MIT, 2026)
> **Purpose**: เสริม A-Wiki ด้าน AI theory — multi-agent/swarm coordination, LLM engineering, agent patterns, tools/protocols
> **คำอธิบาย**: A-Wiki มี operational skills (agile-swarm, model-scouter) แต่ขาด theoretical foundation ไฟล์นี้ track การ ingest 5 priority phases เข้า wiki

---

## 🎯 Resume Here (สำหรับ agent ที่รับช่วงต่อ)

> **Status**: ✅ **ALL CHUNKS DONE** (P1a, P1b, P2a, P2b, P3, P4, P5 completed 2026-06-08)
> P6 (Ethics & Safety) deferred intentionally — ดู Skipped Phases section
> ไม่มีงานค้าง

---

## 📋 Task Board

| Chunk | Status | Priority | Goal | Files Created | Verify |
|-------|--------|----------|------|---------------|--------|
| `ai-eng-P1a` | [x] | 🔴 P1 | Ingest glossary/terms.md | `wiki/sources/ai-engineering-glossary.md`, `wiki/concepts/ai-tools/ai-glossary.md` | `search-wiki.py "embedding"` |
| `ai-eng-P1b` | [x] | 🔴 P1 | Ingest glossary/myths.md | `wiki/sources/ai-engineering-myths.md`, `wiki/concepts/ai-tools/ai-myths.md` | `search-wiki.py "hallucination myth"` |
| `ai-eng-P2a` | [x] | 🔴 P1 | Multi-agent theory (subtopics 01-13) | `raw/ai-engineering-multi-agent.md`, `wiki/sources/...`, `wiki/concepts/ai-tools/multi-agent-theory.md` | `search-wiki.py "FIPA"` |
| `ai-eng-P2b` | [x] | 🔴 P1 | Swarm optimization + case studies (subtopics 14-25) | `wiki/concepts/ai-tools/swarm-optimization.md` | `search-wiki.py "PSO"` |
| `ai-eng-P3` | [x] | 🟡 P2 | Agent engineering patterns (phase 14) | `raw/ai-engineering-agent-patterns.md`, `wiki/sources/...`, `wiki/concepts/ai-tools/agent-planning-loops.md`, `wiki/concepts/ai-tools/agent-memory-systems.md` | `search-wiki.py "planning loop"` |
| `ai-eng-P4` | [x] | 🟡 P2 | LLM engineering (phase 11) | `raw/ai-engineering-llm.md`, `wiki/sources/...`, `wiki/concepts/ai-tools/llm-rag-architecture.md`, `wiki/concepts/ai-tools/llm-eval-frameworks.md` | `search-wiki.py "RAG architecture"` |
| `ai-eng-P5` | [x] | 🟡 P2 | Tools & protocols (phase 13) | `raw/ai-engineering-tools-protocols.md`, `wiki/sources/...`, `wiki/concepts/ai-tools/mcp-architecture.md`, `wiki/concepts/ai-tools/a2a-protocol.md` | `search-wiki.py "A2A protocol"` |
| `ai-eng-P6` | [ ] | ⚪ P3 | Ethics & safety (phase 18) | tbd | — |

---

## 🤖 For Any Agent Picking This Up

```
1. git pull origin main
2. Read this file — find first [ ] chunk in Task Board above
3. Follow "Per-Chunk Instructions" for that chunk
4. Source files: use mcp__github__get_file_contents with owner=rohitg00, repo=ai-engineering-from-scratch
5. Save raw content to raw/<slug>.md FIRST (hook enforced — see ingest workflow below)
6. Follow 6-step ingest workflow (wiki/context/wiki-guide.md)
7. After chunk done:
   - Change [ ] → [x] in Task Board
   - Update "Resume Here" next chunk
   - git commit -m "chunk(ai-eng-Px): <result> [next: ai-eng-Py]"
   - git push origin main (so next agent gets updated state)
```

### compat note — agents without mcp__github__:
```bash
# Clone sparse, extract target phase
git clone --no-checkout --depth 1 https://github.com/rohitg00/ai-engineering-from-scratch.git /tmp/ai-eng
cd /tmp/ai-eng && git sparse-checkout init --cone
git sparse-checkout set glossary phases/16-multi-agent-and-swarms phases/14-agent-engineering
git checkout main
```

---

## 📑 Per-Chunk Instructions

### ✅ [ai-eng-P1a] Glossary Terms — DONE
- **Source**: `glossary/terms.md` (27KB, ~50 key AI terms)
- **Raw**: `raw/ai-engineering-glossary.md` ✅
- **Source summary**: `wiki/sources/ai-engineering-glossary.md` ✅
- **Concept page**: `wiki/concepts/ai-tools/ai-glossary.md` ✅
- **Commit**: `chunk(ai-eng-P1a): ingest AI engineering glossary [next: ai-eng-P1b]`

---

### ✅ [ai-eng-P1b] Glossary Myths — DONE
- **Source**: `glossary/myths.md` (10KB, ~20 AI misconceptions)
- **Raw**: `raw/ai-engineering-myths.md` ✅
- **Source summary**: `wiki/sources/ai-engineering-myths.md` ✅
- **Concept page**: `wiki/concepts/ai-tools/ai-myths.md` ✅
- **Commit**: `chunk(ai-eng-P1b): ingest AI engineering myths [next: ai-eng-P2a]`

---

### ✅ [ai-eng-P2a] Multi-Agent Theory (subtopics 01-13) — DONE
- **Source paths** (fetch each README.md):
  - `phases/16-multi-agent-and-swarms/01-why-multi-agent/`
  - `phases/16-multi-agent-and-swarms/02-fipa-acl-heritage/`
  - `phases/16-multi-agent-and-swarms/03-communication-protocols/`
  - `phases/16-multi-agent-and-swarms/05-supervisor-orchestrator-pattern/`
  - `phases/16-multi-agent-and-swarms/06-hierarchical-architecture/`
  - `phases/16-multi-agent-and-swarms/08-role-specialization/`
  - `phases/16-multi-agent-and-swarms/09-parallel-swarm-networks/`
  - `phases/16-multi-agent-and-swarms/11-handoffs-and-routines/`
  - `phases/16-multi-agent-and-swarms/12-a2a-protocol/`
  - `phases/16-multi-agent-and-swarms/13-shared-memory-blackboard/`
- **Consolidate** all content → save to `raw/ai-engineering-multi-agent.md`
- **Create**:
  - `wiki/sources/ai-engineering-multi-agent.md`
  - `wiki/concepts/ai-tools/multi-agent-theory.md` — covers FIPA-ACL, supervisor pattern, A2A, BFT, shared memory, role specialization
- **Update**:
  - `agent-skills/swarm-intelligence/agile-swarm.md` → add `[[concepts/ai-tools/multi-agent-theory]]` cross-ref section
- **Verify**: `python3 scripts/search-wiki.py "FIPA"`
- **Commit**: `chunk(ai-eng-P2a): multi-agent theory concepts [next: ai-eng-P2b]`

---

### ✅ [ai-eng-P2b] Swarm Optimization + Case Studies (subtopics 14-25) — DONE
- **Source paths**:
  - `phases/16-multi-agent-and-swarms/14-consensus-and-bft/`
  - `phases/16-multi-agent-and-swarms/15-voting-debate-topology/`
  - `phases/16-multi-agent-and-swarms/19-swarm-optimization-pso-aco/`
  - `phases/16-multi-agent-and-swarms/20-marl-maddpg-qmix-mappo/`
  - `phases/16-multi-agent-and-swarms/23-failure-modes-mast-groupthink/`
  - `phases/16-multi-agent-and-swarms/25-case-studies-2026-sota/`
- **Append** to `raw/ai-engineering-multi-agent.md` (or new file `raw/ai-engineering-swarm-optimization.md`)
- **Create**:
  - `wiki/concepts/ai-tools/swarm-optimization.md` — PSO, ACO, MARL (MADDPG/QMIX/MAPPO), BFT, voting topology, failure modes
- **Verify**: `python3 scripts/search-wiki.py "PSO ACO"`
- **Commit**: `chunk(ai-eng-P2b): swarm optimization concepts [next: ai-eng-P3]`

---

### ✅ [ai-eng-P3] Agent Engineering Patterns (phase 14) — DONE
- **Source path**: `phases/14-agent-engineering/` (fetch directory listing first, then key README.md files)
- **Create**:
  - `raw/ai-engineering-agent-patterns.md`
  - `wiki/sources/ai-engineering-agent-patterns.md`
  - `wiki/concepts/ai-tools/agent-planning-loops.md`
  - `wiki/concepts/ai-tools/agent-memory-systems.md`
- **Verify**: `python3 scripts/search-wiki.py "planning loop"`
- **Commit**: `chunk(ai-eng-P3): agent engineering patterns [next: ai-eng-P4]`

---

### ✅ [ai-eng-P4] LLM Engineering (phase 11) — DONE
- **Source path**: `phases/11-llm-engineering/` (fetch directory listing first, then key README.md files)
- **Create**:
  - `raw/ai-engineering-llm.md`
  - `wiki/sources/ai-engineering-llm.md`
  - `wiki/concepts/ai-tools/llm-rag-architecture.md`
  - `wiki/concepts/ai-tools/llm-eval-frameworks.md`
- **Verify**: `python3 scripts/search-wiki.py "RAG architecture"`
- **Commit**: `chunk(ai-eng-P4): LLM engineering concepts [next: ai-eng-P5]`

---

### ✅ [ai-eng-P5] Tools & Protocols (phase 13) — DONE
- **Source path**: `phases/13-tools-and-protocols/` (fetch directory listing first, then key README.md files)
- **Create**:
  - `raw/ai-engineering-tools-protocols.md`
  - `wiki/sources/ai-engineering-tools-protocols.md`
  - `wiki/concepts/ai-tools/mcp-architecture.md`
  - `wiki/concepts/ai-tools/a2a-protocol.md`
- **Verify**: `python3 scripts/search-wiki.py "A2A"`
- **Commit**: `chunk(ai-eng-P5): tools & protocols concepts [next: ai-eng-P6 or done]`

---

### [ ] [ai-eng-P6] Ethics & Safety (phase 18) — Optional
- **Source path**: `phases/18-ethics-safety-alignment/`
- **Defer** unless specifically requested.

---

## ✅ Post-All-Chunks Checklist

```bash
python3 scripts/gen-index.py         # regenerate wiki-overview.md
python3 scripts/build-wiki-index.py  # rebuild FTS5 search index
python3 scripts/search-wiki.py "multi-agent"   # verify
python3 scripts/search-wiki.py "swarm"         # verify
python3 scripts/search-wiki.py "RAG"           # verify
# /snapshot-nb ai-tools               ← offer to user for NotebookLM refresh
```

---

## 🚫 Skipped Phases (intentional)

| Phase | Reason skipped |
|-------|----------------|
| `00-setup-and-tooling` | Redundant with A-Wiki setup |
| `01-math-foundations` | A-Wiki ไม่ใช่ textbook |
| `02-ml-fundamentals` | A-Wiki ไม่ใช่ textbook |
| `03-deep-learning-core` | A-Wiki ไม่ใช่ textbook |
| `04-computer-vision` | นอก domain |
| `06-speech-and-audio` | นอก domain |
| `07-transformers-deep-dive` | Math-heavy; ไม่ตรง operational focus |
| `09-reinforcement-learning` | Marginal; covered partially ใน P2b |
| `10-llms-from-scratch` | Implementation details; ไม่ใช่ operational knowledge |
| `12-multimodal-ai` | นอก current domain |
| `15-autonomous-systems` | Partially covered in P3 |
| `17-infrastructure-and-production` | Partially covered ใน existing wiki |

*Last updated: 2026-06-08 by claude-sonnet-4-6 — ALL CHUNKS COMPLETE (P1a, P1b, P2a, P2b, P3, P4, P5)*
