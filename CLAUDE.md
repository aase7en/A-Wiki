# A-Wiki — Hybrid Agent Wiki (Swarm + Knowledge) — Session Rules

> **A-Wiki** = repo หลักของระบบ — รวมพลัง swarm intelligence (A-Wiki) + knowledge wiki (InW-Wiki) + AI ecosystem skills (ECC, 9arm/claude-thai-skills)
> เบาที่สุด ทรงพลังที่สุด — ทุก layer ทำงานประสาน ไม่ชนกัน ไม่มี loop

---

## 🚨 First action every session

1. Read `agent-skills/README.md` — Iron Laws + Swarm Architecture
2. Read `wiki/context/wiki-overview.md` — wiki stats + synthesis + pointers
3. Read `wiki/context/session-memory.md` — cross-session decisions + TODOs

**Load on demand** (ห้าม load ทุก session):
- `wiki/context/overview-{iot,env,ai,pharmacy}.md` — ตาม domain ที่ถาม
- `wiki/context/knowledge-graph.md` — auto-gen relationships
- `agent-skills/swarm-intelligence/model-scouter.md` — free model routing

---

## 🏗️ Directory Structure (Hybrid — Swarm + Knowledge)

```
A-Wiki/
├── CLAUDE.md              ← Thin Pointer (นี้)
├── AGENTS.md              ← Multi-agent config (Claude/Codex/Gemini)
├── index.md / log.md / profile.md / session-memory.md
├── brain-map.canvas       ← Visual mind map
│
├── wiki/                  ← CORE KNOWLEDGE (จาก InW-Wiki)
│   ├── context/           ← ⚡ Fast-load overviews + session-memory
│   ├── entities/{iot,env,ai-tools,pharmacy}/
│   ├── concepts/{iot,env,ai-tools,pharmacy}/
│   ├── sources/           ← Source summaries
│   └── synthesis/         ← Cross-domain analysis
│
├── agent-skills/          ← ACTIVE LAYER (Swarm + Iron Laws)
│   ├── engineering/       ← debug-mantra, scrutinize, post-mortem
│   ├── productivity/      ← management-talk
│   ├── swarm-intelligence/← model-scouter, agile-swarm
│   ├── infrastructure/    ← git-safety
│   ├── automations/       ← hooks.py, run-task.sh
│   └── extensibility/     ← symlink-connector
│
├── skills/                ← ALL ECOSYSTEM SKILLS (ECC + 9arm + InW-Wiki)
│   ├── claude-code/       ← Original InW-Wiki skills (ingest-source, lint-wiki, etc.)
│   ├── claude-thai/       ← 9arm/claude-thai-skills (fuzzy-search, thai-ocr, etc.)
│   └── ecosystem/         ← ECC skills (everything-claude-code)
│
├── scripts/               ← Utility scripts (deduped)
│   ├── wiki/              ← wiki management (gen-index, search-wiki, etc.)
│   ├── swarm/             ← swarm ops (agent-switch, delegate, etc.)
│   └── ecosystem/         ← ECC scripts
│
├── raw/                   ← [Immutable] Source documents — ห้ามแก้ไข
├── docs/protocols/        ← Protocol docs (load on demand)
├── decisions/             ← ADRs
├── journal/               ← Daily journals
├── exports/               ← NotebookLM bundles
│
├── .claude/               ← Claude config (hooks, lock, agents)
├── .codex/                ← Codex config
├── .gemini/               ← Gemini config
└── .obsidian/             ← Obsidian vault
```

---

## 🧠 Swarm Intelligence Protocol (จาก A-Wiki)

| Role | Model | Responsibility |
|------|-------|----------------|
| **Architect** | OpenRouter free reasoning/CoT | Planning, root cause, design |
| **Executioner** | OpenRouter free flash/coder | Code writing, tests, refactoring |
| **Senior Critic** | Primary Agent (YOU) | Validate ALL outputs — NOT delegatable |

**Flow**: SCOUT → ALLOCATE → VALIDATE (ดู `agent-skills/swarm-intelligence/`)

---

## 💰 Cost-First Decision Pyramid (จาก InW-Wiki)

| Level | ช่องทาง | ใช้กับงาน |
|-------|---------|-----------|
| **-1** | Local FTS5 / knowledge-graph | **ฟรี + ออฟไลน์** — ค้น wiki, neighbors, hubs |
| **0** | Hook (SessionStart / PreToolUse) + Context Compaction | **ฟรี** — งานซ้ำทุก session, strategic `/compact` |
| **1** | Free API (OpenRouter free / Gemini Flash) | **ฟรี** — search, lookup, synthesis |
| **2** | Cheap paid (DeepSeek, Qwen) | **ถูกมาก** — reasoning เบา, table |
| **3** | Subagent (Claude Haiku / Explore) | **ถูก** — scan ไฟล์เยอะ, lint |
| **4** | Claude Sonnet (current) | **ปกติ** — เขียน wiki, schema, reasoning ซับซ้อน |

