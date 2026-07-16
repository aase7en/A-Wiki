---
name: a-plan
description: "วางแผน + ออกแบบ — UX/UI, database schema, system architect engineer. Chain: A-Think → grill-with-docs (บังคับถาม ≥3 Qs) → spec-driven-development → design tool → plan-orchestrate. Trigger: 'ออกแบบ', 'วางแผน', 'design', 'architecture', 'database schema', 'ux/ui'. Iron Law: ห้าม implement ก่อน grill เสร็จ."
version: 1.0.0
author: A-Wiki
domain: [engineering, ux-ui, design]
lifecycle_phase: define
category: pipeline
agents: [all]
invocation: both
---

# A-Plan — วางแผน / ออกแบบ UX-UI-DB-Architecture

Aggregator สำหรับงานวางแผนและออกแบบ — รวม canonical skills ที่ A-Wiki มีอยู่เป็น chain เดียว บังคับ grill ก่อน propose

## เมื่อไหร่ใช้

✅ ใช้:
- ออกแบบ UX/UI หน้าเว็บ, app
- วาง database schema
- วาง system architecture / engineer
- เลือกระหว่าง competing design approaches
- วางแผน refactor >3 ไฟล์

❌ ข้าม:
- Implement ตรง (ใช้ incremental-implementation)
- Bug fix (ใช้ A-Debug)
- แก้ typo / เพิ่ม 1 field

## Iron Law

> **NO IMPLEMENTATION WITHOUT GRILL FIRST**

ห้าม jump เข้า Edit/Write ทันที — ต้องจบ 5 stage ข้างล่างก่อน (ยกเว้น user บอก "เริ่มเลย" อย่างชัดเจน)

## Chain (5 stages — เรียงบังคับ)

```
┌─────────┐    ┌────────────────┐    ┌──────────────────────┐    ┌──────────────┐    ┌──────────────────┐
│ A-Think │───▶│ grill-with-docs│───▶│ spec-driven-         │───▶│ design tool  │───▶│ plan-orchestrate │
│ (7-step)│    │ (≥3 Qs + ADR)  │    │ development (spec)   │    │ (UX/DB/Arch) │    │ (tasks + sub)    │
└─────────┘    └────────────────┘    └──────────────────────┘    └──────────────┘    └──────────────────┘
```

### Stage 1: `a-think` (always)
รัน 7-step reasoning loop ก่อน — โดยเฉพาะ step 1 (Restate) + step 2 (Done-criteria)

### Stage 2: `grill-with-docs` (MANDATORY — บังคับ)
- ถาม user **ทีละข้อ ไม่พร้อมกัน** ≥3 questions:
  1. ขอบเขต: ครอบคลุมแค่ไหน? domain ไหน?
  2. ข้อจำกัด: token/time budget? mobile? legacy compat?
  3. success criteria: ทำเสร็จแล้วดูยังไงว่าใช้ได้
- **สร้าง ADR** (Architecture Decision Record) + **glossary** ควบคู่ไปด้วย (สิ่งที่ grill-with-docs ทำให้)
- ห้าม assume — ถ้า user ไม่ตอบ = ถามซ้ำ ไม่ guess

### Stage 3: `spec-driven-development`
จาก grill answers → เขียน spec ที่ verify ได้:
- Functional requirements (testable)
- Non-functional (perf, security, a11y)
- Acceptance criteria

### Stage 4: เลือก design tool ตาม domain

| Domain | Canonical skill | Output |
|---|---|---|
| **UX/UI** | `frontend-design` + `frontend-slides` | mockup HTML + 34 templates |
| **Database** | `domain-modeling` | ER diagram + entity list |
| **Architecture** | `codebase-design` + `api-design` | component diagram + API contract |
| **Mixed** | ผสมตามโจทย์ | — |

### Stage 5: `plan-orchestrate`
แตก spec เป็น tasks + subagent allocation:
- Task list (ordered, dependency-marked)
- แต่ละ task → เลือก skill/subagent ที่จะ execute
- Estimate effort + risk

## Handoff contract

แต่ละ stage ส่ง output ไป stage ถัดไปผ่าน context ของ primary agent:

### Stage 1 → 2
- **Input**: user's raw request
- **Output**: restated problem + done-criteria + constraint list

### Stage 2 → 3
- **Input**: Stage 1 output
- **Output**:
  ```yaml
  clarifications:
    - question: "..."
      answer: "..."
  adr: "path/to/adr-001-design-choice.md"
  glossary: ["term1", "term2"]
  ```

### Stage 3 → 4
- **Input**: clarifications + ADR
- **Output**: spec document (functional/non-functional/acceptance)

### Stage 4 → 5
- **Input**: spec
- **Output**: design artifact (diagram/mockup/contract)

### Stage 5 → execution
- **Input**: design artifact
- **Output**: task list พร้อม skill mapping

## Rationalization table

| ข้ออ้าง | คำตอบโต้ |
|---|---|
| "user คงต้องการแบบนี้" | รอไม่ได้ — ถาม 1 question ใช้เวลา 30 วิ |
| "scope เล็ก" | ถ้าเล็กจริง user ตอบ grill ทันที 1 ประโยค |
| "เคยทำแบบนี้" | session-memory.md อาจมี approach เดิม — อ่านก่อน + confirm |
| "ข้าม grill ได้มั้ย" | ได้ ถ้า user บอกชัด "เริ่มเลยไม่ต้องถาม" |

## Examples

**Bad (skip grill)**:
```
user: ทำ dashboard พลังงาน รพ.
agent: [เริ่ม React + chart.js ทันที]  → ผิด scope 3 รอบ เสีย 3 ชม
```

**Good (follow chain)**:
```
user: ทำ dashboard พลังงาน รพ.
A-Think: restated = dashboard แสดง kWh รายวัน/เดือน + alarm threshold
grill-with-docs (3 Qs):
  Q1: data source? → IoT meter Modbus / spreadsheet manual?
  Q2: ใครดู? → ผอ. / เจ้าหน้าที่ ENV / public?
  Q3: refresh rate? → real-time / daily?
→ ADR-001, glossary
spec: FR1 แสดง kWh/day, FR2 alarm > threshold, NFR1 load <2s, AC1 ผอ. ดูได้บน iPad
design: frontend-design → wireframe + Tailwind table + Chart.js
plan-orchestrate: T1 schema, T2 ingest, T3 dashboard, T4 alarm (4 tasks, 2 subagents)
```

## Invocation

```
/A-Plan [task description]
```

Skill นี้จะ run chain 5 stages อัตโนมัติ — หยุดถาม user เฉพาะ stage 2 (grill) + ตอนเลือก design approach
