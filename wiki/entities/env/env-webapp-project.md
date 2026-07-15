---
type: entity
category: project
tags: [wastewater, supabase, migration, sibling-repo, companion-repo, fastapi]
sources: []
created: 2026-07-05
updated: 2026-07-16
last_verified: 2026-07-16
verify_tool: training
---

# env-wastewater-webapp (sibling repo)

**ประเภท**: Software project — data migration + monitoring webapp backend
**สถานะ**: Phases P1–P5 เสร็จแล้ว (2026-07-16) — 907/907 rows migrated +
schema stabilized (P1–P4) + FastAPI backend scaffolded with all v1 endpoints
live (P5). PR #10 (https://github.com/aase7en/env-wastewater-webapp/pull/10)
เปิดอยู่บน branch `claude/webapp-p5-fastapi`.
ขั้นถัดไป: P6 frontend build-out (ยังไม่เริ่ม — รอ lock design direction) +
P5b.2-live (DB introspection, blocked รอ SUPABASE_DB_URL). ดู `MIGRATION.md`
ใน repo นั้นสำหรับ chunk plan + open follow-ups.
**Location**: sibling directory ของ A-Wiki บนเครื่องเดียวกัน (`$A_WIKI_ROOT/../env-wastewater-webapp` หรือตามที่ผู้ใช้ clone) — **แยก git repo จาก A-Wiki** (private, github.com/aase7en/env-wastewater-webapp)

## ภาพรวม

Migrate ข้อมูลบ่อบำบัดน้ำเสียของ รพ.ประจำอำเภอ จาก Google Sheets/AppSheet เข้า Supabase Postgres (`wastewater`/`carbon`/`core` schema) แล้วต่อยอดเป็น monitoring webapp (FastAPI + frontend) ในอนาคต

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

Project **ENV_DB** (`gllqtbyofrcjzmbnfoeh`, ap-southeast-1).

### ⚠️ Schema source-of-truth clarification

**Schema จริงใน ENV_DB คือ source of truth** — ไม่ใช่เอกสาร
`wiki/synthesis/env-webapp-schema-wastewater.md` (ที่อยู่ในไฟล์เดียวกับนี้)

เอกสาร synthesis นั้นเป็น **ดีไซน์ยุคแรก (Pi5 self-host era, 2026-05-04)** —
ออกแบบตาราง `treatment_ponds`/`staff`/`water_quality_records`/`meter_readings`
สำหรับ Docker-on-Pi5 stack ซึ่ง **ถูกยกเลิก** (Pi5 รัน Bitcoin node + Hermes
agent อยู่แล้ว ทำให้ CPU/RAM ไม่พอ). แผนย้ายไป Supabase free tier แทน (ดู ADR-0003
ใน sibling repo).

Schema ที่ implement จริงใน ENV_DB (P1–P4) ต่างออกไป:
- `core.app_user`, `core.personnel`, `core.location`, `core.location_category`,
  `core.equipment`, `core.repair_request`, `core.pdf_template`
- `carbon.meter`, `carbon.reading`
- `wastewater.reading`, `wastewater.threshold`
- views: `wastewater.v_reading_detail`, `wastewater.v_monthly_summary`

**สิ่งที่ยังใช้ได้จากเอกสารเก่า** (verified P5b.2-local):
- computed-value สูตร: `do_average`, `energy_kwh`, `sv30_percent`,
  `energy_per_m3`, `date_thai_be` (implement ใน `app/core/computed.py`)
- alert thresholds: DO<2.0, Cl<0.5, pH 6.5–8.5 (stub ใน `app/core/alert.py`)
- แนวคิด "computed ใน Pydantic ไม่เก็บ DB"

**สำหรับ schema จริง** ดู:
- `reports/schema-snapshot-p5.md` (local-source reconciliation, verified)
- `scripts/introspect_schema.py` — รันเพื่อ snapshot live schema
- `app/models/` — ORM models (11 ตัว, verified against INSERT contract)
- `MIGRATION.md` — per-phase decisions สำหรับแต่ละตาราง

## ความสัมพันธ์

- เกี่ยวข้องกับ: [[hospital-wastewater-treatment]] — ความรู้โดเมน regulatory/technical
- เกี่ยวข้องกับ: [[water-quality-parameters]] — parameter ที่ migrate (DO, pH, TDS, SV30, Free Chlorine)
- Schema design (legacy, Pi5 era): [[env-webapp-schema-wastewater]] (synthesis) — **อ่านคำเตือนด้านบนก่อนใช้**
- Backend ADR: `docs/adr/0003-fastapi-sqlalchemy-async-supabase-jwt.md` ใน sibling repo

## P5 deliverables (2026-07-16, PR #10)

- `app/` — FastAPI: 11 ORM models, 15 endpoints (readings CRUD, dashboard,
  reference, repair requests, PDF templates, `/api/me`)
- `app/core/` — config, async DB layer, auth (stub + JWT-ready), computed
  values, threshold alert stub
- `tests/` — 44 unit tests (pure functions, schemas, auth, endpoint contracts)
- `tests/integration/` — 8 tests ตรวจ schema/endpoints จริง (auto-skip จนกว่า
  `SUPABASE_DB_URL` จะถูกตั้ง)
- `scripts/introspect_schema.py` — snapshot live schema → `reports/schema-snapshot-live.md`
- `.github/workflows/test.yml` — CI runs unit suite ทุก PR (ไม่ต้องการ secret)
- สแต็ค: FastAPI + SQLAlchemy 2.0 async + asyncpg + Pydantic v2 (ADR-0003)

## แหล่งข้อมูล

- Repo: https://github.com/aase7en/env-wastewater-webapp (private)
- [training] — บันทึกจาก session ที่สร้าง repo นี้ 2026-07-05
