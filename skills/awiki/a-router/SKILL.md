---
name: a-router
description: "A-Suite dispatcher + session-start pointer — รับงานแล้วบอกว่าใช้ skill ไหน phase ไหน. อ่าน trigger table จาก wiki/A-ROUTER.md (generated จาก skills-registry.json) หรือเรียก MCP `skill_route`. ไม่มี trigger ของตัวเองโดยตั้งใจ — จะได้ไม่แย่งงาน skill ปลายทาง. ใช้เมื่อ: ไม่รู้จะเริ่มยังไง, อยากเห็น 7-phase spine, หรือต้องการ route งานเข้า A-*. รวม awiki-lifecycle-router (session-start) + a-route (suggest+confirm) เข้ามาเป็นตัวเดียว 2026-08-09."
version: 1.1.0
author: A-Wiki
domain: [engineering]
lifecycle_phase: meta
category: pipeline
agents: [all, hermes]
status: canonical
invocation: manual
invocation_hint: "/A-Router"
a_phase: any
# 2026-08-09 v1.1.0: merge a-route + awiki-lifecycle-router → a-router ตัวเดียว
#   (3 routers ซ้อนทับ → 1). a-route ละเมิด Iron Law #10 (keyword dict hardcoded),
#   lifecycle-router ซ้อนทับ registry-driven logic. a-router รวมหน้าที่ทั้งคู่.
# 2026-07-27 A-Suite v2 C6: ห้ามตั้ง invocation: auto — ตารางเต็มอยู่ใน
#   wiki/A-ROUTER.md อ่าน on-demand; a-plan/a-debug ถูกย้าย both→manual มาแล้ว
#   เพื่อประหยัด ~1.2k tokens/session ต่อตัว
---

# A-Router — ตัวจ่ายงานของ A-Suite (router ตัวเดียว)

