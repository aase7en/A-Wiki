> **อ่านเมื่อทำงานใน `wiki/`** — auto-loaded by Claude Code เมื่อ cwd อยู่ใน wiki/ หรือ subdirectory
> สำหรับรายละเอียด delegation/notebooklm/knowledge-currency → ดู `docs/protocols/`
> ถ้าการแก้ wiki เปลี่ยนความสามารถของ A-Wiki brain, agent workflow, skills, hooks, scripts, sync, หรือ policy ข้อมูลส่วนตัว → อ่าน `docs/protocols/brain-improvement-gate.md` ก่อน

---

## รูปแบบหน้า Wiki

### หน้า Entity (`wiki/entities/iot/<name>.md` หรือ `wiki/entities/env/<name>.md`)
```markdown
---
type: entity
category: [device|protocol|company|person|project]
tags: [tag1, tag2]
sources: [source-slug-1, source-slug-2]
created: YYYY-MM-DD
updated: YYYY-MM-DD
last_verified: YYYY-MM-DD        # วันที่ตรวจสอบข้อมูล time-sensitive ล่าสุด (ราคา, version, สถานะ)
verify_tool: training|WebSearch|Gemini|WebFetch
---

# ชื่อ Entity

**ประเภท**: ...  
**สถานะ**: ...

## ภาพรวม
[2-4 ประโยคสรุป]

## คุณสมบัติหลัก
- ...

## การใช้งานใน IoT
[บริบทเฉพาะของโดเมน IoT]

## ความสัมพันธ์
- เกี่ยวข้องกับ: [[page-name]]
- แข่งขันกับ: [[page-name]]
- ใช้ร่วมกับ: [[page-name]]

## แหล่งข้อมูล
- [[sources/source-slug]] — [คำอธิบายสั้น]
```

### หน้า Concept (`wiki/concepts/iot/<name>.md` หรือ `wiki/concepts/env/<name>.md`)
```markdown
---
type: concept
tags: [tag1, tag2]
sources: [source-slug-1]
created: YYYY-MM-DD
updated: YYYY-MM-DD
last_verified: YYYY-MM-DD
verify_tool: training|WebSearch|Gemini|WebFetch
---

# ชื่อ Concept

## นิยาม
[คำอธิบายกระชับ]

## ทำไมถึงสำคัญใน IoT
...

## วิธีการทำงาน
...

## ตัวอย่างการใช้งาน
...

## ข้อดี / ข้อเสีย
| ข้อดี | ข้อเสีย |
|-------|---------|
| ...   | ...     |

## ความสัมพันธ์
- [[concept-name]] — [ความเกี่ยวข้อง]

## แหล่งข้อมูล
- [[sources/source-slug]]
```

### หน้า Source (`wiki/sources/<slug>.md`)
```markdown
---
type: source
title: "ชื่อบทความ/เอกสาร"
slug: source-slug
date_ingested: YYYY-MM-DD
original_file: raw/filename.md
tags: [tag1, tag2]
---

# [ชื่อ Source]

**ประเภท**: article | paper | video | podcast | book-chapter  
**วันที่**: [วันที่เผยแพร่ หรือ unknown]  
**ผู้เขียน**: ...

## ประเด็นหลัก
1. ...
2. ...
3. ...

## ข้อมูลที่น่าสนใจ / สถิติ
- ...

## ข้อโต้แย้งหรือความขัดแย้ง
[เปรียบกับสิ่งที่ wiki รู้อยู่แล้ว — ถ้ามี]

## หน้า Wiki ที่ได้รับการอัปเดต
- [[entities/...]]
- [[concepts/...]]
```

### หน้า Synthesis (`wiki/synthesis/<name>.md`)
```markdown
---
type: synthesis
tags: [tag1, tag2]
sources: [slug1, slug2]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# ชื่อการวิเคราะห์

## คำถามที่ตอบ
...

## สรุป
...

## การวิเคราะห์
...

## แหล่งข้อมูลที่ใช้
- [[sources/...]]
```

