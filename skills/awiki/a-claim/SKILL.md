---
name: a-claim
description: "บังคับ: COLLAB/Git คือ durable cross-machine claim authority; `claim_acquire` ต้องมี exact `task_id` แล้ว mirror ไป TTL cache; `claim_list`/`claim_advance`/`claim_release` เป็น derived same-machine cache; hook block เฉพาะ RECONCILED foreign claim. Trigger: 'claim', 'จอง', 'agent อื่น', 'ชนกัน', 'coordination'."
version: 1.1.0
author: A-Wiki
domain: [engineering, ai-ops]
lifecycle_phase: meta
category: pipeline
agents: [all]
status: canonical
invocation: both
invocation_hint: "/A-Claim"
a_phase: any
---

# A-Claim — ระบบจองงานข้าม Agent (บังคับ)

> **ทำไมมี**: 2026-07-27 Claude กับ ZCode สร้าง intent-router ตัวเดียวกัน + phase
> state machine ตัวเดียวกัน ใน repo เดียวกัน branch เดียวกัน ชั่วโมงเดียวกัน
> ทั้งคู่ไม่รู้เลยจนกระทั่ง merge ลง main แล้ว
>
> ปัจจุบัน **COLLAB.md + Git เป็น durable authority ข้ามเครื่อง** ส่วน `.tmp/agent-claims.json`
> เป็น derived TTL cache สำหรับ same-machine fast enforcement เท่านั้น. `claim_acquire`
> ต้องผูก exact `task_id` แล้วเขียน durable claim ก่อนจึงค่อย mirror cache; TTL row ที่
> reconcile ไม่สำเร็จห้ามกลายเป็น ownership authority.

## Iron Law

> **ประกาศก่อนแตะ shared surface — ทุกครั้ง ทุก agent**
> `check_cost_tier` บังคับประกาศต้นทุน · `check_skill_registry` บังคับลงทะเบียน skill
> · **`check_agent_claim` บังคับประกาศงาน**

## เมื่อไหร่ใช้

✅ บังคับ:
- ก่อนแก้ `skills/`, `scripts/`, `commands/`, `agents/`, `skills-registry.json`, `AGENTS.md`, `.claude/settings.json`
- ก่อนเริ่มงานหลาย step ที่กินเวลาเกิน ~15 นาที

✅ ควรใช้:
- ก่อนเริ่ม**อะไรก็ตาม**ที่ไม่ trivial → `claim_list` ดูก่อนว่ามีคนทำอยู่ไหม (ฟรี, 1 call)

❌ ข้าม:
- แก้ไฟล์ส่วนตัว / `.tmp/` / scratch
- อ่านอย่างเดียว (hook ไม่ยุ่งกับ Read/Grep/Bash)

## Flow

```
┌────────────┐   ┌──────────────┐   ┌────────┐   ┌────────────┐   ┌──────────────┐
│ 1 claim_   │──▶│ 2 claim_     │──▶│ 3 ทำงาน │──▶│ 4 claim_   │──▶│ 5 claim_     │
│   list     │   │   acquire    │   │        │   │   advance  │   │   release    │
│ (ใครทำอะไร)│   │ (จอง scope)  │   │        │   │ (ตาม phase)│   │ (คืนของ)     │
└────────────┘   └──────────────┘   └────────┘   └────────────┘   └──────────────┘
      │ มีคนทำอยู่แล้ว
      ▼
 ┌──────────────────────────────┐
 │ bb_post คุยกับเขา — อย่าทำซ้ำ │
 └──────────────────────────────┘
```

### 1. `claim_list` — ดู cache บนเครื่องนี้
```
claim_list()
→ zcode    [implement] a-flow stage gate   scope=scripts/lib/**  (42m left)
```
`claim_list` เป็น **derived same-machine cache** ไม่ใช่ cross-machine SSoT. ถ้ารู้ task id
ให้ตรวจ durable truth ด้วย `python -m conductor claims --task-id "<WO-ID>" --json`.
ถ้ามี owner อื่นใน durable claim หรือ RECONCILED cache → **หยุด แล้วคุยก่อน** (ข้อ 6).

### 2. `claim_acquire` — durable-first
```
claim_acquire({
  "task_id": "WO-EXACT-ID",
  "scope": ["skills/awiki/**", "scripts/skills_registry/**"],
  "goal":  "A-Suite v2 — auto-pick + 7-phase spine",
  "phase": "design"
})
```
- `task_id` = exact durable identity; ห้าม fuzzy/ตั้งใหม่ถ้ามี WO/claim เดิมอยู่แล้ว
- `scope` = glob ที่จะแตะ (`**` ครอบ subdir) — จองแคบที่สุดที่พอ
- `goal` = done criteria 1 บรรทัด
- ระบบเขียน/ยืนยัน **COLLAB/Git ก่อน** แล้วจึง mirror ไป TTL cache
- TTL lease เป็น cache acceleration เท่านั้น; หมดอายุแล้ว durable claim ยังอยู่

