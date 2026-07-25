# Phase 1: Decompose (goal → tasks)

> โหลดเฉพาะตอนเริ่ม `/A-Loop "<objective>"`. ไม่ auto-load ทุก session.

## 🧠 Model tier: Opus 5 (tier 4c)

Phase 1 คือจุดที่ใช้ **Opus 5 คุ้มที่สุด** — decompose กำหนด task ทั้งหมด
ถ้าผิดที่นี่ = เสียเวลาทั้ง loop. ทำ 1 ครั้ง → ลงทุน deep reasoning ที่นี่.

Override เป็น free: `A_LOOP_TIER_PHASE1=1` (ใช้เฉพาะตอนโครงการเล็ก/trivial)

## ขั้นตอน

### 1. รับ objective จาก user
```
/A-Loop "ship feature X with tests + docs + ADR"
```

### 2. รัน a-think 7-step (โดยเฉพาะ step 3 Decompose)
- Restate: objective จริงๆ คืออะไร? (ไม่ใช่แค่ "ทำ X" แต่ "ทำ X โดย Y")
- Done-criteria: success หน้าตาเป็นยังไง? verify ยังไง?
- Decompose: แตกเป็น 3-7 subtasks **เล็กพอที่ verify ได้ทีละตัว**

### 3. สร้าง goal + subtasks บน goal_store
```python
from scripts.lib.goal_store import GoalStore
store = GoalStore(".tmp/task-board.json")
goal_id = store.create_goal(objective="ship feature X with tests + docs + ADR")
store.add_subtask(goal_id, goal="write failing test for X", files=["tests/test_x.py"])
store.add_subtask(goal_id, goal="implement X", files=["scripts/x.py"])
store.add_subtask(goal_id, goal="write ADR-NNN for X decision", files=["decisions/adr-nnn.md"])
store.add_subtask(goal_id, goal="update wiki entity for X", files=["wiki/entities/x.md"])
```

### 4. บันทึก decision ใน ledger
```python
memory_remember(type="decision",
    summary=f"A-Loop started: {objective} decomposed into N tasks",
    tags=["a-loop", "goal"])
```

## เกณฑ์ decomposition ที่ดี

- แต่ละ task **verify ได้ด้วยตัวมันเอง** (test/command/visual check)
- ขนาดพอดี — ไม่ใหญ่เกิน (context overflow) ไม่เล็กเกิน (overhead claim/release)
- **Dependency** ระบุใน `notes` ถ้า task B ต้องรอ task A

## ตัวอย่าง

**Bad** (1 task ใหญ่):
```
T1: "build feature X"  ← verify ไม่ได้ว่าจบตรงไหน
```

**Good** (4 tasks เล็ก):
```
T1: "write failing test for X.query()" — verify: pytest test_x.py RED
T2: "implement X.query()"              — verify: pytest test_x.py GREEN
T3: "write ADR for X design choice"    — verify: file exists + reviews OK
T4: "update wiki entity X"             — verify: gen-index --check passes
```

## หลัง Phase 1 เสร็จ

→ ไป Phase 2 (Execute): `references/phase-execute.md`
→ หรือ compact + resume ใน session ใหม่: `goal_store.next_todo(goal_id)`
