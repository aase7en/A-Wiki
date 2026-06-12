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

| Condition | วิธี |
|-----------|------|
| Skip ทั้ง session | `HOOK_SKIP=check_cost_tier` |
| Skip เฉพาะ automated CI | `CI=true` (set อัตโนมัติใน GitHub Actions) |
| Write ไปยัง `.tmp/` | exempt อัตโนมัติ |
| Bash/PowerShell/Read/Glob/Grep | exempt อัตโนมัติ |

## Session Start Integration

`session_start.py` ทำ 2 อย่างเพิ่มเติม:

- **Clean stale declarations**: ลบ `cost-tier-*.txt` จากวันก่อนหน้า (reset gate)
- **Warn stale scout**: ถ้า `model-scout-current.json` เก่า > 24h → แนะนำ `python3 scripts/model-scout-current.py`

## ทดสอบ

```bash
pytest tests/test_hooks.py::TestCostTierGate -v    # 11 tests
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
