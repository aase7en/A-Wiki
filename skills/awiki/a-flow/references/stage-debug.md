# A-Flow Stage: DEBUG

> โหลดเมื่อ: `state.stage == "DEBUG"` หรือ review found critical
>
> Goal: หา root cause ก่อน fix (Iron Law #2) — ห้าม patch สุ่ม

## Chain (delegate ไป `a-debug`)

```
a-think (step 1: restate the bug)
   ↓
debug-mantra (4-step: reproduce → isolate → rank hypotheses → test cheapest)
   ↓
root-cause-first (5-why, แตกใหญ่จนเจอ root)
   ↓
tdd (write failing test ที่ capture bug)
   ↓
fix (minimal change ให้ test ผ่าน)
   ↓
verify-before-done (test ผ่าน + ไม่ break อย่างอื่น)
   ↓
scrutinize (review fix ว่าไม่ทำใหม่ปัญหาอื่น)
```

## Discipline

- ❌ ห้าม `console.log` spam แล้วเดา
- ❌ ห้าม "ลอง revert ดู" โดยไม่มี hypothesis
- ✅ Reproduce ก่อนเสมอ (deterministic test case)
- ✅ Root cause เป็น sentence: "Bug เกิดเพราะ X, ผลข้างเคียง Y"
- ✅ Failing test ก่อน fix (Iron Law #1 ในบริบท debug)

## Subagent fan-out (bug ซับซ้อน)

ใช้ `delegate-subagent` → `council`:
- code-reviewer: "รหัสไหนอาจ trigger bug?"
- test-engineer: "edge case อะไรที่ไม่ได้ test?"

## Tools

- `agent-introspection-debugging` — hook state introspection
- `debug-mantra` — canonical 4-step root cause discipline (Iron Law #2)
- `diagnosing-commands` / `diagnosing-hooks` / `diagnosing-mcp` (ZCode plugin)

## Outputs

- Root cause statement in `state.notes[]`
- Failing test ที่ผ่าน (capture bug)
- Fix commit (atomic: `fix(<scope>): <root cause summary>`)
- Advance: กลับ `REVIEW` หรือ `TEST` แล้วแต่กรณี
