---
name: ingest-source
description: Use this skill when the user sends a new source (file in raw/, URL, or pasted text) to be ingested into the wiki. Full workflow in .claude/skills/ingest-source/SKILL.md (model-agnostic).
---

# ingest-source

ใช้เมื่อผู้ใช้ส่ง source ใหม่ (ไฟล์ใน `raw/`, URL, หรือ paste text) เพื่อ ingest เข้า wiki

## ขั้นตอน

1. **อ่าน source** — ถ้าเป็น URL ให้ WebFetch ก่อน; ถ้าเป็นไฟล์ใน raw/ อ่านตรง
2. **ระบุ domain** — IoT / Env / AI Tools / Pharmacy (ถามถ้าไม่ชัด)
3. **สร้าง source summary** → `wiki/sources/<slug>.md` (template: wiki/CLAUDE.md §Source)
4. **อัปเดต entities/concepts** — เพิ่มหรือ patch หน้าที่เกี่ยวข้อง
5. **ตรวจ contradictions** — เปรียบกับ wiki-state.md Known Issues + existing pages
6. **อัปเดต index** — รัน `python3 scripts/gen-index.py` (chain: overview + graph + FTS5)
7. **อัปเดต log.md** — append entry
8. **รายงานสรุป** — entities/concepts ที่เพิ่ม/แก้ + contradictions ที่พบ

## กฎ
- raw/ เป็น immutable — ห้ามแก้ไข source ต้นฉบับ
- domain ต้องระบุก่อน create file ใดๆ
- ทุก wiki page ต้องมี cross-reference ไปหาหน้าที่เกี่ยวข้อง
