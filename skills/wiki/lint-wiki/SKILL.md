---
name: lint-wiki
description: Use this skill when the user asks for /lint, /status, or requests a wiki health check. Full workflow in .claude/skills/lint-wiki/SKILL.md (model-agnostic).
---

# lint-wiki

ใช้เมื่อผู้ใช้ขอตรวจสุขภาพ wiki — `/lint` หรือ `/status`

## ขั้นตอน

1. Delegate `general-purpose` subagent scan `wiki/` ทั้งหมด พร้อม prompt:
   ```
   สแกน wiki/ ทั้งหมด รายงาน:
   - orphan pages (ถูก link แต่ไม่มีไฟล์จริง)
   - stale pages (last_verified > 90 วัน)
   - stub concepts (มี [[link]] แต่ยังไม่มีหน้า)
   - frontmatter ขาด field บังคับ (type, tags, updated)
   - contradictions กับ wiki-state.md Known Issues
   ตอบเป็น 5 sections — ห้ามแก้ไฟล์
   ```
2. Review รายงานจาก subagent → ตัดสินใจ action (fix / defer / accept)
3. Fix pages ที่จำเป็น → อัปเดต log.md
4. ถ้า fix > 5 หน้า → เสนอ user รัน `/snapshot-nb` ก่อนปิด session
