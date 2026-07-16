---
name: a-doc-_template
description: "TEMPLATE สำหรับสร้าง type ใหม่ — copy โฟลเดอร์นี้ + edit. ดู announce/ เป็นตัวอย่าง canonical ที่สมบูรณ์"
version: 0.1.0
author: A-Wiki
domain: [document, thai]
lifecycle_phase: build
category: pipeline
agents: [all]
invocation: manual
---

# A-Doc Type: _template (สำหรับ copy)

> **วิธีสร้าง type ใหม่**:
> 1. `cp -r skills/awiki/a-doc/types/_template skills/awiki/a-doc/types/<new-type>`
> 2. เปลี่น `name: a-doc-<new-type>` ใน frontmatter
> 3. เปลี่ยน description + structure ตามเอกสาร
> 4. เพิ่ม entry ใน `skills-registry.json`
> 5. `python scripts/regen-skill-surfaces.py` + commit

## ชื่อ type: <TODO>

## เมื่อไหร่ใช้ (trigger keywords)
- TODO: list keywords ที่บอกว่าเป็น type นี้

## ไฟล์ตัวอย่างใน `_uThaiHos`
- TODO: path + pattern ที่เห็น

## Structure (โครงเอกสาร)

```
TODO: layout บน→ล่าง
```

## Style profile ที่ใช้
- TODO: เลือกจาก `style-profiles/` หรือสร้างใหม่

## Generation

```javascript
// TODO: docx-js skeleton
```

## TODO (รอ user สอน)
- [ ] confirm structure
- [ ] confirm style profile
- [ ] test generate
