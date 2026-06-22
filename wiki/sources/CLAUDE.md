> **Cost-First**: ก่อนให้ Claude ทำงานใดๆ ใน domain นี้ → ดู [Cost-First Pyramid](/CLAUDE.md#-cost-first-decision-pyramid-บังคับคิดก่อนทุกงาน)
> Hook → Free API → Cheap paid (DeepSeek/Qwen) → Subagent Haiku → Claude Sonnet
> **Prompt ส่งออกนอก: ใช้ภาษาอังกฤษเสมอ** (ประหยัด token ~30%)

---


# Scoped Context — Source Summaries

> **โดเมน**: Source documents — summaries of raw/ content
> **Last updated**: 2026-06-22
> **ไฟล์นี้เป็น nested context สำหรับ Claude/Cline — อ่านเมื่อทำงานใน sources/**
> ถ้าการแก้ source workflow เปลี่ยนความสามารถของ A-Wiki brain, ingestion, provenance, hooks, scripts, หรือ public-safe policy → อ่าน `docs/protocols/brain-improvement-gate.md` ก่อน

---

## Sources ที่มีอยู่ (167 files)

ครอบคลุม 4 domains: IoT (ส่วนใหญ่), Environmental Health, AI Tools, Pharmacy

---

## Rules

1. **frontmatter บังคับ**: `type: source`, `title`, `slug`, `date_ingested`, `original_file`, `tags`
2. **ทุก source ต้องมี**: ประเภท (article/video/paper), วันที่, ผู้เขียน, ประเด็นหลัก, ข้อมูลที่น่าสนใจ
3. **ตรวจ contradiction**: ถ้า source ขัดแย้งกับ wiki ที่มี → ระบุในหัวข้อ "ข้อโต้แย้ง"
4. **อัปเดต "หน้า Wiki ที่ได้รับการอัปเดต"** ทุกครั้งที่ source ถูกใช้

---

## Workflow

1. source ใหม่ → สร้างใน `wiki/sources/<slug>.md` (ใช้ skill ingest-source)
2. เขียนสรุปตาม template ใน CLAUDE.md หลัก
3. เชื่อมโยงไป entities/concepts ที่เกี่ยวข้อง
4. รัน `python3 scripts/gen-index.py`
5. บันทึก `log.md`
