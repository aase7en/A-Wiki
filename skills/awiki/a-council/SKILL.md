---
name: a-council
description: "Persistent multi-persona council: code-reviewer/test-engineer/security-auditor post findings to a blackboard thread that survives sessions. Auto-aggregates severity, blocks ship if critical."
version: 1.0.0
domain: [engineering]
lifecycle_phase: review
category: pipeline
agents: [all]
status: canonical
invocation: manual
invocation_hint: "/A-Council \"<topic>\""
---

# A-Council — Persistent Multi-Persona Council

> Tier 2 #8. Council (multi-perspective review) แบบถาวร — thread คงอยู่ข้าม session,
> dashboard แสดงได้, resume ได้. พื้นฐานของ self-audit (Tier 2 #7).

## เมื่อไหร่ใช้

✅ ใช้:
- Review งานก่อน ship (Iron Law #3 — validate ทุก output)
- ตัดสินใจ architecture (ต้องการหลายมุมมอง)
- Security review (security-auditor + code-reviewer)
- Production-audit (ทุก persona พร้อมกัน)

❌ ข้าม:
- Bug fix เล็ก (ใช้ /A-Debug)
- แค่ lint/format
- งานเดียวจบ

## Personas (4)

| Persona | มุมมอง | File |
|---------|--------|------|
| `code-reviewer` | senior staff engineer — logic/architecture | `agents/code-reviewer.md` |
| `test-engineer` | QA — edge cases / regression | `agents/test-engineer.md` |
| `security-auditor` | security — exploit surface | `agents/security-auditor.md` |
| `web-performance-auditor` | perf — load/budget | `agents/web-performance-auditor.md` |

กฎ: personas ไม่เรียก personas อื่น (Hermes lifecycle_config rule).

## วิธีใช้

```
/A-Council "review PR #42 for security implications"
```

```python
from scripts.lib.council_persistent import Council
council = Council(".tmp/blackboard.jsonl")
tid = council.open(topic="review PR #42", participants=["code-reviewer","security-auditor"])
# แต่ละ persona (via subagent fan-out หรือ manual):
council.post_perspective(thread_id=tid, persona="security-auditor",
                          finding="sql injection in query()", severity="critical")
council.post_perspective(thread_id=tid, persona="code-reviewer",
                          finding="naming inconsistent", severity="minor")
# สรุป:
summary = council.summarize(tid)
# → {critical: 1, important: 0, minor: 1, total_findings: 2}
# บล็อก ship ถ้า critical:
if council.has_critical(tid):
    print("⛔ BLOCK — critical findings, do not ship")
```

## Severity levels

| Level | Meaning | Action |
|-------|---------|--------|
| **critical** | security hole / data loss / crash | ⛔ block ship |
| **important** | bug likely / perf regression | ⚠️ fix before ship |
| **minor** | style / naming / nit | ✅ ship ok, note for later |

## Persistence (cross-session)

- Thread อยู่ใน `.tmp/blackboard.jsonl` → survives compact + restart
- Council ใหม่อ่าน thread เก่าได้ → resume discussion ข้าม session
- Dashboard `/api/bb` endpoint แสดง council threads

## Self-audit hook (Tier 2 #7)

Stop hook ที่ใช้ A-Council: เปิด council → run personas → ถ้า critical
→ บล็อก ship + เขียน findings เป็น ledger. ดู `references/self-audit.md`.

## Reuse (ไม่ duplicate)

| สิ่งที่มี | ใช้ตรงไหน |
|---------|---------|
| `blackboard.jsonl` (NS C4) | storage layer |
| `agents/*.md` personas | บอทที่จะ respond |
| Hermes `parallel_fan_out` | orchestration |

## Files

| File | Purpose |
|---|---|
| `SKILL.md` | This skill |
| `references/self-audit.md` | Tier 2 #7 self-audit hook detail |
| `scripts/lib/council_persistent.py` | Council library |
| `scripts/hooks/self_audit.py` | Stop hook (Tier 2 #7) |
