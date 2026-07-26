---
name: a-router
description: "A-Suite dispatcher — รับงานแล้วบอกว่าใช้ skill ไหน phase ไหน. อ่าน trigger table จาก wiki/A-ROUTER.md (generated จาก skills-registry.json) หรือเรียก MCP `skill_route`. ไม่มี trigger ของตัวเองโดยตั้งใจ — จะได้ไม่แย่งงาน skill ปลายทาง. ใช้เมื่อ: ไม่รู้จะเริ่มยังไง, อยากเห็น 7-phase spine, หรือต้องการ route งานเข้า A-*."
version: 1.0.0
author: A-Wiki
domain: [engineering]
lifecycle_phase: meta
category: pipeline
agents: [all]
status: canonical
invocation: manual
invocation_hint: "/A-Router"
a_phase: any
# 2026-07-27 A-Suite v2 C6: ห้ามตั้ง invocation: auto — ตารางเต็มอยู่ใน
#   wiki/A-ROUTER.md อ่าน on-demand; a-plan/a-debug ถูกย้าย both→manual มาแล้ว
#   เพื่อประหยัด ~1.2k tokens/session ต่อตัว
---

# A-Router — ตัวจ่ายงานของ A-Suite

> **บาง ๆ โดยตั้งใจ** — ไม่มี logic เป็นของตัวเอง มีหน้าที่เดียวคือส่งงานให้ถูกคน
> ข้อมูลจริงอยู่ใน `skills-registry.json` → generate เป็น `wiki/A-ROUTER.md`

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
