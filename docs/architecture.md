# InW-Wiki — Architecture Overview

> **วัตถุประสงค์**: แผนผังระบบแบบกระชับ — ใช้เป็น entry point แทนการอ่าน CLAUDE.md + wiki-overview.md + knowledge-graph.md พร้อมกัน
> **Last updated**: 2026-05-20

---

## Data Flow

```
raw/ (source documents, immutable)
  │ ingest
  ▼
wiki/
  ├── sources/       ← สรุป source
  ├── entities/      ← {iot,env,pharmacy,ai-tools}
  ├── concepts/      ← {iot,env,pharmacy,ai-tools}
  ├── synthesis/     ← cross-domain analysis
  └── context/
       ├── wiki-overview.md    ← auto-generated (python3 scripts/gen-index.py)
       ├── wiki-state.md       ← hardware inventory + domain status + stubs (Tier 1)
       ├── knowledge-graph.md  ← relationships (manual update)
       └── session-memory.md   ← rolling 10-session memory
```

---

## Domain Isolation (ข้อมูล 2026-05-20)

```
wiki/
  entities/                     concepts/
    iot/          ← 35 files     iot/          ← 12 files
    env/          ← 3 files      env/          ← 5 files
    pharmacy/     ← 5 files      pharmacy/     ← 8 files
    ai-tools/     ← 5 files      ai-tools/     ← 11 files

  synthesis/      ← 25 files
  sources/        ← 70 files
```

- แต่ละ domain มี `index-{domain}.md` + nested `wiki/CLAUDE.md` (auto-loaded เมื่ออยู่ใน wiki/)
- Cross-domain → `synthesis/` เสมอ

---

## AI Stack

```
User
  │
  ├─ Claude Code (Anthropic) — wiki agent, reasoning, synthesis, ingest [PRIMARY]
  │
  ├─ Codex (OpenAI) — same repo via .codex/AGENTS.md → reads CLAUDE.md
  │
  ├─ Gemini CLI (Google, free) — web search, lookup, datasheet [desktop only]
  │
  └─ NotebookLM Pro — synthesize >3 wiki pages (cache layer, manual)
```

---

## Directory Structure (ย่อ)

```
InW-Wiki/
├── CLAUDE.md          ← schema หลัก (ห้ามแก้ไม่ได้รับอนุญาต)
├── AGENTS.md          ← thin pointer → CLAUDE.md (สำหรับ Codex/GPT)
├── .claude/
│   ├── settings.json  ← permission allowlist + hooks config
│   ├── hooks/         ← edit protection + safety guards
│   └── skills/        ← reusable AI workflows (CANONICAL)
├── .agents/
│   └── skills/        ← mirror ของ .claude/skills/ สำหรับ Codex
├── .codex/
│   └── AGENTS.md      ← Codex-specific delegation rules
├── docs/
│   ├── protocols/     ← delegation, lifecycle, edit-protection, notebooklm ...
│   ├── runbooks/      ← recover-drive-conflict, setup-new-machine ...
│   └── architecture.md ← ไฟล์นี้
├── scripts/           ← gen-index.py, delegate.sh, export-to-notebooklm.sh ...
├── raw/               ← source (immutable, hook-protected)
├── wiki/              ← AI-managed knowledge base
│   ├── context/       ← fast-load files (wiki-overview, wiki-state, graph, memory)
│   ├── entities/      ← {iot,env,pharmacy,ai-tools}/
│   ├── concepts/      ← {iot,env,pharmacy,ai-tools}/
│   ├── sources/       ← source summaries
│   └── synthesis/     ← cross-domain analysis
└── exports/
    └── notebooklm/    ← bundle wiki → upload NotebookLM Pro
```

---

## Model-Agnostic Architecture

InW-Wiki ถูกออกแบบให้ **ไม่ผูกติดกับ AI model ใด model หนึ่ง**:

```
.claude/skills/*/SKILL.md   ← CANONICAL workflow files (Claude Code อ่าน)
.agents/skills/*/SKILL.md   ← Mirror ของ .claude/skills/ (Codex/GPT อ่าน)
                               ทั้งสองต้องมีเนื้อหาเหมือนกัน — อัปเดตทีเดียวทั้งคู่

docs/protocols/*.md         ← Detail protocols (load on demand)
CLAUDE.md / AGENTS.md       ← Summary + pointers เท่านั้น
```

**หลักการ**: `.claude/skills/*/SKILL.md` = single source of truth สำหรับ workflow — ไม่ว่า Claude, Codex, Gemini CLI, หรือ model อื่นในอนาคต ทุกตัวอ่าน workflow เดียวกัน

### Multi-API Search Stack (Auto-Fallback)

| Priority | Engine | API Key | Cost |
|----------|--------|---------|------|
| 1 | OpenRouter Free (28 models) | `$OPENROUTER_API_KEY` | ฟรี |
| 2 | Google AI Studio (Gemini Flash) | `$GEMINI_API_KEY` | ฟรี |
| 3 | Groq (Llama 3.3 70B) | `$GROQ_API_KEY` | ฟรี |
| 4 | Gemini CLI (desktop only) | OAuth | ฟรี |
| 5 | Claude WebSearch (built-in) | — | จ่าย token |

ทุก engine เรียกผ่าน `scripts/delegate.sh <task_type> "<prompt>"` — wrapper เลือก engine อัตโนมัติ

---

## Token Efficiency Strategy

| กลยุทธ์ | Mechanism | ประหยัด/ครั้ง |
|---------|-----------|--------------|
| Tier-1 quick load | `wiki-state.md` ~20 บรรทัด แทนโหลด full pages | ~300 tokens/query |
| Slim baseline | `wiki-overview.md` แทน index.md + abstracts | ~300 tokens/session |
| Lazy domain load | overview-{domain}.md โหลดเฉพาะเมื่อถามเรื่อง domain นั้น | ~100 tokens/query |
| Scoped context | nested `wiki/CLAUDE.md` auto-loaded ใน wiki/ dir | ~100 tokens/query |
| Skills on-demand | `.claude/skills/*/SKILL.md` โหลดเมื่อ trigger เท่านั้น | ~150 tokens/session |
| NotebookLM cache | synthesize >3 pages ผ่าน NotebookLM ไม่ต้องโหลด Claude | ~500 tokens/query |
| Free model delegate | `scripts/delegate.sh` → free engine แทน Claude WebSearch | ~200 tokens/search |

---

## 4-Tier Memory System

```
Tier 1: wiki/context/wiki-state.md       ← ~20 lines, hardware + status + stubs
Tier 2: wiki/context/wiki-overview.md    ← auto-gen, full abstract table (181 pages)
Tier 3: wiki/context/overview-{domain}.md ← domain detail (load on demand)
Tier 4: full wiki pages                  ← โหลดเมื่อ abstract ไม่เพียงพอ
```

---

## Solo Multi-Device Workflow

```
[Device A] edit → git push origin main
[Device B] session start → hook: git pull --ff-only origin main → latest
[Device C] same

SessionStart hook ensures every device starts from identical state.
No branches, no PRs — single main branch = single brain.
```
