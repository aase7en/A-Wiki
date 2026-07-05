---
type: entity
category: tool
tags: [mcp-server, memory, knowledge-graph, rag, typescript, opt-in]
sources: []
created: 2026-07-05
updated: 2026-07-05
last_verified: 2026-07-05
verify_tool: WebFetch
---

# GBrain

**ประเภท**: Standalone CLI + MCP server (stdio + HTTP) — memory/synthesis layer สำหรับ agent
**สถานะ**: opt-in — ไม่ auto-install, ติดตั้งผ่าน `scripts/setup-optional-mcp.sh --gbrain`
**License**: MIT
**Stars**: 25k★ (2026-07-05)

## ภาพรวม

GBrain (โดย Garry Tan, President/CEO ของ Y Combinator) เป็น "memory layer" ให้ agent — ไม่ใช่แค่ keyword/vector search แต่มี **synthesis layer** (ตอบเป็นร้อยแก้วพร้อม citation + gap analysis ว่า "brain ยังไม่รู้อะไรบ้าง") และ **self-wiring knowledge graph** (สกัด entity relationship อัตโนมัติทุกครั้งที่เขียนหน้าใหม่ โดยไม่ต้องเรียก LLM) [verified 2026-07-05]

รองรับทั้ง local (PGLite, ไม่ต้องมี server/Docker) และ scale-up (Postgres/Supabase + pgvector)

## ทำไมเป็น opt-in ไม่ integrate เต็มรูปแบบ

- **Tool-shaped ไม่ใช่ skill-shaped** — เป็น standalone service (ติดตั้งผ่าน `bun install -g`, รัน CLI + MCP server ของตัวเอง) ไม่ใช่ SKILL.md drop-in
- ใช้ runtime + DB ของตัวเอง (Bun + PGLite/Postgres) — ต่างจาก Matt Pocock skills ที่ไม่มี dependency เพิ่ม
- ทับซ้อนกับ A-Wiki's `wiki/context/session-memory.md` + local FTS5/vector index บางส่วน (ดูหัวข้อเปรียบเทียบด้านล่าง) — ผู้ใช้เลือกเปิดเองถ้าต้องการความสามารถ synthesis+graph ที่ A-Wiki's local index ยังไม่มี

## ติดตั้ง (opt-in)

```bash
bash scripts/setup-optional-mcp.sh --gbrain
```

Script ทำ:
1. เช็ค Bun runtime (ติดตั้งเองถ้าไม่มี: `curl -fsSL https://bun.sh/install | bash`)
2. `bun install -g github:garrytan/gbrain`
3. `gbrain init --pglite` (local brain, ~2 วินาที ไม่ต้อง Docker)

หลังจากนั้น register MCP เอง (ต้องตอบคำถาม API key แบบ interactive):
```bash
claude mcp add gbrain -- gbrain serve
```
หรือ merge `"gbrain"` entry จาก `.mcp.json.example` เข้า `.mcp.json` (`disabled: false`)

**Import A-Wiki เป็น corpus เริ่มต้น** (ถ้าต้องการทดลอง synthesis layer กับข้อมูลที่มีอยู่แล้ว):
```bash
gbrain import wiki/
gbrain query "สรุปความสัมพันธ์ระหว่าง IoT กับ pharmacy domain"
```

## เปรียบกับระบบ memory ที่ A-Wiki มีอยู่แล้ว

| | **A-Wiki (FTS5 + sqlite-vec + knowledge-graph.md)** | **GBrain** |
|-|-|-|
| ต้นทุน | Local, ฟรี, offline (Level -1 ใน Cost Pyramid) | ต้องมี Bun + PGLite/Postgres + LLM key สำหรับ synthesis |
| Output | Search results (keyword+semantic) + graph neighbors | Synthesized prose + citation + gap analysis |
| Graph | Manual-ish (`build-wiki-graph.py`, link-based) | Self-wiring อัตโนมัติทุก write (typed edges: works_at, invested_in ฯลฯ) |
| Scope | wiki/ ของ A-Wiki เท่านั้น | รับ import ได้ทุก markdown corpus (meetings, people, companies) |
| ใช้คู่กันได้? | ✅ — GBrain เสริม synthesis layer ให้ query ที่ local search ตอบได้แค่ "นี่คือหน้าที่เกี่ยวข้อง" |

## ข้อดี / ข้อเสีย

| ข้อดี | ข้อเสีย |
|-------|---------|
| Synthesis layer จริง ไม่ใช่แค่ document dump | ต้องติดตั้ง Bun runtime แยก (ไม่ใช่ pip/npm มาตรฐาน) |
| Self-wiring graph ไม่ใช้ LLM call ต่อ write | ต้องมี LLM API key สำหรับ synthesis query |
| Local PGLite = ไม่ต้อง Docker/server สำหรับเริ่มต้น | ทับซ้อนกับ session-memory.md + local index บางส่วน — ต้องตัดสินใจว่าจะใช้คู่กันยังไงไม่ให้สับสน |
| MIT license | 25k★ community ใหญ่ แต่ project ใหม่ (2026) — ยังไม่ mature เท่า established tools |
| Benchmark ดี (P@5 49.1%, +31.4pt เหนือ vector-only RAG) | Company-brain mode (multi-user) ซับซ้อนเกินความจำเป็นสำหรับ personal wiki เดี่ยว |

## ความสัมพันธ์

- เกี่ยวข้องกับ: [[gitnexus]] — คนละ layer (GitNexus = code graph, GBrain = knowledge/memory graph)
- เกี่ยวข้องกับ: [[graphify]] — Graphify เน้นแปลงไฟล์เป็น graph แบบ one-shot; GBrain เน้น 24/7 memory daemon ที่ enrichment ต่อเนื่อง
- พิจารณาแล้วไม่ integrate: [[deer-flow]] — ทั้งคู่เป็น "agent brain/harness" แต่ scope ต่างกัน (GBrain = memory only, DeerFlow = full orchestration harness ซึ่งซ้ำกับ Hermes)

## แหล่งข้อมูล

- GitHub: https://github.com/garrytan/gbrain
- Author: Garry Tan (Y Combinator)
- [verified 2026-07-05] `gh api repos/garrytan/gbrain` — MIT, 25,018 stars, TypeScript
