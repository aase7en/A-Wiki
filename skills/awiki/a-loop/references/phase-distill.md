# Phase 3: Distill (outcomes/failures → ideas)

> Stop hook อัตโนมัติ. ไม่ต้องเรียกเอง.

## ทำงานยังไง

```
Stop event → a_loop_distill.py hook fires
  → scan memory_ledger หา type=failure entries
  → group by tag → count
  → ถ้า pattern ซ้ำ ≥3 → propose type=idea entry
  → SessionStart แสดง ideas (มีอยู่แล้วใน replay_for_session_start)
```

## ตัวอย่าง

```
session A: failure "permission denied" tags=[permission]
session B: failure "permission denied on /tmp" tags=[permission]
session C: failure "permission denied writing config" tags=[permission]
→ Stop hook: pattern 'permission' count=3 ≥ min_count
→ propose idea: "Repeated failure 'permission' (3x). Consider: guard/prevent/test."
→ SessionStart แสดง idea → user/agent เห็น → อาจสร้าง skill (Phase 4)
```

## Idempotency

ถ้ารันสองครั้ง → ไม่ propose ซ้ำ (tag marker `distill:<tag>` ตรวจใน existing ideas).

## Manual trigger (ถ้าอยาก distill กลาง session)

```python
from scripts.hooks.a_loop_distill import propose_ideas
n = propose_ideas(".tmp/memory-ledger.jsonl", min_count=3)
print(f"proposed {n} ideas")
```

## → Phase 4 (Improve)

ถ้า failure pattern ซ้ำมากๆ (≥3) + user เห็น idea → อาจอนุมัติให้สร้าง skill.
Phase 4 ทำงานเมื่อ user ยืนยัน (ไม่ auto-register) — ดู `references/phase-skill.md`.
