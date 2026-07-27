# A-Flow Stage: IMPLEMENT

> โหลดเมื่อ: `state.stage == "IMPLEMENT"`
>
> Goal: ลงมือทำ task ทีละตัว — TDD + small verified steps (Iron Law #1)

## Loop

```
for each task in state.tasks:
  1. claim from task_board
  2. write failing test first (TDD)
  3. minimal code ให้ test ผ่าน
  4. refactor (optional)
  5. verify locally (test + lint)
  6. mark done in task_board
  7. ไป task ถัดไป
```

## Skills

- `incremental-implementation` — small verified steps
- `test-driven-development` (Matt Pocock) — Red → Green → Refactor
- `doubt-driven-development` — สงสัยตรงไหน เขียน test ก่อน
- `source-driven-development` — verify กับ docs ก่อน code

## Discipline

- ❌ ห้าม implement ไฟล์ที่ไม่อยู่ใน `allowed_files[]` (hook บล็อก)
- ❌ ห้ามข้าม TDD (Iron Law #1) — ยกเว้น "exploration" ที่ไม่ ship
- ✅ แต่ละ step: what done / how verified / next
- ✅ Commit ทีละ task (atomic) → `chunk(implement-T<n>): <goal>`

## Failure

ถ้า implement ไม่ผ่าน:
- อย่า force — back out + debug
- `a_flow_state.advance("DEBUG")` (กลางใจ)
- DEBUG จบ → กลับ IMPLEMENT

## Outputs

- Working code (all tasks done)
- Tests passing
- พร้อม advance REVIEW
