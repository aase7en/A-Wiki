---
name: a-loop
description: "Autonomous goal loop: decompose → execute → verify → distill → improve. A- suite aggregator that drives a goal to completion across sessions."
version: 1.0.0
domain: [engineering]
lifecycle_phase: meta
category: pipeline
agents: [all]
status: canonical
invocation: manual
invocation_hint: "/A-Loop \"<objective>\""
---

# A-Loop — Autonomous Goal Loop

> Foundation skill ของ Phase 2 — ทำให้สมองทำงานได้เองจนจบ + เรียนรู้ + พัฒนาตัวเอง.
> รวม Goal Loop + Idea Distiller + Failure→Skill เป็น loop เดียว (ไม่แยก 3 skills — กัน context ยาว/หลุด).

## เมื่อไหร์ใช้

✅ ใช้:
- User สั่ง objective ที่ต้องทำหลายขั้น + verify จนจบ
- งานที่ต้อง restart ข้าม session ได้ (checkpoint ใน task_board)
- อยากให้สมองเรียนรู้จาก failure/outcome อัตโนมัติ

❌ ข้าม:
- งานเดียวจบ (ใช้ skill ตรงๆ เช่น `/build`, `/test`)
- Bug fix (ใช้ `/A-Debug`)
- แค่วางแผน (ใช้ `/A-Plan`)

## 4 Phases (วงจร loop)

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ 1. Decompose │────▶│ 2. Execute    │────▶│ 3. Distill   │────▶│ 4. Improve   │
│ goal→tasks   │     │ claim→verify  │     │ outcomes→    │     │ failure≥3 →  │
│ (goal_store) │     │ (Hermes loop) │     │ ideas        │     │ propose skill│
└─────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                            ▲                       │                   │
                            └─── retry ◀────────────┘                   │
                            (debug-mantra if verify fail)               │
                                                                        ▼
                                                            ┌────────────────────┐
                                                            │ user confirms     │
                                                            │ → new-skill.py     │
                                                            └────────────────────┘
```

**อ่านรายละเอียดแต่ละ phase ใน `references/`** (progressive disclosure — โหลดเฉพาะที่ใช้).

## วิธีใช้

### Phase 1: Decompose
```
/A-Loop "ship feature X with tests + docs"
```
→ a-think decompose → `goal_store.create_goal()` + `add_subtask()` หลายตัว
→ ดูรายละเอียด: `references/phase-decompose.md`

### Phase 2: Execute (เรียกซ้ำจน done)
```
next = goal_store.next_todo(goal_id)
task_board.claim(next, claimant="me")
# รัน Hermes phase (define→plan→build→verify→review→ship)
# fail → debug-mantra + tdd → retry (cap 3)
# pass → A-Loop v2 completion gate (scripts/lib/a_loop_review.py):
#   open_review_for_task → review-bus cycle → task_gate
#   gate READY (verdict PASS + retest ที่ head ปัจจุบัน + CI เขียว + ไม่มี blocker)
#   เท่านั้นถึง task_update(status="done") — fix ที่ head ใหม่ = approval เก่าเพิกถอน
#   วนกลับหา next_todo
```
→ ดูรายละเอียด: `references/phase-execute.md`

### Phase 3: Distill (Stop hook อัตโนมัติ)
- Stop → scan `memory_ledger` หา `type=failure`/`type=outcome` patterns
- เจอ pattern น่าสนใจ → `memory_remember(type="idea")`
→ ดูรายละเอียด: `references/phase-distill.md`

### Phase 4: Improve (trigger เมื่อ failure ≥3)
- นับ failure pattern ซ้ำ → `skill-scout` (เช็คซ้ำ) → draft → **propose ให้ user**
- user ยืนยัน → `new-skill.py --apply`
→ ดูรายละเอียด: `references/phase-skill.md`

## Handoff contract (cross-session safe)

ทุก phase เขียน state ลง disk (ไม่ถือใน context):
- Goal + tasks → `.tmp/task-board.json` (survives compact)
- Decisions/lessons → `.tmp/memory-ledger.jsonl`
- Resume: `goal_store.get_goal()` + `next_todo()` → รู้ทันทีว่าอยู่ phase ไหน

```yaml
phase: <1|2|3|4>
goal_id: "G..."
current_task: "T..." | null
progress: {total: 5, done: 2, percent_done: 40}
next: "<phase + task_id + why>"
```

## Context discipline (กันหลุด/ลืม)

- **SKILL.md นี้ ~150 บรรทัด** — โหลดเบา ไม่กิน token
- **references/ แยก** — โหลดเฉพาะ phase ที่ทำอยู่ (progressive disclosure)
- **Checkpoint ใน task_board** — compact แล้ว resume จาก status ได้ ไม่ต้องจำ
- **invocation: manual** — ไม่ auto-load ทุก session (ประหยัด token)

## Model tier policy (cost-first — ใช้ Opus 5 คุ้มที่สุด)

อ้างอิง: `wiki/context/a-loop-model-policy.conf`

| Phase | Tier | เหตุผล |
|-------|------|--------|
| **1. Decompose** | **Opus 5** (4c) | decisions สำคัญมาก ทำ 1 ครั้ง → คุ้มที่สุด |
| 2. Execute | free (1) | routine + มี tdd ตรวจ → ไม่ต้องเก่ง |
| 3. Distill | free (1) | deterministic counting → ไม่ต้องคิด |
| **4. Improve** | **Opus 5** (4c) | ออกแบบ skill = durable capability → คุ้ม |

Override: `A_LOOP_TIER_PHASE1=1` (force free), `A_LOOP_TIER_PHASE4=1`
Cost guard: ถ้า Opus5 calls > 4 ต่อ run → เตือน + suggest tier-down

## สิ่งที่ reuse (ไม่ duplicate)

| สิ่งที่มี | ใช้ตรงไหน |
|---------|---------|
| `goal_store.py` (C1) | Phase 1+2 — goal lifecycle |
| `task_board` (NS C5) | atomic claim/release |
| `memory_ledger` (NS C2) | Phase 3 — distill source |
| `new-skill.py` | Phase 4 — register skill |
| Hermes lifecycle | Phase 2 — sub-loop per task |
| `a-think` / `debug-mantra` / `tdd` | Phase 2 — per-task reasoning |

## Files

| File | Purpose |
|---|---|
| `SKILL.md` | This thin router |
| `references/phase-decompose.md` | Phase 1 detail |
| `references/phase-execute.md` | Phase 2 detail |
| `references/phase-distill.md` | Phase 3 detail |
| `references/phase-skill.md` | Phase 4 detail |
| `scripts/lib/goal_store.py` | Goal lifecycle wrapper |
| `scripts/hooks/a_loop_distill.py` | Phase 3 Stop hook |