> **เริ่มจาก Level ต่ำสุดเสมอ** — เลื่อนขึ้นก็ต่อเมื่อ level ต่ำกว่าทำไม่ได้
> Prompt ส่งออกนอก: **ใช้ภาษาอังกฤษ** (ประหยัด ~30%)

---

## 🔗 Repository Integration (ECC + 9arm + InW-Wiki)

| Repo | Integration | Purpose |
|------|-------------|---------|
| **affaan-m/everything-claude-code** | `skills/ecosystem/` | ECC skill library — tool integrations, automations |
| **Boom-Vitt/claude-thai-skills** | `skills/claude-thai/` | Thai language skills — fuzzy-search, thai-ocr, line-bot |
| **Aase7en-InW-Wiki** (legacy) | Merged into `wiki/` + `skills/claude-code/` | Original knowledge base + wiki skills |

**Symlink**: `bash agent-skills/extensibility/symlink-connector.md` หรือ `bash scripts/link-my-skills.sh`

---

## 🔒 Iron Laws (UNBREACHABLE — จาก A-Wiki)

1. **NO production code without a failing test first**
2. **NO bug fixing without root cause investigation first** (debug-mantra 4-step)
3. **If parallel model violates #1 or #2 → DISCARD and REWRITE**
4. **raw/ is immutable** — ห้ามแก้ไขหรือลบ (hook-protected)
5. **CLAUDE.md ห้ามแก้โดยไม่ได้รับอนุญาต** — soft + hard lock

---

## ✅ Core Rules

1. **wiki/ เป็นของ AI agent** — สร้าง แก้ไข ดูแลทุกหน้า
2. **ชื่อไฟล์ wiki** ใช้ kebab-case ภาษาอังกฤษ
3. **อัปเดต `log.md` และ `wiki/context/` ทุกครั้ง** หลัง ingest หรือแก้ไขสำคัญ
4. **Confidence marker** บังคับ: `[training]` / `[verified YYYY-MM-DD]` / `[wiki]` / `[notebooklm YYYY-MM-DD]`
5. **Plan ก่อน implement เสมอ** — ถ้างานกระทบ >3 ไฟล์ → ระบุ: "จะแก้ [files] — ทำอะไรในแต่ละไฟล์"
6. **Commit ตรงลง main เท่านั้น** — ห้าม branch, ห้าม PR, ห้าม worktree
7. **ใช้ภาษาไทย** ในการสื่อสาร (เว้นแต่ถูกขอให้ใช้ภาษาอื่น)

---

## ⌨️ Quick Commands

> รายการเต็ม: `docs/protocols/quick-commands.md`
> Context compaction: `docs/protocols/context-compaction.md`
> Token optimization skill: `skills/claude-code/token-optimization/SKILL.md`

| Command | Action |
|---------|--------|
| `/verify <ข้อความ>` | Verify-before-done checklist (delegate to web search) |
| `/search "query"` | `python3 scripts/search-wiki.py "query"` |
| `/status` | สรุปสถานะ wiki: จำนวนหน้า, stale, pending |
| `/today` | สรุปสิ่งที่ทำใน session + commit message แนะนำ |
| `/lint` | Run wiki health check |
| `/ingest` | Ingest new source |
| `/snapshot-nb [domain]` | Export wiki → NotebookLM bundle |
| `/ask-nb <คำถาม>` | แนะนำ user ถาม NotebookLM ก่อน → paste → action ต่อ |
| `/compact [focus]` | Context compaction (ประหยัด 40-60%) — ดู `docs/protocols/context-compaction.md` |
| `/clear` | เคลียร์ context — เปลี่ยน task ใหม่ที่ไม่เกี่ยวกัน (ทำ `/rename <task>` ก่อน) |
| `/caveman` | Aggressive token saving mode — ตอบสั้น ~60-65% |
| `/delegate` | Subagent delegation (see `docs/protocols/delegation.md`) |

---

## 🔚 SESSION END PROTOCOL

1. สรุป ≤10 bullet (done / todo / key findings)
2. บันทึกลง `log.md` format: `## [YYYY-MM-DD] session | <หัวข้อ>`
3. อัปเดต `wiki/context/session-memory.md` — ตัดอันเก่าสุดถ้าเกิน 10 sessions
4. `git add . && git commit -m "session(DATE): ..." && git push origin main`
5. ถ้าแก้ wiki >5 หน้า → เสนอ `/snapshot-nb` ก่อนปิด

---

*Schema Hybrid v1.0 — Asse7en A-Wiki — 2026-05-24*
*Battery: A-Wiki swarm + InW-Wiki knowledge + ECC ecosystem + 9arm Thai skills*