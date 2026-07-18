---
type: synthesis
tags: [web-app, postgresql, schema, env, multi-domain, v2, supabase, carbon-footprint]
sources: [env-webapp-schema-wastewater, appsheet-env-datadict, ENV_DB-live-introspect-2026-07-17]
created: 2026-07-17
updated: 2026-07-17
supersedes: [env-webapp-schema-wastewater.md]
---

# ENV_DB Schema (v2 — multi-domain) — Supabase

> **Supersedes** `env-webapp-schema-wastewater.md` (Pi5 era, wastewater-only).
> v2 expands from 2 operational schemas (wastewater + carbon) to **10 schemas**
> covering every environmental / occupational-health / safety module
> รพ.อุทัย runs.

## Project

- **Repo**: `env-wastewater-webapp` (private) — React 18 + Vite + TS frontend,
  Supabase-first (no FastAPI in production, ADR-0004).
- **Companion**: this file + `wiki/entities/env/*` are the domain knowledge.
- **Supabase project**: `ENV_DB` (`gllqtbyofrcjzmbnfoeh`, ap-southeast-1).
- **Migration trail**: `supabase/migrations/*.sql` in the repo. Live introspect
  via `scripts/introspect_schema_api.py` (Management API over HTTPS — IPv6
  workaround).

## Schemas (10)

| Schema | Purpose | Tables | Carbon scope |
|---|---|---|---|
| `core` | Master/reference (personnel, equipment, location, app_user, AI tables, audit_log, attachment, pdf_template, repair_request, regulation TBD) | 11 | — |
| `wastewater` | บ่อบำบัดน้ำเสีย — daily quality log (existing) | `reading`, `threshold`, `threshold_alert` | — |
| `carbon` | Carbon accounting — meters, daily readings, emission factors, monthly rollup view | `meter`, `reading`, `emission_factor`, `v_monthly_co2e`, `v_reading_co2e`, `v_unified_co2e` (TBD) | Scope 2 |
| `water_supply` | น้ำประปาบาดาล — daily quality check | `daily_check` | — |
| `garbage` | ขยะ — collection log | `collection_log` | Scope 3 |
| `fuel` | น้ำมันเชื้อเพลิง — dispense log | `dispense_log` | Scope 1 |
| `garden` | คนสวน/ตัดหญ้า — work round | `work_round` | Scope 1 |
| `building` | อาคารสถานที่ — inspection round | `inspection_round` | — |
| `safety` | ความปลอดภัย — monthly fire/emergency-light check | `monthly_check` | — |
| `food` | สุขาภิบาลอาหาร — coliform lab test | `lab_test` | Scope 3 |
| `chemical` | คลังเคมีภัณฑ์ย่อย — movement + balance | `movement` (+ optional `master`) | Scope 1/3 |

## Conventions (binding)

1. **Master data** lives in `core.*` (personnel, equipment, location, location_category, app_user). Operational data lives in domain schemas.
2. **Every transactional table has** `id uuid PK DEFAULT gen_random_uuid()`, `*_date date NOT NULL`, `recorded_by uuid` (FK to auth.users via app_user), `created_at timestamptz DEFAULT now()`.
3. **RLS enabled on every table** + policy `<schema>_<table>_rw` (authenticated, ALL commands, `true`/`true`). Anon (unauthenticated) gets nothing. Service-role bypasses RLS via Supabase service key (server-only).
4. **Thai dates** are stored as `date` (Gregorian CE). UI displays พ.ศ. via `core.thai_be_to_date()` helper or client-side conversion. Never assume CE in display.
5. **Carbon feed pattern**: every module that contributes GHG has a clear column (litres, kWh, weight_kg, fuel_used_l) that joins to `carbon.emission_factor` on source+unit.
6. **Audit trail**: `core.audit_log` (existing) — SCHEMA-4 will add generic trigger on every transactional table.
7. **PHI boundary**: hospital patient-adjacent data must NOT route through AI providers or ZCode (Chinese data law). ENV data itself (water/air/waste checks) is operational, not patient-identifiable — verified case-by-case per module.

## New schemas (SCHEMA-1 — applied 2026-07-17)

