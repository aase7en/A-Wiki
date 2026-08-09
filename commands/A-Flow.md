# /A-Flow — Master 7-stage dev pipeline

Maps to: `skills/awiki/a-flow/SKILL.md`

## When to use
- task non-trivial (≥3 files, design decision, multi-step)
- ขอ professional workflow / dev pipeline
- stake สูง (security, money, deploy, migration)

## Flow (7 stages, hook-enforced)
```
ASK → DESIGN → PLAN → IMPLEMENT → REVIEW → DEBUG → TEST
```

ห้ามข้าม stage — hook `check_a_flow_discipline` block Edit/Write ก่อนจบ PLAN.

เต็ม ๆ: `skills/awiki/a-flow/SKILL.md` · state: `.tmp/a-flow.json`
