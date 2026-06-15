# Cost Gate Protocol

> Hook: `scripts/hooks/check_cost_tier.py` (blocking, PreToolUse)
> Pair: `session_start.py` resets gate daily + warns on stale scout

## ปัญหาที่แก้

Agent ใช้ primary model ทำงานทุกอย่างโดยไม่คิดก่อน แม้จะมี Cost-First Pyramid ใน CLAUDE.md เพราะ pyramid เป็นแค่ prose ไม่มี enforcement — จึงถูกข้ามทุก session

## วิธีทำงาน

Hook `check_cost_tier.py` บล็อก **Edit / Write / Agent / NotebookEdit** ทุกครั้งจนกว่า agent จะประกาศ tier งาน:

```
.tmp/cost-tier-YYYY-MM-DD.txt
content: "L4|task-type|reason"
```

ไฟล์นี้มีผลตลอดวัน (reset ตอน session start ของวันถัดไป)

## Tier Levels

| Tier | ช่องทาง | งานที่เหมาะ |
|------|---------|------------|
| **L1** | local / free | grep, FTS5, read-only, knowledge-graph |
| **L2** | cheap model | สรุปสั้น, table, reasoning เบา |
| **L3** | low-scout | scan ไฟล์เยอะ, lint, gather model intel |
| **L4** | primary | เขียนโค้ด, reasoning ซับซ้อน, wiki synthesis |

## Agent Workflow

1. Session เริ่ม → `session_start.py` แจ้งถ้า model scout เก่า > 24h
2. Agent ต้องการ Edit/Write/Agent → hook บล็อกพร้อมคำแนะนำ
3. Agent classify งาน → เลือก tier → สร้างไฟล์ประกาศ:

```bash
# Bash
echo "L4|implementation|เขียน NPC rendering ใน FarmScene" > .tmp/cost-tier-2026-06-12.txt

# PowerShell
[IO.File]::WriteAllText('.tmp\cost-tier-2026-06-12.txt', 'L4|implementation|เขียน NPC rendering')
```

4. Retry tool call เดิม → hook อ่าน tier → แสดง `💰 Cost tier: L4` → ผ่าน
5. Declaration ใช้ได้ตลอดวัน — เปลี่ยน task ให้ทับไฟล์ใหม่

## Skip Conditions

| Condition | วิธี | หมายเหตุ |
|-----------|------|---------|
| Skip ทั้ง session | `HOOK_SKIP=check_cost_tier` | bypass มี warning `💰 Cost gate: BYPASSED` ไป stderr |
| Skip เฉพาะ automated CI | `CI=true` (set อัตโนมัติใน GitHub Actions) | bypass มี warning เช่นกัน |
| Write ไปยัง `.tmp/` | exempt อัตโนมัติ | ที่เก็บ declaration เอง |
| Bash/PowerShell/Read/Glob/Grep | exempt อัตโนมัติ | ใช้เขียน declaration ได้ |

## ⚠️ Enforcement Reality — gate นี้บังคับได้แค่ไหน? [verified 2026-06-15]

ตรง ๆ: นี่คือ **"nudge เตือนสติ"** ไม่ใช่ **"กำแพงบังคับต้นทุน"** — บังคับให้ *ประกาศ* tier ได้จริง แต่ไม่ได้บังคับให้ *ทำตาม* tier ที่ประกาศ จุดอ่อนที่ตั้งใจ trade-off เพื่อ friction ต่ำ:

| จุดอ่อน | รายละเอียด | สถานะ |
|---------|-----------|-------|
| **Per-day ไม่ใช่ per-task** | ประกาศครั้งเดียวตอนเช้า → Edit/Write/Agent ทั้งวันผ่านหมด ไม่ว่า task จริงจะ tier ไหน | by design (friction ต่ำ) |
| **ไม่ validate model จริง** | ประกาศ L1 แล้วใช้ primary model เขียน 50 ไฟล์ก็ได้ — hook ไม่เห็น model ที่รันจริง | by design (hook ไม่มี access ถึง model state) |
| **Bash exempt** | agent เดียวกับที่เขียน declaration คือ agent ที่ไม่ถูก gate (เขียนผ่าน Bash) | by design (ต้องให้ self-declare ได้) |
| **Tier validity** | ~~`garbage` ก็ผ่าน~~ → **harden แล้ว 2026-06-15**: tier ที่ไม่ใช่ L1-L4 ถูก block (exit 2) | ✅ fixed |
| **Bypass เงียบ** | ~~`CI`/`HOOK_SKIP` ข้ามแบบไม่มีร่องรอย~~ → **harden แล้ว**: bypass emit warning ไป stderr | ✅ fixed |

**สรุป:** gate ยกระดับ "ความตั้งใจ" (ต้องหยุดคิด+ประกาศก่อนเขียน) แต่ enforcement จริงของ cost-first ยังพึ่ง **honor system + primary agent เป็น validator** (Iron Law III) ไม่ใช่กลไกบังคับอัตโนมัติ — ถ้าต้องการ hard enforcement ต้องเพิ่ม per-task re-declare หรือ model-vs-tier validation (friction สูงขึ้น)

## Session Start Integration

`session_start.py` ทำ 2 อย่างเพิ่มเติม:

- **Clean stale declarations**: ลบ `cost-tier-*.txt` จากวันก่อนหน้า (reset gate)
- **Warn stale scout**: ถ้า `model-scout-current.json` เก่า > 24h → แนะนำ `python3 scripts/model-scout-current.py`

## ทดสอบ

```bash
pytest tests/test_hooks.py::TestCostTierGate -v    # 17 tests (incl invalid-tier + empty-tier hardening)
pytest tests/test_hooks.py -v                       # full hook suite
```

## ตัวอย่าง session ที่ถูกต้อง

```
SessionStart → 💰 Cost gate: model scout เก่า 26h → python3 scripts/model-scout-current.py

[agent อยากทำ Edit wiki page]
⚠️  COST GATE: ยังไม่ได้ประกาศ tier งานนี้ (2026-06-13)
  L1/L2/L3/L4 ... (คำอธิบาย)

[agent classify]
$ echo "L2|wiki-edit|อัปเดตหน้า entity ไม่ต้อง reasoning" > .tmp/cost-tier-2026-06-13.txt

[agent retry Edit]
💰 Cost tier: L2  (L2|wiki-edit|อัปเดตหน้า entity ไม่ต้อง reasoning)
→ ผ่าน
```