Skeleton tables; columns extended in MOD-* chunks. See `supabase/migrations/20260718000003_v3a_alert_readrls.sql` and `20260719000000_v2_schemas.sql`.

```sql
-- 8 new transactional tables (RLS enabled, authenticated-rw policy each)
water_supply.daily_check   (id, check_date, location_id, recorded_by, note, created_at)
garbage.collection_log     (id, log_date, location_id, waste_type, weight_kg, disposal_route, recorded_by, note, created_at)
fuel.dispense_log          (id, log_date, fuel_type, litres, meter_before, meter_after, vehicle_or_use, recorded_by, note, created_at)
garden.work_round          (id, round_date, location_id, work_type, area_sqm, worker_count, fuel_used_l, recorded_by, note, created_at)
building.inspection_round  (id, round_date, location_id, inspector, findings, issues_found, repair_needed, recorded_by, note, created_at)
safety.monthly_check       (id, check_date, location_id, extinguisher_inspected, exit_light_functional, issues_found, recorded_by, note, created_at)
food.lab_test              (id, sample_date, sample_type, test_type, result, reported_date, technician, recorded_by, note, created_at)
chemical.movement          (id, movement_date, chemical_name, direction, quantity, unit, balance_after, purpose, recorded_by, note, created_at)
```

## Cross-domain carbon rollup (TBD — SCHEMA-3)

`carbon.v_unified_co2e` will UNION every carbon-contributing table across
schemas, aggregated by month, tagged by scope (1/2/3) + source. Drives the
unified carbon dashboard (CRB-3).

## Existing schemas (existing, prior to v2)

- `wastewater.reading` — 907 rows migrated from AppSheet (Phase 2 complete 2026-07-05)
- `wastewater.threshold` — config (min/max per parameter, effective_from)
- `wastewater.threshold_alert` — violation log + `read_at` (V3a)
- `carbon.reading` — 907 rows; consumption column is authoritative (phase1 §4)
- `carbon.meter` — 1 active ("ระบบบ่อบำบัดน้ำเสีย"); `source_type` enum = electricity/diesel/gasoline/lpg/other
- `carbon.emission_factor` — empty as of SCHEMA-1; SCHEMA-2 fills Scope 1+2+3 rows
- `core.app_user` (role admin/staff), `core.personnel` (9 seeded), `core.equipment` (10), `core.location` (1), `core.location_category` (16 — 8 original + 8 new env zones)
- `core.ai_provider`, `core.ai_query_log`, `core.ai_scope` — empty; Wave 4 AI-1/2/3 use them
- `core.pdf_template` — empty; ADR-0001 + Wave 4 PDF-1/2/3 use it
- `core.repair_request` — V1a data layer ready
- `core.audit_log`, `core.attachment` — empty; SCHEMA-4 + DOC-3 use them

## Work-order system

WO files in `docs/work-orders/` (env-wastewater-webapp repo) define each chunk:
- **Done (Wave 1)**: V1a (repair), V3a (alerts), V2a (carbon data)
- **In progress**: SCHEMA-1 (this — foundations applied, doc synced)
- **Queued Wave 2**: SCHEMA-2 (emission factors), SCHEMA-3 (rollup view), SCHEMA-4 (audit trigger)
- **Queued Wave 3**: MOD-WS/WA/FU/GA/BL/FS/FO/CH (8 modules — data + UI skeleton)
- **Queued Wave 4**: AI-1/2/3 (provider config + chat port from A-Wiki), IMP-1/2/3 (generic import), PDF-1/2/3 (template designer)
- **Queued Wave 5**: CRB-1/2/3/4 (carbon rollup expansion)
- **Queued Wave 6**: DOC-1/2/3 (regulatory + manuals)
- **Queued Wave 7**: F-DASH/PERF/A11Y (polish — Track F)

## Companion entity pages

Each module has a domain-knowledge page in `wiki/entities/env/`:
- `env-webapp-project.md` (existing pointer)
- `activated-sludge-system.md` (existing — wastewater process)
- `water-supply.md`, `garbage.md`, `fuel.md`, `garden.md`, `building.md`, `fire-safety.md`, `food.md`, `chemical.md` (8 new skeletons — created in this sync)