### 3–4. ทำงาน + เดิน phase
`claim_advance({"claim_id": "...", "phase": "implement"})` เปลี่ยน phase/ต่อ lease ของ
**derived cache เท่านั้น**; durable owner/scope ใน COLLAB/Git ไม่เปลี่ยน.

### 5. `claim_release` — ปล่อย cache; durable release แยก
`claim_release` และ Stop hook (`release_agent_claims.py`) ปล่อยเฉพาะ TTL cache.
การจบงานต้อง update/release **แถว durable เดิมใน `COLLAB.md` ผ่าน Git** ตาม work-order
protocol; ห้ามถือว่า cache หมดอายุหรือถูก release แล้ว ownership ข้ามเครื่องหายไปด้วย.

### 6. ถ้าชน — คุย ไม่ใช่แย่ง
```
bb_post({"frm":"claude","to":"zcode","type":"question",
         "body":"เห็นว่าจอง scripts/lib/** อยู่ — ผมจะแตะ neural_spine_mcp.py ชนไหม?"})
bb_read({"to_filter":"claude"})
```

## สิ่งที่ hook ทำให้

| สถานการณ์ | ผล |
|---|---|
| แก้ไฟล์ที่อยู่ใน claim ของ agent อื่น | 🛑 **BLOCK (exit 2)** + บอกว่าใคร ทำอะไร phase ไหน ติดต่อยังไง |
| แก้ shared surface โดยไม่มี claim | ⚠️ เตือน (ไม่ block — ไม่งั้น deadlock tool ที่ใช้สร้าง claim) |
| แก้ไฟล์ทั่วไป | เงียบ |
| claim หมดอายุ | reap อัตโนมัติตอนอ่าน — agent ที่ crash ไม่ล็อก repo ค้าง |
| SessionStart | แสดง claim ของ agent อื่นให้เห็นก่อนเริ่ม |

## Rationalization table

| ข้ออ้าง | คำตอบโต้ |
|---|---|
| "งานเล็ก ไม่ต้องจอง" | 2026-07-27 ทั้งสองฝั่งก็คิดแบบนี้ — เสียเวลารวมหลายชั่วโมง |
| "จองกว้างๆ ไว้ก่อนกันเหนียว" | ผิด — จองกว้าง = block คนอื่นเกินจำเป็น จองแคบที่สุดที่พอ |
| "อีก agent ไม่ได้ใช้ระบบนี้" | มันอยู่ใน MCP → ทุก agent ที่ต่อ MCP ได้ใช้ได้ ไม่ใช่ของ Claude ตัวเดียว |
| "block น่ารำคาญ ปิดดีกว่า" | `AWIKI_CLAIM_GATE=0` ปิดได้ แต่มัน print BYPASSED ให้เห็น — เจตนาคือให้เห็น ไม่ใช่ให้เงียบ |
| "ลืมปล่อย claim" | TTL cache หมดเอง/Stop hook ปล่อยได้ แต่ durable COLLAB claim ต้อง release/update ผ่าน Git เมื่อ chunk จบ |

## Files

| ไฟล์ | บทบาท |
|---|---|
| `COLLAB.md` + Git | **canonical durable cross-machine ownership authority** |
| `conductor claims --task-id ... --json` | exact durable claim reader |
| `scripts/lib/agent_claims.py` | derived TTL cache + collision logic |
| `scripts/hooks/check_agent_claim.py` | PreToolUse gate; durable fallback + RECONCILED cache enforcement |
| `scripts/hooks/release_agent_claims.py` | Stop — ปล่อย derived cache ของ session |
| `.tmp/agent-claims.json` | derived same-machine cache (gitignored; ไม่ใช่ authority) |
| MCP `claim_*` | durable-first acquire + cache list/advance/release |

> **Cross-machine rule**: ownership ดูจาก COLLAB/Git. `.tmp/` ช่วยให้ hook เร็วบนเครื่องเดียวกัน
> และอาจเป็น `PARTIAL_UNRECONCILED`; row แบบนั้นเป็นข้อมูลประกอบและ **ห้าม block ในฐานะ owner**.

## Invocation

```
/A-Claim              # ดูสถานะ + จองงาน
```
