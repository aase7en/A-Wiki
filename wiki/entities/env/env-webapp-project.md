---
type: entity
category: project
tags: [wastewater, supabase, migration, sibling-repo, companion-repo]
sources: []
created: 2026-07-05
updated: 2026-07-05
last_verified: 2026-07-05
verify_tool: training
---

# env-wastewater-webapp (sibling repo)

**ประเภท**: Software project — data migration + future monitoring webapp
**สถานะ**: Phase 1 (read-only CSV analysis) in progress
**Location**: `~/Desktop/env-wastewater-webapp` — **แยก git repo จาก A-Wiki** (private, github.com/aase7en/env-wastewater-webapp)

## ภาพรวม

Migrate ข้อมูลบ่อบำบัดน้ำเสียของ รพ.อุทัย จาก Google Sheets/AppSheet เข้า Supabase Postgres (`wastewater`/`carbon`/`core` schema) แล้วต่อยอดเป็น monitoring webapp (FastAPI + frontend) ในอนาคต

**สาเหตุที่แยก repo**: งานนี้เป็น production application code (migration scripts วันนี้ + FastAPI/frontend อนาคต) ต้องการ git workflow ปกติ (branch/PR/CI) ไม่ผูกกับกฎ "commit ตรง main ห้าม branch" ของ A-Wiki (Core Rule #6) ผู้ใช้ตัดสินใจแยก repo แต่ยังต้องการให้ความรู้โดเมน (schema, ENV concepts) อยู่ที่ A-Wiki เหมือนเดิม

## Code vs Knowledge split

| อะไร | อยู่ที่ไหน |
|------|-----------|
| Migration scripts, FastAPI backend, frontend (โค้ด production) | `env-wastewater-webapp` repo |
| Schema design doc | `wiki/synthesis/env-webapp-schema-wastewater.md` (A-Wiki) |
| ENV domain concepts (มาตรฐานน้ำทิ้ง, activated sludge ฯลฯ) | `wiki/concepts/env/`, `wiki/entities/env/` (A-Wiki) |
| หน้านี้ (project pointer) | A-Wiki — บอกว่าโค้ดจริงอยู่ repo ไหน |

## กลไกกันลืมว่าต้องใช้คู่กัน

- `env-wastewater-webapp/AGENTS.md` มีหัวข้อ "Companion repo — A-Wiki" ชี้กลับมาที่นี่ (resolve ผ่าน `$A_WIKI_ROOT` env var หรือ sibling directory `../A-Wiki`)
- `env-wastewater-webapp/.claude/hooks/session-start-companion-notice.sh` พิมพ์เตือนตำแหน่ง A-Wiki ทุก session start
- หน้านี้ (ฝั่ง A-Wiki) — ถูกดึงเข้า `wiki/context/overview-env.md` + `wiki-overview.md` อัตโนมัติทุกครั้งที่ `gen-index.py` รัน เพื่อให้เห็น sibling repo เวลาโหลด ENV domain context

## Supabase target

Project **ENV_DB** (`gllqtbyofrcjzmbnfoeh`, ap-southeast-1) — ยืนยันแล้วว่า `wastewater.reading` + `carbon.reading` ตรงกับ mapping table ที่ออกแบบไว้ (ดู `wiki/synthesis/env-webapp-schema-wastewater.md` และ commit history ของ repo ใหม่สำหรับรายละเอียด mapping ล่าสุด)

## ความสัมพันธ์

- เกี่ยวข้องกับ: [[hospital-wastewater-treatment]] — ความรู้โดเมน regulatory/technical
- เกี่ยวข้องกับ: [[water-quality-parameters]] — parameter ที่ migrate (DO, pH, TDS, SV30, Free Chlorine)
- Schema design: [[env-webapp-schema-wastewater]] (synthesis)

## แหล่งข้อมูล

- Repo: https://github.com/aase7en/env-wastewater-webapp (private)
- [training] — บันทึกจาก session ที่สร้าง repo นี้ 2026-07-05
