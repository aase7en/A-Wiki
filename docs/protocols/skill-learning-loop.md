# Self-Learning Skill Loop Protocol

> Module: `scripts/lib/skill_learning.py` (fail-soft, offline, Level 0 — see `docs/protocols/brain-improvement-gate.md`)
> Wired: `scripts/hooks/session_start.py::run_skill_learning_watch()` — non-lean path only
> Tests: `pytest tests/test_skill_learning.py -v`

## ปัญหาที่แก้

A-Wiki มี Cost-First Pyramid, Iron Laws, hooks — แต่ไม่มีอะไรจับ "รูปแบบงานที่ทำซ้ำแล้วซ้ำอีกข้าม session แต่ยังไม่มี skill ครอบ" agent ต้อง Edit ไฟล์แบบเดิม ๆ หลาย session โดยไม่มีใครสังเกตว่าน่าจะ scaffold เป็น skill แล้ว หรือ hook เดิมบล็อกซ้ำ ๆ จนน่าจะมี protocol/skill ช่วยลด friction — สัญญาณเหล่านี้จมอยู่ใน `log.md` (private journal) กับ `.tmp/live-events.jsonl` (hook telemetry) ที่ไม่มีใครอ่านย้อนหลังเป็นประจำ

โมดูลนี้อ่านสองแหล่งนั้นที่ SessionStart แล้วเสนอ (ไม่ scaffold เอง) เมื่อรูปแบบซ้ำเกิน threshold และยังไม่มี skill ครอบ

## วิธีทำงาน

1. **Parse `log.md`** → `parse_log_sessions()` แยกเป็น session ตาม header `## [YYYY-MM-DD] session | topic` (ทน header หลายแบบ: มี/ไม่มี `|`, มี/ไม่มี เวลา, em-dash form)
2. **สกัด term** → `extract_terms()` จับเฉพาะ **kebab-compound token** (เช่น `compaction-suggest`, `cost-tier`) จาก topic+body — คำเดี่ยวและข้อความไทยถูกมองข้ามโดยตั้งใจ (สัญญาณ low-noise, ไม่พยายามทำ general NLP)
3. **นับ session ที่ต่างกัน** ต่อ term (นับซ้ำใน session เดียวแค่ครั้งเดียว) → term ที่ปรากฏ ≥ `MIN_SESSIONS` distinct sessions และไม่ถูกครอบโดย `skills-registry.json` (ชื่อ/alias/description) → เสนอ
4. **อ่าน `.tmp/live-events.jsonl`** → hook ไหน `result: "block"` ≥ `HOOK_BLOCK_THRESHOLD` ครั้ง → เสนอแยกอีก kind หนึ่ง (`hook-friction`)
5. **Throttle**: ทำงานจริงเมื่อ cache (`.tmp/skill-learning-cache.json`) หายหรือเก่ากว่า `CHECK_EVERY_DAYS` เท่านั้น — ถ้ายังสด คืน `[]` ทันที ไม่แตะไฟล์ suggestions เลย
6. **เขียน `.tmp/skill-suggestions.json`** ทุกครั้งที่ทำงานจริง (แม้ suggestions ว่างเปล่า — ใช้เป็น freshness marker) แล้วอัปเดต cache
7. **คืน notice สูงสุด 3 บรรทัด** ให้ SessionStart พิมพ์; รายการเต็มอยู่ใน `.tmp/skill-suggestions.json`

## Thresholds / Env Flags

| ค่า | Default | ความหมาย |
|-----|---------|----------|
| `MIN_SESSIONS` | 3 | จำนวน distinct session ขั้นต่ำก่อนเสนอ log-pattern |
| `HOOK_BLOCK_THRESHOLD` | 5 | จำนวน block ขั้นต่ำต่อ hook ก่อนเสนอ hook-friction |
| `CHECK_EVERY_DAYS` | 7 | throttle — ไม่ทำงานจริงถี่กว่านี้ |
| `AWIKI_SKILL_LOOP` | `1` | `0` = ปิดทั้ง loop (คืน `[]` เสมอ) |
| `AWIKI_SKILL_LOOP_MIN_SESSIONS` | (unset) | override `MIN_SESSIONS` โดยไม่ต้องแก้โค้ด |

