# A-Flow Stage: PLAN

> โหลดเมื่อ: `state.stage == "PLAN"`
>
> Goal: แตก spec เป็น task list ที่ verify ได้ทีละตัว + เลือก executor แต่ละ task

## 1. Spec finalization

จาก DESIGN output → เขียน spec document:
- Functional requirements (testable ทีละข้อ)
- Non-functional (perf, security, a11y)
- Acceptance criteria (แต่ละข้อ measure ได้)

## 2. Task breakdown

แตกเป็น tasks ที่:
- **Cohesive** (1 task = 1 logical change)
- **Independently testable** (แต่ละ task มี test ของตัวเอง)
- **Small enough** (~30 min - 2 hr each)
- **Dependency-marked** (T2 deps T1?)

ไฟล์ที่จะแก้รวม task → เพิ่มใน `state.allowed_files[]` (hook enforce)

## 3. Subagent allocation

แต่ละ task → เลือก executor:

| Task type | Executor |
|---|---|
| Mechanical codegen | Cheap-capable (Sonnet/Haiku) |
| Architecture decision | Primary (Opus/GPT-5) |
| Test writing | Cheap-capable |
| Code review | Primary + persona fan-out |
| Bug investigation | Primary (root cause) |

ใช้ `delegate-subagent` / `council` skills สำหรับ fan-out

## 4. Estimate

- Effort: แต่ละ task hours/days
- Risk: high/medium/low (one-way door = high)
- Cost budget: token estimate

## Outputs

- Task list (ordered) → `.tmp/task-board.json`
- `state.allowed_files[]` อัปเดต
- `state.notes[]`: "PLAN done — T1..Tn queued"
- Advance: `a_flow_state.advance("IMPLEMENT")`

## Hook unblock

หลัง PLAN จบ → hook อนุญาต Edit/Write ใน `allowed_files[]` เท่านั้น
