# Phase 2: Execute (claim → Hermes loop → verify per task)

> โหลดเฉพาะตอนทำ task. ไม่ auto-load ตอน decompose หรือ distill.

## Loop หลัก

```
while next = goal_store.next_todo(goal_id):
    task_board.claim(next.id, claimant="me")
    result = run_hermes_phases(next)   # see below
    if result == "pass":
        task_board.update(next.id, status="done")
    elif result == "fail" and retries < 3:
        debug_mantra(next)   # root cause + tdd
        retries += 1
    else:
        task_board.update(next.id, status="blocked", note="exhausted 3 retries")
        break
# loop exits when next_todo returns None → goal complete
goal_store.update_goal(goal_id, status="done")
```

## Hermes phases (sub-loop per task)

แต่ละ task วิ่งผ่าน 6 phases ของ Hermes lifecycle (orchestration contract ใน `scripts/hermes/lifecycle-config.json`):

| Phase | Skill | ทำอะไร | Verify |
|-------|-------|--------|--------|
| **define** | `spec-driven-development` | ชัดเจนว่า task นี้ต้องการอะไร | spec written |
| **plan** | `planning-and-task-breakdown` | แผนการทำ (ถ้า task เล็กอาจข้าม) | plan noted |
| **build** | `incremental-implementation` + `tdd` | เขียน failing test ก่อน → implement | test GREEN |
| **verify** | `browser-testing-with-devtools` / `verify-before-done` | ทดสอบจริง | test + manual |
| **review** | `scrutinize` + personas | ตรวจทาน outsider view | review notes |
| **ship** | `git-workflow-and-versioning` | commit (Iron Law: commit main only) | commit hash |

**Shortcut blocklist** (Hermes บังคับ — อย่าข้าม):
- `implement_without_spec` → ห้ามเขียนโค้ดโดยไม่มี spec/test ก่อน
- `skip_test_before_implementation` → Iron Law #1
- `skip_review_before_ship` → ต้อง review ก่อน commit
- `dont_document_decision` → ADR สำหรับ decision สำคัญ

## Retry logic (เมื่อ verify fail)

```
fail count 1 → debug-mantra 4 mantras:
  1. Reproducibility: สร้าง repro ที่ deterministic
  2. Know fail path: stack trace → source trace
  3. Question hypothesis: 3-5 ranked, disproof first
  4. Every run = breadcrumb: ledger ทุก experiment
→ root-cause-first → tdd (failing test) → fix → re-verify

fail count 2 → ลอกกลับไป debug-mantra อีกรอบ + ขยาย hypothesis

fail count 3 → task_board.update(status="blocked", note="3 retries exhausted")
              → memory_remember(type="failure", ...) เพื่อ Phase 3 distill
              → หยุด loop + แจ้ง user
```

## Resume หลัง compact / session switch

```python
# session ใหม่ — ไม่ต้องจำอะไร อ่านจาก disk
store = GoalStore(".tmp/task-board.json")
goals = store.list_goals()
for g in goals:
    if g["status"] != "done":
        view = store.get_goal(g["id"])
        prog = store.goal_progress(g["id"])
        next_task = store.next_todo(g["id"])
        print(f"Goal {g['id']}: {prog['percent_done']}% done, next: {next_task}")
```

## Iron Laws ที่ถือใน Phase 2

- **#1**: failing test ก่อน implement (tdd)
- **#2**: root cause ก่อน fix (debug-mantra)
- **#3**: validate ทุก output (scrutinize)
- **#6**: commit main only (Iron Law)

## หลัง Phase 2 เสร็จ (goal done)

→ Phase 3 ทำงานอัตโนมัติที่ Stop hook (distill)
→ Phase 4 trigger ถ้ามี failure pattern ซ้ำ ≥3
