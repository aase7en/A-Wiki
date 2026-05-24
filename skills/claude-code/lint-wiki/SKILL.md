---
name: lint-wiki
description: Use this skill when the user asks for /lint, /status, or requests a wiki health check. Full workflow below — model-agnostic.
---

# lint-wiki

> **วัตถุประสงค์**: ตรวจสุขภาพ wiki ทั้งหมด — ใช้เมื่อผู้ใช้สั่ง `/lint` หรือขอ health check
> **เกณฑ์**: delegate `general-purpose` subagent เพื่อกัน context หลักไม่ให้บวม

---

## ขั้นตอน (subagent ทำ)

### 1. ตรวจ orphan pages
- หาหน้าใน `wiki/` ที่ไม่มี inbound links จากหน้าอื่น
- ตรวจทั้ง `entities/`, `concepts/`, `sources/`, `synthesis/`

### 2. ตรวจ contradictions
- เปรียบเทียบข้อมูลระหว่างหน้าต่างๆ ที่เกี่ยวข้อง
- รายงานถ้าพบข้อมูลขัดแย้งกัน (เช่น ราคา, spec, วันที่)

### 3. ตรวจ missing concepts
- หา concepts ที่ถูก link มาจาก entity/synthesis page แต่ยังไม่มีไฟล์จริง

### 4. ตรวจ stale pages
- หา `last_verified` ที่เกิน 90 วัน (สำหรับ time-sensitive entity)
- รายงานว่าใช้ `verify_tool` อะไรล่าสุด

### 5. ตรวจ frontmatter
- หาหน้าที่ขาด frontmatter fields บังคับ (`type`, `tags`, `sources`, `created`, `updated`)

---

## Output format

```markdown
## Lint Report — YYYY-MM-DD

### ⚠️ Orphan Pages (X)
| Path | Created | Last updated |
|------|---------|--------------|

### 🔴 Contradictions (X)
| หน้า 1 | หน้า 2 | รายละเอียด |
|--------|--------|------------|

### 🟡 Missing Concepts (X)
| Link ใน | Concept | เสนอให้สร้าง? |
|---------|---------|---------------|

### 🟠 Stale Pages (X)
| Path | last_verified | verify_tool |
|------|---------------|-------------|

### 🔵 Frontmatter Issues (X)
| Path | Field ที่ขาด |
|------|--------------|

### 📊 Summary
- Total pages: X
- Healthy: X
- Needs attention: X
```

---

## หลัง lint

1. นำเสนอรายงานให้ผู้ใช้ — ถามว่าจะ fix อะไรบ้าง
2. ถ้า fix หลายหน้า → เสนอ `/snapshot-nb` หลังจบ
3. บันทึกใน `log.md`:

```
## [YYYY-MM-DD] lint | health check
- พบ: X orphan, X contradiction, X stale
- Fixed: X
- ค้าง: X