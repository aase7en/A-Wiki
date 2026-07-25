# Phase 4: Improve (failure ≥3 → propose skill)

> Trigger เมื่อ Phase 3 distill แล้ว user เห็น idea + อนุมัติ. ไม่ auto-register.

## 🧠 Model tier: Opus 5 (tier 4c)

Phase 4 คือจุดที่ใช้ **Opus 5 คุ้มที่สุด** — ออกแบบ skill ใหม่ = เพิ่ม
durable capability ให้สมอง. ทำน้อยครั้ง + อยู่กับเรานาน → deep reasoning.

Override เป็น free: `A_LOOP_TIER_PHASE4=1` (ใช้เฉพาะตอน skill เล็ก/simple)

## ขั้นตอน

### 1. อ่าน pattern จาก ledger (Phase 3 เขียนไว้)
```python
from scripts.hooks.a_loop_distill import count_failure_patterns
patterns = count_failure_patterns(".tmp/memory-ledger.jsonl", min_count=3)
# patterns = [{tag, count, sample_summaries}]
```

### 2. สร้าง proposal (draft — ยังไม่ register)
```python
from scripts.lib.a_loop_skill import propose_skill_for_pattern
proposal = propose_skill_for_pattern(
    tag=patterns[0]["tag"],
    failure_count=patterns[0]["count"],
    sample_summaries=patterns[0]["sample_summaries"],
)
# proposal = {name: "guard-<tag>", description, rationale, ...}
```

### 3. แสดงให้ user พิจารณา
```
💡 A-Loop detected repeated failure: 'permission' (3x)
   Proposed skill: guard-permission
   Rationale: <evidence>
   Apply? (y/n)
```

### 4. เมื่อ user ยืนยัน → register (Iron Law #9)
```python
from scripts.lib.a_loop_skill import apply_proposal
ok = apply_proposal(proposal)
# → shells out to: new-skill.py guard-permission --domain engineering --phase verify --apply
# → registry-first ordering (check_skill_registry.py enforces)
# → regen-skill-surfaces.py auto-runs
```

## ทำไมไม่ auto-register

- **brain-improvement-gate**: ทุกการเปลี่ยน brain capability ต้องผ่าน review
- **กัน spam skills**: threshold ต่ำ → สร้างเยอะ → registry บวม
- **User authority**: user เป็น Senior Critic (Iron Law #3) — validate ทุก output

## Name convention

- Prefix `guard-` สำหรับ skill ที่ป้องกัน failure class
- kebab-case (registry validate)
- ตัวอย่าง: `guard-permission-denied`, `guard-timeout`, `guard-import-error`

## → หลัง Phase 4

กลับไป Phase 1 ของ goal ใหม่ หรือ goal เดิมที่ยังไม่จบ.
Loop วนต่อจนกว่าจะไม่มี goal todo.
