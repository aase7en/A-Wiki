---
type: entity
category: project
tags: [wastewater, supabase, migration, sibling-repo, companion-repo, react, vite, github-pages]
sources: []
created: 2026-07-05
updated: 2026-08-07
last_verified: 2026-08-07
verify_tool: training
---

# env-wastewater-webapp (sibling repo)

**ประเภท**: Software project — data migration + monitoring webapp
**สถานะ** (verified 2026-08-07 ผ่านการอ่าน `MIGRATION.md` + `git log`):
907/907 rows migrated (P1–P4 เสร็จ 2026-07-07). **FastAPI backend ถูก retire
ไปแล้ว** (`c6fc72a`, 2026-07-19, "Approach C — direct-to-Supabase") — frontend
เรียก Supabase โดยตรงผ่าน JS client + PostgREST façade views. Frontend
(React + Vite + TypeScript + Tailwind) shipped เป็น tracer-bullet P10+ แล้ว
deploy บน GitHub Pages. งานปัจจุบันเป็น **two-track parallel**: Track F
(Fable5/Claude — visual layer) ∥ Track Z (ZCode/GLM — feature/data/SQL layer).
Shipped ล่าสุด: OAUTH-1..4 (Google/LINE + deny-pending RLS), SCHEMA5b (5
reference tables), AI-SQL trio (P4-nl-sql + audit-viewer + suggest-chip), DOCK
role-module-visibility, 6-bug backlog sweep, OPT-HYGIENE (carbon.ts tests +
WO sync). ดู `MIGRATION.md` ใน repo นั้นสำหรับ chunk plan + In-progress claims.
**Location**: sibling directory ของ A-Wiki บนเครื่องเดียวกัน (`$A_WIKI_ROOT/../env-wastewater-webapp` หรือตามที่ผู้ใช้ clone) — **แยก git repo จาก A-Wiki** (private, github.com/aase7en/env-wastewater-webapp)

## ภาพรวม

Migrate ข้อมูลบ่อบำบัดน้ำเสียของ รพ.ประจำอำเภอ จาก Google Sheets/AppSheet เข้า Supabase Postgres (`wastewater`/`carbon`/`core` schema) แล้วต่อยอดเป็น monitoring webapp (frontend เรียก Supabase ตรง — FastAPI ถูก retire แล้ว)

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
  `energy_per_m3`, `date_thai_be` — implement ใน frontend (`lib/carbon.ts`,
  `lib/utils.ts`) และ SQL views ฝั่ง Supabase (ไม่ใช่ Pydantic อีกต่อไป)
- alert thresholds: DO<2.0, Cl<0.5, pH 6.5–8.5 (frontend inline warnings)

**สำหรับ schema จริง** ดู:
- `reports/schema-snapshot-live.md` (live introspection output)
- `scripts/introspect_schema_api.py` — รันเพื่อ refresh snapshot ผ่าน Management API
- `MIGRATION.md` — per-phase decisions สำหรับแต่ละตาราง

## ความสัมพันธ์

- เกี่ยวข้องกับ: [[hospital-wastewater-treatment]] — ความรู้โดเมน regulatory/technical
- เกี่ยวข้องกับ: [[water-quality-parameters]] — parameter ที่ migrate (DO, pH, TDS, SV30, Free Chlorine)
- Schema design (legacy, Pi5 era): [[env-webapp-schema-wastewater]] (synthesis) — **อ่านคำเตือนด้านบนก่อนใช้**
- Backend ADR (legacy FastAPI, superseded by Approach C): `docs/adr/0003-fastapi-sqlalchemy-async-supabase-jwt.md` ใน sibling repo
- Removal record: `docs/work-orders/FASTAPI-removal.md` ใน sibling repo

## Current state (verified 2026-08-07)

> **⚠ FastAPI ถูก retire แล้ว** — section ข้างล่างเดิม ("P5 deliverables")
> อธิบาย backend ที่ถูก removed ใน `c6fc72a` (2026-07-19). Source preserved
> บน branch `archive/fastapi-backend` หากต้องการดู. คำตอบใน handoff docs
> ที่บอก "FastAPI removal still open / assigned to Opus 4.8" = stale.

Stack ปัจจุบัน: **React 18 + Vite + TypeScript + Tailwind + Supabase JS
client + GitHub Pages** (no separate API tier). Auth = Supabase Auth
(email/password + Google + LINE, OAuth-1..4). Tests = Vitest (132/132) +
Playwright E2E (31/31). ดู `MIGRATION.md` ใน sibling repo สำหรับ
In-progress claims table + chunk history + Track F/Z lane rules.

## แหล่งข้อมูล

- Repo: https://github.com/aase7en/env-wastewater-webapp (private)
- [training] — บันทึกจาก session ที่สร้าง repo นี้ 2026-07-05
