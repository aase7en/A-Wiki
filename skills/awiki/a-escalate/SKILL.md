---
name: a-escalate
description: "สร้าง prompt แบบ self-contained ส่งให้ model ที่เก่งกว่าช่วยคิด — รวม goal, constraints, สิ่งที่ลองแล้ว (ดึงจาก memory-ledger อัตโนมัติ), ไฟล์ที่เกี่ยว, done-criteria, และคำถามเดียว. เขียนลง exports/escalate/ แล้วให้ user ก๊อปไปวางเอง — ไม่ส่งข้อมูลออกเอง. Trigger: 'escalate', 'ส่งให้โมเดลอื่น', 'ถามโมเดลที่เก่งกว่า', 'second opinion'."
version: 1.0.0
author: A-Wiki
domain: [engineering]
lifecycle_phase: meta
category: pipeline
agents: [all]
status: canonical
invocation: manual
invocation_hint: "/A-Escalate"
a_phase: any
---

# A-Escalate — แพ็คปัญหาส่งโมเดลที่เก่งกว่า

> **ไม่ส่งข้อมูลออกเอง** — สร้างไฟล์ให้ user ก๊อปไปวางเอง
> เป้าหมายเป้าหมายเดียว: ทำให้โมเดลปลายทาง **ไม่ต้องเดาอะไรเลย**

## เมื่อไหร่ใช้

✅ ใช้:
- debug วนเกิน 3 รอบแล้วยังไม่จบ
- ตัดสินใจ architecture ที่ผิดแล้วแพง
- งานที่ต้องการ reasoning ลึกกว่าที่ model ปัจจุบันทำได้
- อยาก second opinion ก่อนลงมือของใหญ่

❌ ข้าม:
- ยังไม่ได้ลองเอง (escalate ตั้งแต่ยังไม่ repro = เสียเวลาโมเดลใหญ่)
- คำถามที่ค้น wiki/docs ได้ → `/search` ก่อน
- งานที่แค่ยาว ไม่ได้ยาก → `/A-Loop`

## Iron Law

> **ต้อง REPRO ได้ก่อน ESCALATE** (สืบทอดจาก debug-mantra mantra #1)
> ส่งอาการคลุมเครือไปให้โมเดลใหญ่ = ได้คำตอบคลุมเครือกลับมา แพงกว่าเดิม

## ทำไมต้องมี skill นี้

โมเดลปลายทาง **ไม่มี context ของ session นี้เลย** — อะไรที่เราคิดในใจแล้วไม่เขียน
ถือว่าหายหมด. คนเขียน prompt เองมักตกสามอย่างนี้เสมอ:

| ตก | ผลที่ได้ |
|---|---|
| "ลองอะไรไปแล้วบ้าง" | โมเดลเสนอวิธีที่เราลองแล้วและพังแล้ว |
| constraints | ได้คำตอบที่ทำไม่ได้จริงในระบบเรา |
| done-criteria | ได้คำตอบยาวๆ ที่ไม่รู้ว่าจบหรือยัง |

script ดึง "ลองอะไรไปแล้ว" จาก `.tmp/memory-ledger.jsonl` (type = failure/lesson/decision)
ให้อัตโนมัติ — ช่องที่มีค่าที่สุดและคนขี้เกียจเขียนที่สุด

## Flow (4 steps)

```
┌──────────┐   ┌───────────────┐   ┌──────────┐   ┌───────────┐
│ 1 repro  │──▶│ 2 รวบรวม      │──▶│ 3 render │──▶│ 4 user    │
│   ให้ได้  │   │   บริบท       │   │   ไฟล์    │   │   ก๊อปไปวาง│
└──────────┘   └───────────────┘   └──────────┘   └───────────┘
```

### Step 1: repro ให้ได้ก่อน
ถ้ายัง repro ไม่ได้ → กลับไป `/A-Debug` mantra #1 ก่อน **ห้ามข้าม**

### Step 2: รวบรวมบริบท
ถาม user ให้ครบ (หรือเติมเองถ้ารู้อยู่แล้ว):
- **goal** — จะทำอะไรให้สำเร็จ
- **question** — คำถามเดียวที่อยากได้คำตอบ (ไม่ใช่สามคำถาม)
- **constraints** — อะไรห้ามแตะ / ต้องคงไว้
- **done** — รู้ได้ยังไงว่าจบ
- **files** — ไฟล์ที่เกี่ยว (จะถูก embed เป็น excerpt 60 บรรทัดแรก)

### Step 3: render

```bash
python scripts/a_escalate.py \
  --goal "ทำให้ dashboard โหลดใน <2s" \
  --question "ทำไม query นี้ยังช้าแม้ใส่ index แล้ว?" \
  --constraint "ห้ามเปลี่ยน schema (production)" \
  --constraint "ต้องรองรับ Postgres 14" \
  --done "p95 < 2s ที่ 10k rows" \
  --tried "ใส่ index บน created_at แล้ว — ดีขึ้น 10% เอง" \
  --file scripts/query.py
```

Flags: `--constraint/--tried/--file/--done` ใส่ซ้ำได้ · `--stdout` พิมพ์แทนเขียนไฟล์ ·
`--no-ledger` ไม่ต้องดึงจาก memory-ledger · `--slug` ตั้งชื่อไฟล์เอง

### Step 4: ส่ง
ได้ path ใน `exports/escalate/<slug>.md` → **บอก user ให้ก๊อปไปวาง** ในโมเดลที่เลือก
(ไม่ hardcode ว่าโมเดลไหน — เปลี่ยนเร็วกว่าที่ skill จะตามทัน)

## Rationalization table

| ข้ออ้าง | คำตอบโต้ |
|---|---|
| "อธิบายสั้นๆ พอ เดี๋ยวมันเดาได้" | มันเดาไม่ได้ — ไม่มี context เรา สิ่งที่ไม่เขียน = หาย |
| "ยังไม่ได้ลอง แต่ดูยาก escalate เลย" | ผิด Iron Law — repro ก่อน ไม่งั้นได้คำตอบคลุมเครือ |
| "ส่งทั้ง repo ไปเลยดีกว่า" | ไม่ — 60 บรรทัดที่ตรงจุด ดีกว่า 5000 บรรทัดที่ไม่ตรง |
| "ให้ agent ส่ง API เองเลยสิ" | ตั้งใจไม่ทำ — ข้อมูลออกนอกเครื่องต้องผ่านสายตา user |

## Files

| ไฟล์ | บทบาท |
|---|---|
| `scripts/a_escalate.py` | renderer |
| `exports/escalate/` | output (gitignored — ephemeral) |
| `.tmp/memory-ledger.jsonl` | source ของ "ลองอะไรไปแล้ว" |

## Invocation

```
/A-Escalate
```