> **บาง ๆ โดยตั้งใจ** — ไม่มี logic เป็นของตัวเอง มีหน้าที่เดียวคือส่งงานให้ถูกคน
> ข้อมูลจริงอยู่ใน `skills-registry.json` → generate เป็น `wiki/A-ROUTER.md`
>
> **2026-08-09 merge**: a-route (keyword scoring, ละเมิด Iron Law #10) +
> awiki-lifecycle-router (session-start pointer) ถูกรวมเข้าที่นี่ →
> router เดียวที่ใช้ registry เป็น source of truth

## เมื่อไหร่ใช้

✅ ใช้:
- ได้งานมาแล้วไม่รู้ว่าควรใช้ skill ไหน
- อยากเห็น 7-phase spine ทั้งหมด
- เริ่มงานหลาย step แล้วอยากตั้ง focus ให้ถูก phase

❌ ข้าม:
- รู้อยู่แล้วว่าจะใช้อะไร → เรียกตรง (`/A-Debug`, `/A-Plan`, …)
- งาน trivial (ตอบคำถามสั้น, typo, lookup) → ทำเลย ไม่ต้อง route

## Iron Law

> **ROUTE แล้วต้อง `focus_set` เสมอ** — ถ้า route แล้วไม่ประกาศ focus
> session จะไหลข้าม phase โดยไม่มีอะไรจับได้

## Flow (4 steps)

```
┌──────────┐   ┌──────────────┐   ┌───────────┐   ┌──────────────┐
│ 1 match  │──▶│ 2 เลือก skill│──▶│ 3 focus_  │──▶│ 4 ส่งต่อ      │
│ triggers │   │   + phase     │   │   set     │   │   skill ปลายทาง│
└──────────┘   └──────────────┘   └───────────┘   └──────────────┘
                      │ ไม่ match
                      ▼
                 ┌──────────┐
                 │ a-think  │  (fallback — ห้ามเดา)
                 └──────────┘
```

### Step 1: match triggers

เลือกทางที่ถูกกับ agent ที่กำลังรันอยู่ — **ทั้งสามทางอ่าน `triggers` field เดียวกัน**:

| ถ้าคุณคือ | ทำ |
|---|---|
| Claude Code | hook `check_a_route.py` เสนอให้อัตโนมัติตอน user พิมพ์ |
| agent ที่ต่อ MCP ได้ (Codex/ZCode/Gemini/Claude) | เรียก `skill_route({"text": "<request>"})` |
| agent ที่ไม่มี hook/MCP (Cline/Windsurf/Cursor/Aider/Kilo) | อ่าน `wiki/A-ROUTER.md` §2 แล้ว match เอง |

> parity คือ**ข้อมูล** ไม่ใช่**กลไก** — harness แต่ละตัวมี hook ไม่เท่ากัน
> (Claude 6 events, Codex 5, Gemini 2, Cline/Windsurf/Cursor/Aider 0)

### Step 2: เลือก skill + phase

- ได้ผลลัพธ์ → ใช้ตัวคะแนนสูงสุด
- ได้ `[]` → **`a-think`** (fallback) ห้ามเดาเอง
- ได้หลายตัวคะแนนใกล้กัน → ถาม user 1 คำถาม อย่าทายมั่ว

### Step 3: `focus_set`

```
focus_set({"skill": "a-plan", "goal": "<done criteria 1 บรรทัด>", "phase": "ask"})
```

phase เริ่มต้น = `ask` เสมอ เว้นแต่รู้ชัดว่าข้ามได้ (เช่น bug ชัดเจน → `debug`)

### Step 4: ส่งต่อ

อ่าน SKILL.md ของ skill ปลายทาง แล้วทำตาม chain ของมัน
ระหว่างทางเดิน phase ด้วย `focus_advance` — จบงานแล้ว `focus_clear`

## 7-phase spine

```
ASK → DESIGN → PLAN → IMPLEMENT → REVIEW → DEBUG → TEST
```

รายละเอียดต่อ phase + skill ที่ป้อนเข้าแต่ละ phase → `wiki/A-ROUTER.md` §1

## Session-start routing (จาก awiki-lifecycle-router ที่รวมเข้ามา)

เมื่อ task มาถึง (session start หรือ mid-session) map intent เร็ว:

```
Task arrives
    │
    ├── ไม่รู้ว่าจะใช้อะไร? ─────────────→ /A-Router  (หรือ MCP skill_route)
    ├── ยังไม่ชัดว่าต้องการอะไร? ────────→ /A-Think → grill-with-docs
    ├── ออกแบบ / วางแผนของใหม่? ─────────→ /A-Plan
    ├── งานเว็บ / frontend? ─────────────→ /A-Web
    ├── เอกสารราชการ / docx? ────────────→ /A-Doc
    ├── ค้นคว้า / วิจัย / ตรวจแหล่ง? ────→ /A-Research
    ├── คอนเทนต์ / การตลาด? ─────────────→ /A-Content
    ├── การลงทุน? ───────────────────────→ /A-Invest
    ├── รีวิวก่อน ship? ─────────────────→ /A-Council
    ├── พัง / bug / test แดง? ───────────→ /A-Debug
    ├── งานยาวข้าม session? ─────────────→ /A-Loop "<objective>"
    └── เกินกำลัง model ปัจจุบัน? ───────→ /A-Escalate
```

ไม่ match อะไรเลย → **`/A-Think`** (fallback — ห้ามเดา)

### A-Wiki domain-specific intents

```
    ├── Wiki ingest (URL / pasted text / file)? → ingest-source
    ├── Platform fetch (Reddit/YouTube/Bilibili, no-auth)? → platform-ingest
    ├── Wiki health check / lint? ──────────────→ lint-wiki
    ├── Wiki search? ───────────────────────────→ wiki-search-local
    ├── Pharmacy order lookup? ─────────────────→ pharmacy-order-lookup
    ├── Cross-domain synthesis? ────────────────→ ask-notebooklm
    ├── Multi-model delegation? ────────────────→ delegate-subagent
    └── Refine vague ideas? ────────────────────→ brainstorm-before-build
```

## Core operating behaviors

ใช้ตลอดเวลา ข้ามทุก skill:

1. **Route, then declare focus.** หลังเลือก skill แล้วเรียก MCP `focus_set`
   พร้อม skill, goal 1 บรรทัด, และ phase เริ่มต้น — ถ้าไม่ จะไม่มีอะไรจับได้ว่า
   session ไหลจาก DESIGN ไป IMPLEMENT
2. **Walk the chain.** `focus_advance` ระหว่าง phase, `focus_clear` ตอนจบ
3. **ห้ามข้าม ASK/DESIGN บนงาน non-trivial** — ส่วนใหญ่ fail ที่ requirement ไม่ใช่ coding
4. **Fallback คือการตัดสินใจ ไม่ใช่การเดา** — ไม่ match = `/A-Think`,
   ไม่ใช่ "เลือก skill ที่ดูใกล้สุด"
5. **State assumptions** — พูดก่อน implement ห้ามเดาเงียบ
6. **Verify, don't assume** — "ดูน่าจะใช่" ไม่พอ
7. **Registry เป็น source of truth** (Iron Law #10) — จะแก้ discovery ต้องแก้
   `skills-registry.json` แล้วรัน `python scripts/regen-skill-surfaces.py`
   ห้ามแก้ generated surface มือ

## Rationalization table

| ข้ออ้าง | คำตอบโต้ |
|---|---|
| "รู้อยู่แล้วว่าจะใช้อะไร ข้าม route" | ถูก — เรียกตรงเลย แต่ยังต้อง `focus_set` |
| "งานเล็ก ไม่ต้อง focus" | งานเล็กจริงข้ามได้; ถ้า >3 ไฟล์ หรือ >1 phase = ไม่เล็ก |
| "ไม่ match เลย เดาๆ ไปก่อน" | ไม่ได้ — `[]` แปลว่า a-think ไม่ใช่ "ทายตัวที่ใกล้สุด" |
| "แก้ trigger ใน SKILL.md เอาเลย" | ไม่ได้ — registry เป็น source of truth (Iron Law #10) แก้ registry → regen |

## Examples

**Bad (เดา)**:
```
user: ช่วยดูหน่อยว่าทำไมมันช้า
agent: [เปิด a-plan] → ออกแบบใหม่ทั้งระบบ → ไม่ตรงโจทย์
```

**Good (route)**:
```
user: ช่วยดูหน่อยว่าทำไมมันช้า
skill_route("ช่วยดูหน่อยว่าทำไมมันช้า") → []            ← ไม่มี trigger ตรง
→ fallback a-think → restate: "อาการคือ latency สูง ยังไม่รู้ root cause"
→ a-think ชี้ว่าเป็น debug → focus_set(a-debug, phase=debug)
→ เดิน chain ของ a-debug
```

## Files

| ไฟล์ | บทบาท |
|---|---|
| `skills-registry.json` | source of truth (`triggers`, `a_phase`) |
| `scripts/skills_registry/routing.py` | matcher ตัวจริง (ตัวเดียว ห้าม fork) |
| `wiki/A-ROUTER.md` | ตาราง generated — agent อ่านตรง ห้ามแก้มือ |
| `scripts/hooks/check_a_route.py` | auto-suggest (Claude เท่านั้น) |
| MCP `skill_route` / `focus_*` | ทางเข้าสำหรับ agent อื่น |

## Invocation

```
/A-Router "<งานที่จะทำ>"
```