## Human-Approval Flow (สำคัญ — โมดูลนี้ไม่ scaffold เอง)

```
SessionStart → 🧠 Skill loop: 'cost-tier' ซ้ำ 3 sessions ยังไม่มี skill ครอบ → ดู .tmp/skill-suggestions.json

[มนุษย์อ่าน .tmp/skill-suggestions.json ตัดสินใจว่าคุ้มไหม]

$ python scripts/new-skill.py cost-tier --domain code --phase build
  # ปรับ domain/phase ให้ตรงงานจริงก่อนรัน — โมดูลนี้เดา domain=code, phase=build เป็นค่าเริ่มต้นเสมอ

→ new-skill.py เขียน skills-registry.json ก่อน แล้วค่อยเขียน SKILL.md (ลำดับนี้จำเป็น — hook #15
  check_skill_registry.py บล็อก SKILL.md ที่ยังไม่ได้ลงทะเบียน)
→ commit ตามปกติ (ไม่มี auto-commit จากโมดูลนี้)
```

Suggestion ที่เป็น `hook-friction` ไม่มี `new-skill.py` hint ตรง ๆ — เสนอให้พิจารณา skill หรือแก้ protocol ที่ต้นตอ (เช่น hook บล็อกบ่อยเพราะ workflow เดิมชนกฎซ้ำ ๆ)

## Fail-Soft Guarantees

`check_skill_patterns()` (public entry ที่ SessionStart เรียก) **ไม่มีทาง raise**:

| ความล้มเหลว | ผลลัพธ์ |
|-------------|---------|
| `log.md` หาย | ถือว่าไม่มี session, เดินหน้าต่อด้วย events อย่างเดียว |
| `skills-registry.json` corrupt/หาย | ถือว่า registry ว่าง (ไม่มีอะไรถูกครอบ) — ไม่ crash |
| `.tmp/live-events.jsonl` หายหรือมีบรรทัดพัง | ข้ามบรรทัดพัง, ไฟล์หาย → `[]` จากส่วนนั้น |
| cache JSON corrupt | ถือว่า stale, ทำงานจริง (ไม่ throttle ผิดพลาด) |
| เขียน `.tmp/` ไม่ได้ (permission, path ชน) | ข้ามการเขียนไฟล์, ยัง return notices ที่คำนวณในหน่วยความจำได้ |
| exception ใด ๆ ที่ไม่คาดคิด | `except Exception: return []` ที่ entry point |

ไม่มี network call ในโมดูลนี้เลย — อ่านเฉพาะไฟล์ในเครื่อง

## ทดสอบ

```bash
pytest tests/test_skill_learning.py -v              # parse/extract/suggest/registry-coverage/entry/CLI
pytest tests/test_lean_session_start.py -v           # run_skill_learning_watch อยู่ใน SKIPPABLE (lean mode ข้าม)
pytest tests/test_hooks.py -q                        # regression — ไม่กระทบ hook suite เดิม
pytest tests/test_vendor_watch.py -q                 # regression — neighbor module เดิมไม่พัง

python scripts/lib/skill_learning.py --report        # demo อ่านจริงจาก repo, ไม่แตะ cache/suggestions, exit 0 เสมอ
```

## ข้อจำกัดที่ตั้งใจ (by design)

- **ภาษาอังกฤษ kebab-compound เท่านั้น** — ข้อความไทยและคำเดี่ยวไม่ถูกนับเป็น pattern เพราะ noise สูงเกินไปสำหรับ regex-based extraction ถ้าต้องการ semantic clustering ข้ามภาษา ต้องเป็นโมดูลอื่น (เช่น sqlite-vec semantic search ที่มีอยู่แล้วใน wiki layer)
- **Domain/phase เดาเป็น `code`/`build` เสมอ** ใน hint — มนุษย์ต้องปรับก่อนรัน `new-skill.py` จริง
- **Per-session ไม่ใช่ per-repo-wide dedup อัจฉริยะ** — ถ้า session เดียวพูดถึง term เดิมหลายรอบนับครั้งเดียว แต่ session ที่ topic ต่างกันวันเดียวกัน (เช่น `session` กับ `session-2`) นับแยกกันตามการออกแบบ (`date+topic` = identity)
