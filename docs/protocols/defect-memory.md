# Defect Memory — บันไดป้องกันการเกิดซ้ำ (Executable > Prose)

> Protocol กำกับ: ทุก defect ที่ "material" (ทำให้ CI แดง / ทำลายงานผู้ใช้ / กวนระบบ > 30 นาที) ต้องถูกแปลงเป็น **กลไกกันซ้ำที่แข็งแรงที่สุดที่ทำได้** ไม่ใช่แค่จดบทเรียนพรรณนา
> แรงบันดาลใจ: graph-engineering template §42 + ประสบการณ์จริงของ repo (CI แดงทั้งสัปดาห์จาก generated-content nondeterminism จบด้วย *test + determinism rule* ไม่ใช่การจดจำ)

## หลักเดียว

> **Executable memory beats prose memory.** — "จำไว้ว่าอย่าทำอีก" ไม่ใช่การแก้อะไร

## บันได 9 ขั้น — เลือกสูงสุดที่ทำได้ (ขั้น 1 แรงสุด)

| Tier | กลไก | ตัวอย่างใน repo นี้ |
|---|---|---|
| 1 | **Regression test** | `tests/test_repo_root_seam.py` (absolute-path guard bug) |
| 2 | **Deterministic checker** | `scripts/check_pr_loop.py`, `check-stale-specs.py` |
| 3 | **Type/schema constraint** | `schemas/awiki-review/v1` + `additionalProperties:false` |
| 4 | **Architectural invariant** | hooks_runner registry authority (register ก่อนรันเสมอ) |
| 5 | **CI rule** | `pr-loop-gate`, `gen-index --check` ใน Core CI |
| 6 | **Linter/static scan** | pre-commit privacy/secret scan |
| 7 | **Monitoring/alert** | wiki-health digest cron, provider balance |
| 8 | **Durable documentation** | protocol/ADR นี้, runbook |
| 9 | **Prose memory** (ledger lesson) | `.tmp/memory-ledger.jsonl` — **ใช้เมื่อไม่มีอะไรแรงกว่าเหลืออยู่เท่านั้น** |

## สัญญาการบันทึก (บังคับผ่านแบบฟอร์ม ledger)

เมื่อเขียน `type=lesson` ลง memory ledger สำหรับ defect ต้องระบุ `mechanism_tier` (เลข 1-9 จากบันได) + เหตุผลสั้นว่าทำไมไม่ใช้ tier ที่สูงกว่า:

```json
{
  "type": "lesson",
  "summary": "<อาการ> → <root cause>",
  "tags": ["defect", "tier-1"],
  "extra": {
    "mechanism_tier": 1,
    "mechanism": "tests/test_x.py::test_y",
    "why_not_higher": "test ครอบ case นี้พอดี; ไม่มี invariant ทั่วไปกว่านี้ที่ไม่ overfit",
    "evidence": "commit <sha> — แดงก่อนเขียวหลังเพิ่ม mechanism"
  }
}
```

**ไม่มี mechanism_tier = ยังไม่ถือว่าปิด defect** (a-loop Phase 3 distill จะไม่นับ)

## ตัวอย่างจริงจากประวัติ repo

| Defect | Tier ที่เลือก | เหตุผล |
|---|---|---|
| CI แดงทั้งสัปดาห์ (generated content นับ runtime file) | 5 + 4 | determinism rule (tracked-only) + อยู่ใน CI ทุก push |
| `.serena` staged ค้างหลุดติด commit | 2 | hook/ขั้นตอน "git status ก่อน commit" นับใจไม่ได้ — checker ถึงจะนับ |
| a-plan backtick หลุดโดนตีเป็นชื่อ skill | 1 | integrity test จับเฉพาะจุด — เพียงพอ |

## เมื่อไหร่ปรับลด tier

อนุญาตเลื่อนลงเมื่อ tier สูง **ทำให้ workflow ตายจริง** (เช่น บล็อกงานเล็กทุกครั้ง) — ต้องจดเหตุผลใน ledger เหมือนกัน ห้ามเงียบ

---
*เชื่อมต่อ: `agent-skills/engineering/` (debug-mantra 4 ขั้น = เครื่องมือหา root cause ก่อนเลือก tier) · Iron Law #1 (test-first) · a-loop Phase 3 (distill นับเฉพาะ lesson ที่มี mechanism_tier)*