---

---

## Workflow: Ingest Source ใหม่

> ใช้ skill: `ingest-source` — `.claude/skills/ingest-source/SKILL.md`

เมื่อผู้ใช้ส่ง source ใหม่ (ไฟล์ใน `raw/` หรือ URL หรือ paste text):
อ่าน source → ระบุ domain → สร้าง source summary → อัปเดต entities/concepts → ตรวจ contradictions → อัปเดต index + log → รายงานสรุป

---

---

## ⚡ Fast Query Protocol (ลด API tokens 60-70%)

**ลำดับการโหลด context ก่อนตอบทุก session:**

```
1. อ่าน wiki/context/wiki-overview.md      ← แทน index.md + 10 หน้า
2. อ่าน wiki/context/knowledge-graph.md   ← เมื่อต้องการ relationships
3. อ่านหน้าเต็มเฉพาะเมื่อ abstract ไม่เพียงพอ
```

**Topic Router — โหลดเฉพาะสิ่งที่ต้องการ:**
- คำถาม hardware (IoT) → `entities/iot/` ที่เกี่ยวข้อง (ดูจาก overview)
- คำถาม hardware/มาตรฐาน (Env) → `entities/env/` + `concepts/env/`
- คำถาม concept → concepts/{domain}/ + linked entities
- คำถาม "ออกแบบระบบ X" → synthesis ก่อน → ถ้าไม่มีค่อย entities+concepts
- คำถาม cross-domain (IoT × Env) → synthesis/ ก่อน จากนั้นค่อย load ทั้งสอง domain
- Ingest ใหม่ → ตามปกติ (อ่าน source ก่อน → ระบุ domain)

**หลัง ingest หรือแก้ไข wiki:**
- อัปเดต `wiki/context/wiki-overview.md` (เพิ่ม abstract ใหม่)
- อัปเดต `wiki/context/knowledge-graph.md` (ถ้า relationships เปลี่ยน)
- อัปเดต memory `wiki-state.md` (page count, hardware, stubs)

---

## Workflow: ตอบคำถาม (Query)

1. อ่าน `wiki/context/wiki-overview.md` หา abstract ที่เกี่ยวข้อง (ไม่ต้องอ่าน index.md)
2. ถ้าต้องการ relationships → อ่าน `wiki/context/knowledge-graph.md`
3. อ่านหน้าเต็มเฉพาะเมื่อจำเป็น
4. **ถ้าต้องอ่าน >5 หน้า → delegate `general-purpose` subagent** (ดู §🧩 Subagent Delegation)
5. **ถ้าคำถามเชิง synthesize หลาย source** → เสนอ user ใช้ NotebookLM ก่อน (ดู §📘 NotebookLM-first Protocol)
6. ตอบคำถามพร้อม citations ไปยังหน้า wiki
7. ถ้าคำตอบมีคุณค่า → เสนอผู้ใช้ว่าจะ save เป็นหน้า synthesis ไหม
8. เพิ่ม log entry ถ้าเป็นการวิเคราะห์สำคัญ

---

---

## Workflow: Lint Wiki

> ดูรายละเอียดเต็มที่: `.claude/skills/lint-wiki/SKILL.md`

ทำเมื่อผู้ใช้สั่ง `/lint` หรือขอ health check:

> **ใช้ `general-purpose` subagent** เพื่อกัน context หลักไม่ให้บวม — ดู §🧩 Subagent Delegation
> Claude หลักทำหน้าที่ review รายงานที่ subagent ส่งกลับ + ตัดสินใจ action ต่อ

1. ตรวจ orphan pages, contradictions, missing concepts, stale pages, frontmatter
2. รายงานสุขภาพของ wiki
3. ถ้า fix หลายหน้า → เสนอ `/snapshot-nb` หลังจบ

---
