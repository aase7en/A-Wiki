---
name: ingest-source
description: Ingest แหล่งข้อมูลใหม่เข้า wiki — จาก raw/, URL, หรือข้อความที่วาง — แล้วสร้างหน้าสรุปใน wiki/sources/ และ entities/concepts ตาม domain
status: beta
migrated_from: InW-Wiki
---

# Ingest Source

> **TODO: migrate full content from InW-Wiki**
>
> Full workflow in `.claude/skills/ingest-source/SKILL.md` (model-agnostic)

This skill handles the complete ingestion pipeline:
1. Accept source (file in `raw/`, URL, or pasted text)
2. Classify domain (IoT, Env, AI-Tools, Pharmacy)
3. Create source summary in `wiki/sources/`
4. Extract entities and concepts into `wiki/entities/{domain}/` and `wiki/concepts/{domain}/`
5. Update index files
6. Log to `log.md`