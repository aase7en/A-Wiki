---
name: a-claim
description: "บังคับ: ประกาศงานก่อนแตะ shared surface เพื่อไม่ให้ agent หลายตัว (Claude/ZCode/Codex/Gemini) ทำงานซ้ำกัน. MCP `claim_acquire` / `claim_list` / `claim_advance` / `claim_release`; PreToolUse hook **block** เมื่อจะแก้ไฟล์ที่อยู่ใน claim ของ agent อื่น; lease หมดอายุเอง ไม่ล็อกค้าง. Trigger: 'claim', 'จอง', 'agent อื่น', 'ชนกัน', 'coordination'."
version: 1.0.0
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
> A-Wiki **มีเครื่องมือครบอยู่แล้ว** (TaskBoard มี TTL lease, Blackboard มี @mention,
> `.tmp/` ที่ทุก agent บนเครื่องเดียวกันอ่านร่วมกัน) — สิ่งที่ขาดคือ **gate**
> ไม่มีอะไรบังคับให้ประกาศก่อนลงมือ

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

### 1. `claim_list` — ดูก่อนเสมอ
```
claim_list()
→ zcode    [implement] a-flow stage gate   scope=scripts/lib/**  (42m left)
```
ถ้ามีคนทำเรื่องเดียวกันอยู่ → **หยุด แล้วคุยก่อน** (ข้อ 6)

### 2. `claim_acquire` — จอง
```
claim_acquire({
  "scope": ["skills/awiki/**", "scripts/skills_registry/**"],
  "goal":  "A-Suite v2 — auto-pick + 7-phase spine",
  "phase": "design"
})
```
- `scope` = glob ที่จะแตะ (`**` ครอบ subdir) — จองแคบที่สุดที่พอ
- `goal` = done criteria 1 บรรทัด (คนอื่นต้องอ่านแล้วรู้ว่าซ้ำกับตัวเองไหม)
- lease 1 ชม. ต่ออายุด้วย `claim_advance` หรือหมดอายุเอง

### 3–4. ทำงาน + เดิน phase
`claim_advance({"claim_id": "...", "phase": "implement"})` — ต่อ lease ให้ด้วยในตัว

### 5. `claim_release` — คืน
Stop hook (`release_agent_claims.py`) คืนให้อัตโนมัติตอนจบ session
ไม่ต้องกลัวลืม แต่คืนเองเร็วกว่าดีกว่า — คนอื่นจะได้ทำงานต่อได้

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
| "ลืมปล่อย claim" | lease หมดเอง + Stop hook ปล่อยให้ |

## Files

| ไฟล์ | บทบาท |
|---|---|
| `scripts/lib/agent_claims.py` | store + collision logic (atomic write) |
| `scripts/hooks/check_agent_claim.py` | PreToolUse gate (block on collision) |
| `scripts/hooks/release_agent_claims.py` | Stop — คืน claim ของ session |
| `.tmp/agent-claims.json` | state (gitignored, shared ทุก agent บนเครื่อง) |
| MCP `claim_*` | ทางเข้าสำหรับทุก agent |

> **ข้อจำกัดที่ต้องรู้**: `.tmp/` เป็น local → coordination ทำงานระหว่าง agent
> **บนเครื่องเดียวกัน** เท่านั้น ข้ามเครื่อง (Mac ↔ Work PC) ยังไม่ครอบคลุม —
> ใช้ blackboard + git commit message แทนไปก่อน

## Invocation

```
/A-Claim              # ดูสถานะ + จองงาน
```
