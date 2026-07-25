# Self-Audit Hook (Tier 2 #7)

> Stop hook ที่ใช้ A-Council เป็น gate. Auto-enforce Iron Law #3 (validate output).

## ทำงานยังไง

```
Stop event → self_audit.py hook fires
  → check_open_councils(bb_path) → หา council threads ที่มี findings
  → evaluate_ship_gate() → ถ้ามี critical → block=True
  → record_findings_to_ledger() → write type=failure entries
  → stderr: "⛔ BLOCK SHIP — N critical findings"
```

## Flow จริง (เมื่อใช้ร่วมกับ A-Loop Phase 2)

```
1. Agent ทำ task เสร็จ → /A-Council "review <task>"
2. personas (via subagent fan-out) โพสต์ findings ลง blackboard
3. Agent สั่ง ship (commit/push)
4. Stop hook self_audit.py ทำงาน:
   - ถ้า critical → ⛔ block + ledger failures
   - ถ้าไม่ → ✅ pass
```

## ทำไม hook ไม่เรียก personas เอง

- **Separation of concerns**: personas ทำ review (deep work) ≠ hook enforce gate (cheap)
- **Hook timeout**: hooks มี timeout 5s ตามค่าเริ่มต้น → เรียก personas ไม่ทัน
- **Manual control**: user/agent ตัดสินใจเองว่าเมื่อไหร่จะ council

## Manual trigger (กลาง session)

```python
from scripts.hooks.self_audit import evaluate_ship_gate, record_findings_to_ledger
gate = evaluate_ship_gate(".tmp/blackboard.jsonl")
if gate["block"]:
    print(f"⛔ {gate['critical_count']} critical — fix before ship")
else:
    print("✅ safe to ship")
```

## Severity → action mapping

| Severity | Hook action | Ledger |
|----------|-------------|--------|
| critical | ⛔ block + warn | type=failure |
| important | warn only | (skip) |
| minor | silent | (skip) |

## ข้อจำกัด

- Hook อ่าน council state ที่มีอยู่แล้วเท่านั้น — ถ้ายังไม่ได้เปิด council → pass
- ไม่ detect findings เอง — พึ่ง personas ที่ post ไว้ก่อน Stop
