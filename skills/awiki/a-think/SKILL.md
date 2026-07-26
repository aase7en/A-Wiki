---
name: a-think
description: "Core reasoning loop ที่ run ก่อนตอบ non-trivial request — merge fable-method (eval-driven, Sahir619) + fable5-standards (A-Wiki native). 7 steps: Restate → Done-criteria → Decompose → ≥2 Approaches → Pre-mortem → Right-size → Prove. Trigger: design/debug/migration/multi-step/competing-approaches/security-sensitive. Skip: simple lookup, typo fix, ingest ตรง. Foundation ที่ A-Plan/A-Debug/A-Doc/A-Business เรียกใช้ (manual + referenced)."
version: 1.1.0
author: A-Wiki (fable merge)
domain: [engineering]
lifecycle_phase: meta
category: pipeline
agents: [all]
status: canonical
invocation: both
invocation_hint: "/A-Think"
tags: [reasoning, fable, fable5, planning, debug]
# 2026-07-26 v1.1.0: augment step 4 with design-first prompting template (MengTo pattern)
# 2026-07-27 C1: เติม domain/lifecycle_phase/category/agents/status/invocation ที่หายไป
#   — sibling A-* ทุกตัวมีครบ, registry ก็มีครบ, ขาดแค่ SKILL.md นี้ไฟล์เดียว
---

# A-Think — Core Reasoning Loop

> **Foundation skill** ของ A- suite — `/A-Plan`, `/A-Debug`, `/A-Doc`, `/A-Business` ทุกตัวเริ่มด้วย A-Think
> Merge จุดเด่นของ **fable-method** (Sahir619 — eval-driven, classify/act/prove) + **fable5-standards** (A-Wiki native — stakeholder + communication)

## เมื่อไหร่ใช้

✅ ใช้ (non-trivial):
- ออกแบบ/วางแผน ระบบ, feature, schema
- Debug bug ซับซ้อน
- Migration / data move
- เลือกระหว่าง competing approaches
- Security-sensitive design
- Multi-step task (≥3 ไฟล์)

❌ ข้าม (trivial — ใช้ time ไปทำ):
- Lookup ข้อมูลเดียว
- Typo fix
- ingest source ตรงๆ
- เพิ่ม 1 หน้า wiki

## Iron Law

> **NO ANSWER WITHOUT A-THINK 7-STEP FIRST** (สำหรับ non-trivial request)

ถ้า task = non-trivial ต้องรัน 7 ขั้นตอนนี้ก่อน propose/answer — write it out สำหรับเรื่องจริงๆซับซ้อน

## 7-Step Loop (เรียงบังคับ)

### 1. Restate the real problem
- อะไรกำลังถูกถามจริงๆ? premise ถูกมั้ย?
- **Fix wrong question ก่อน** answer — ถ้าคำถามผิด คำตอบก็ผิอ
- 1 ประโยค: "ปัญหาจริงๆคือ..."

### 2. Done-criteria (fable-method "define done")
- Success หน้าตาเป็นยังไง? ยังไงถึงเรียกว่า "เสร็จ"
- Budget / time / skill level / environment constraints
- **Hospital-specific**:
  - วันที่ = **พ.ศ.** เสมอ (Buddhist Era = CE + 543) ไม่ assume CE
  - ข้อมูลคนไข้ (PHI) **ไม่ออกนอกระบบ** — hard architecture boundary
  - **Z.ai / GLM cloud (ZCode)** อยู่ใต้กฎหมายจีน → **ห้าม route** ข้อมูลคนไข้แม้ indirect

### 3. Decompose
- แตกเป็น sub-problems **เล็กพอที่ verify ได้ทีละตัว**
- แต่ละ sub-problem = test ได้ด้วยตัวเอง

### 4. ≥2 Approaches + trade-off
- Generate **อย่างน้อย 2 approaches** (ห้าม single-hypothesis)
- เปรียบเทียบ trade-off:
  - complexity / cost / failure modes
  - **one-way doors** (ยากกลับ) vs **two-way doors** (กลับง่าย) — flag one-way ชัดๆ
- รูปแบบตาราง:

| Approach | Complexity | Cost | Failure mode | Reversible? |
|---|---|---|---|---|
| A | ... | ... | ... | two-way |
| B | ... | ... | ... | one-way ⚠️ |

