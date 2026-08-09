---
type: concept
tags: [meta, coordination, multi-agent, handoff, project-ledger, agent-memory]
sources: []
created: 2026-08-09
updated: 2026-08-09
---

# Coordination Artifacts — เลือกไฟล์ไหนเก็บอะไร

## นิยาม

แนวคิดที่แยกความแตกต่างของ artifact 3 ชนิดที่ใช้ resume งานข้าม
session/agent: **project ledger** (เช่น `MIGRATION.md`) · **session
memory** (`session-memory.md`) · **handoff** (`handoff.md`). แต่ละอย่าง
มีจุดประสงค์, หน่วย, อายุการใช้งาน, และกฎเขียน/อ่านต่างกัน — สับสน
ว่าจะเขียนลงไฟล์ไหนคือสาเหตุหลักของข้อมูลหาย/ซ้ำซ้อน.

## ทำไมถึงสำคัญในงาน A-Wiki

A-Wiki เป็น multi-agent repo (Core Rule #11: claim-based coordination)
ที่มี artifact 3 ชนิดนี้อยู่แล้ว — `session-memory.md`, `handoff.md`,
`log.md`. การเลือกผิด = ข้อมูลหายเมื่อ compact, หรือซ้ำซ้อนเมื่อหลาย
agent เขียนที่เดียวกัน. Concept นี้ป้องกันการ "เอา MIGRATION.md
มาใส่ใน A-Wiki" (เพราะ A-Wiki = living system, MIGRATION = bounded
project — เป็นคนละ category).

## ตารางเปรียบเทียบ

| ด้าน | Project Ledger (`MIGRATION.md`) | Session Memory (`session-memory.md`) | Handoff (`handoff.md`) |
|---|---|---|---|
| **หน่วย** | หนึ่ง project (env-wastewater-webapp) | ทั้ง hub | หนึ่ง session |
| **อายุ** | ตลอดชีพโปรเจกต์ | ตลอดชีพผู้ใช้ | ครั้งเดียว (throwaway) |
| **git** | tracked (public) | drive-synced (private) | drive-synced + template tracked |
| **โครงสร้าง** | phase map + chunk claim table + close-notes (rigid) | rolling append + recall-augmented (flexible) | "Resume Here" + agent rec + check script |
| **สัญญาณ"เสร็จ"** | claim closed + queue ว่าง | ไม่มี — คือสมอง | มี next handoff มาแทน |
| **ผู้อ่าน** | "agent ใดก็ตามที่ clone มา" | ตัวเอง/agent หลักบนเครื่องนี้ | agent ถัดไป (อาจต่างรุ่น/เครื่อง) |
| **ตัวอย่าง** | env-wastewater-webapp `MIGRATION.md` | A-Wiki `wiki/context/session-memory.md` (158KB!) | A-Wiki `handoff.md` + `docs/handoff/*` |

## เกณฑ์เลือก (decision tree)

```
มีหน่วยงานที่ "จบ" ไหม?
├─ ใช่ → project ledger (สร้าง bounded ledger ใหม่)
│        เช่น migration 907 rows → MIGRATION.md
│             hexagonal refactor → decisions/backlogs/<id>-*.md
│
└─ ไม่ใช่ (เป็นงานต่อเนื่อง) →
   ├─ ต้องการ "สมอง" ระยะยาวที่ recall ได้ → session memory
   │   เช่น "ได้เรียนรู้ X", "ตัดสินใจ Y ด้วยเหตุผล Z"
   │
   └─ ต้องการบอก agent ถัดไปว่า "อ่านตรงนี้" → handoff
       เช่น "resume ที่ chunk DOCK-22", "failover ไป Sonnet 5"
```

## กรณีศึกษา: env-wastewater-webapp

โปรเจกต์นี้ใช้ทั้ง 3 artifact อย่างถูกต้อง:
- **`MIGRATION.md`** — bounded (907 rows + webapp), git-tracked, phase map
  P1→P5 + two-track chunk claims + close-notes. Resume entry point
  cross-agent.
- **`docs/handoff/2026-07-19-track-z-complete.md`** — narrative handoff
  ครั้งเดียว สำหรับ Fable5 review.
- ไม่มี session-memory ของตัวเอง เพราะ A-Wiki session-memory ครอบคลุม
  อยู่แล้ว (cross-repo recall).

สิ่งที่ไม่ควรทำ (pre-mortem):
- สร้าง `MIGRATION.md` ถาวรใน A-Wiki (living system — จะกลายเป็นไฟล์ผี
  ทุก phase "เสร็จ" และไม่มีใครอ่าน)
- เอา project status ใส่ session-memory (จะกินพื้นที่ + ไม่มี
  discoverability ข้าม agent ที่ clone มา)
- เขียน "TODO ถัดไป" ใน handoff โดยไม่เช็ค claim table ของ ledger
  (จะชนกับ agent อื่น)

## รูปแบบที่แนะนำ: bounded ledger สำหรับ infra ใหญ่

เมื่อ A-Wiki มีงาน infra ใหญ่ (เช่น hexagonal refactor ADR-0012,
swarm consolidation) ให้ใช้รูปแบบ `decisions/backlogs/<NNNN>-<slug>-backlog.md`
(มีอยู่แล้ว — `0012-hexagonal-refactor-backlog.md`) ด้วย skeleton:

```markdown
# <NNNN> <slug> — chunk ledger

## Phase map
- Phase 1 (xxx): Status: COMPLETE — close-note
- Phase 2 (yyy): Status: IN-PROGRESS — open items

## In-progress claims (current session)
| Chunk | Agent | Claimed | Scope (files) |

## Close-notes (reverse-chronological)
> **<ID> <agent> done <date>** — summary + verify + commit

## Resume next-session
อ่าน "Phase map" + close-note ล่าสุด → ทำ chunk ถัดไป
```

วางใน `decisions/backlogs/` (ไม่สร้าง structure ใหม่). เมื่อ infra
เสร็จ → mark "ALL PHASES COMPLETE" + เก็บไว้ (decision history).

## Cross-references

- A-Wiki `AGENTS.md` Core Rule #8 (cross-agent plan handoff) + Iron Law
  #11 (claim before touching shared surface)
- `docs/protocols/cross-agent-plan-handoff.md` (session-level) +
  `docs/protocols/cross-agent-work-orders.md` (repo-level)
- env-wastewater-webapp `MIGRATION.md` (worked example)
- `wiki/context/session-memory.md` (the brain) + `handoff.md.example`
  (schema)
- `scripts/hooks/check_agent_claim.py` (claim gate enforcement)
