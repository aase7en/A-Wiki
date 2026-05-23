# Decisions — Architecture Decision Records (ADR)

> **TL;DR:** บันทึก major decision พร้อมเหตุผล — เพื่อให้ตัวเรา/ทีม/AI อนาคตเข้าใจ "ทำไมเลือก X ไม่ใช่ Y"

---

## ทำไมต้องเขียน

**Journal** = ความคิดประจำวัน (HOW we think daily)
**Decisions** = ตัดสินใจสำคัญ (WHY we chose this path)

ใช้ format **ADR** (Architecture Decision Record) ที่นิยมใน software engineering

ดู context ใหญ่ที่: [[wiki/synthesis/digital-legacy-ai-architecture]]

---

## เมื่อไหร่ควรเขียน

✅ **ควรเขียน** เมื่อ:
- ตัดสินใจเรื่องที่ **กลับไปแก้ยาก** (architecture, infrastructure)
- เลือกระหว่าง 2-3 options ที่มี trade-off
- มีคน/AI อนาคตจะถาม "ทำไมทำแบบนี้"
- เปลี่ยนทิศทางสำคัญ (deprecate, migrate, refactor)

❌ **ไม่ต้อง** เมื่อ:
- เป็นรายละเอียด implementation (ใส่ใน wiki แทน)
- ตัดสินใจชั่วคราว เปลี่ยนได้ตลอด
- ไม่มีทางเลือกอื่น (auto-pilot)

---

## รูปแบบไฟล์

```
decisions/
├── README.md              ← ไฟล์นี้
├── _template.md           ← copy ไปใช้
├── 0001-digital-legacy-strategy.md
├── 0002-git-mirror-redundancy.md
├── 0003-...
└── deprecated/
    └── 0xxx-old-decision.md   ← ย้ายมาเมื่อ superseded
```

ชื่อไฟล์: `NNNN-kebab-case-title.md` (4-digit number, ascending)

---

## Workflow

### สร้าง ADR ใหม่
```bash
cd ~/Code/wiki-clean
NEXT=$(ls decisions/*.md 2>/dev/null | grep -oE '^decisions/[0-9]{4}' | sort | tail -1 | grep -oE '[0-9]+')
NEXT=$(printf "%04d" $((10#${NEXT:-0}+1)))
cp decisions/_template.md "decisions/${NEXT}-my-new-decision.md"
code "decisions/${NEXT}-my-new-decision.md"
```

หรือบอก Claude:
```
"สร้าง ADR เรื่อง X — ตัดสินใจระหว่าง A กับ B"
```

### Update existing ADR
- **ไม่แก้** ของเก่าโดยตรง — ADR คือ historical record
- ถ้าเปลี่ยนใจ → สร้าง ADR ใหม่ที่ "supersedes ADR-NNNN"
- ของเก่ามาร์ค status: `Superseded by ADR-XXXX` แล้วย้ายไป `decisions/deprecated/`

---

## Template Status Values

| Status | ความหมาย |
|--------|---------|
| `Proposed` | ยังไม่ตัดสินใจ — กำลังถก |
| `Accepted` | ตัดสินใจแล้ว ใช้งานอยู่ |
| `Deprecated` | ไม่ใช้แล้ว แต่ยังไม่มีตัวแทน |
| `Superseded by ADR-XXXX` | ถูกแทนที่ด้วย ADR ใหม่ |

---

## ความสัมพันธ์
- [[journal/]] — บันทึกประจำวัน
- [[wiki/synthesis/digital-legacy-ai-architecture]] — ภาพใหญ่
- [[CLAUDE.md]] — กฎสำหรับ Claude เกี่ยวกับ wiki