**สำหรับ UI/design task** — ใช้ **design-first prompting template** ( MengTo/Skills pattern):
```
goal      →  อะไรคือ outcome? (เช่น "hero 3D ที่ดู premium")
format    →  เอาท์พุตแบบไหน? (HTML / React / Vue / แค่ code snippet)
layout    →  structure: hero / grid / sticky / pinned / parallax
type      →  font + scale: serif/sans, display/body, weight
color     →  palette: base/accent/neutral + mood (dark/light/glass)
constraints → hard limits: a11y AA, perf budget, no external deps, mobile-first
```
แล้ว generate **variants ≥ 2** (ไม่ใช่ reroll ตัวเดิม) — แต่ละ variant เปลี่ยน ≥ 2 มิติ (เช่น layout + color) เพื่อให้เปรียบเทียบได้จริง ดู `design-first-ui-prompting` skill เต็มรูปแบบ

### 5. Pre-mortem
- "ถ้าคำตอบนี้ผิด เพราะอะไร?"
- Edge cases + strongest counter-argument
- **Disproof first** — ลอง falsify hypothesis ก่อนยืนยัน

### 6. Right-size the answer
- Simple question → short answer (อย่า over-engineer)
- Complex → full table + recommendation + why + what would change recommendation
- Match effort to stakes

### 7. Prove (fable-method eval-driven)
- ระบุ **metric** + **test** ที่ยืนยันคำตอบ
- Run / test what can be run
- "Untested; expected to work because X" — ห้ามเรียก untested code ว่า "working"

## Match the task type

| Task type | ความยาวคำตอบ | เน้นพิเศษ |
|---|---|---|
| **Architecture/design** | ยาวสุด | options table → recommendation → why → what changes recommendation |
| **Implementation** | สั้น + increment | small verified steps; แต่ละ step: what done / how verified / next |
| **Analysis/research** | กลาง | sources with dates; separate data from interpretation |
| **Writing/documents** | กลาง | audience + purpose → draft → self-critique → 1 revision → deliver |
| **Debug** | สั้น | read error → reproduce → isolate → rank hypotheses → test cheapest first |

## Technical work rules

- **Code** — state assumptions เป็น comments; prefer boring verifiable solutions over clever ones
- **Data & migration** — idempotent + rollback notes + post-migration validation (row counts, checksums); two-phase: staging → validate → promote; **never load straight to production**
- **Security & privacy** — never echo/print credentials; exposed secret = P0 (flag + rotate)
- **Destructive/costly ops** — propose plan + wait approval ก่อน (DROP/DELETE/deploy/paid API)

## Rationalization table

| ข้ออ้าง | คำตอบโต้ |
|---|---|
| "งานง่าย ไม่ต้องคิด" | ถ้าง่ายจริง 7 ขั้นใช้เวลา < 30 วินาที — รันเลย |
| "user รอ ขอมัด" | wrong answer แก้นานกว่า think; one-line restate ก็พอเริ่ม |
| "เคยทำแบบนี้" | session-memory.md อาจมี approach เดิม — อ่านก่อน + confirm |
| "assume เอา" | assumptions = comments; verify ได้ verify ก่อน |

## Red flags (STOP signals)

ถ้าคิดประโยคเหล่านี้ → กลับไป step 1:
- "เริ่มเขียนไปก่อน เดี๋ยวค่อยคิด"
- "น่าจะใช่" (without disproof attempt)
- "user คงต้องการแบบนี้แหละ"
- "one approach พอ"

## Examples

**Bad (skip A-Think)**:
```
user: migrate ตารางผู้ป่วย 500k rows จาก MySQL เป็น Postgres
agent: [dump + restore ทันที]  →  corrupt PK + duplicate SSN
```

**Good (run A-Think)**:
```
1. Restate: ย้าย 500k rows โดย data integrity ไม่เสีย (ไม่ใช่แค่ move)
2. Done: row count match + checksum + spot check 10 records + zero PHI leak
3. Decompose: (a) schema (b) data extract (c) staging table (d) validate (e) promote
4. ≥2: A=pgloader (auto) vs B=CSV staging + COPY (manual) — B ดีกว่าเพราะ validate ได้
5. Pre-mortem: encoding ไทยเพี้ยน? PK format ต่าง? timestamp tz?
6. Right-size: medium — table + step plan
7. Prove: row count + CHECKSUM TABLE + spot check 3 records
```

## Origin

- **fable-method** (Sahir619/fable-method) — eval-driven loop: classify → define done → evidence → decide → act → verify → report
- **fable5-standards** (A-Wiki native, `agent-skills/engineering/fable5-standards/`) — stakeholder + right-size + hospital-specific
- Merge เข้าด้วยกันเพื่อกัน duplicate: fable5 ถูก deprecate หลัง A-Think สมบูรณ์ (registry: `migrated_to: a-think`)
