---
title: Sunday Estate Webapp — Real-Estate Management Platform
type: synthesis
domain: cross-domain
related:
  - ai-tools
  - iot          # Pi5 self-hosted infrastructure
created: 2026-05-17
session: 2026-05-17 dev
sources:
  - claude.ai/design bundle (tvug1cB05oRqix3k0_2SEA)
  - /Users/aase7en/supabase-pi5/.env (Pi5 self-host config)
  - /Users/aase7en/Library/CloudStorage/GoogleDrive-aase7en@sunday-estate.com/My Drive/ปล่อยกู้
  - /Users/aase7en/Library/CloudStorage/GoogleDrive-aase7en@sunday-estate.com/My Drive/ขายที่ดิน
---

# Sunday Estate Webapp

ระบบจัดการธุรกิจอสังหาริมทรัพย์ของ **Sunday Estate Co., Ltd.** — แทนเอกสาร Google Drive + กระดาษเดิม. ออกแบบ UI hi-fi prototype ผ่าน claude.ai/design แล้วต่อ data layer เข้า Supabase self-host บน Pi5 พร้อม FastAPI backend สำหรับ AI/OCR

> **Code อยู่นอก wiki**: `/Users/aase7en/Desktop/sunday-estate-webapp/` (separate GitHub repo `aase7en/sunday-estate-webapp`)
> **Entry doc**: [`sunday-estate-webapp/GETTING_STARTED.md`](../../../sunday-estate-webapp/GETTING_STARTED.md)
> **Latest QA batch** (2026-05-18): [[sunday-estate-frontend-qa-2026-05-18]] — 4 bugs fixed + 21 ghost buttons wired (commit `1e8147c`)

---

## Modules ทั้งหมด

### Core business modules
1. **ปล่อยกู้ / รับซื้อฝาก / จำนอง** — ติดตามสัญญา, ดอกเบี้ย, ตารางผ่อน, แจ้งเตือนครบกำหนด + OCR เอกสาร (โฉนด, บัตร ปชช., สัญญา)
2. **ลงทุนพัฒนาที่ดิน** — บัญชีรายจ่าย, หุ้นส่วน + ปันผล, แบ่งแปลง (parcel), ROI calculator, Gantt timeline

### Cross-cutting features
3. **AI Assistant** — chat ผ่าน OpenRouter (เลือก model ฟรี/ถูกได้เอง), system prompt ใส่ context ตาม role
4. **OCR เอกสาร** — Vision model (Gemini Flash 2.0 free / Qwen2-VL) → JSON → pre-fill form
5. **Custom fields editor** — Admin เพิ่ม field ลง loan/land ได้จาก UI โดยไม่ต้อง migrate (เก็บใน `metadata` JSONB)
6. **Drag-and-drop dashboard** — 12 widget catalog, long-press แก้ลำดับ, บันทึก layout ต่อ user ที่ `profiles.dashboard_layout`
7. **Notification popover** — unread filter, mark-read = หายจาก popup
8. **3 themes** — Light (Stripe) / Dark (Linear) / Modern (Vercel violet→cyan glassy)
9. **3 languages** — ไทย / English / 中文 พร้อม tooltips
10. **Profile editor** — แก้ชื่อ/รูป/สี/เบอร์, อัปโหลด avatar ผ่าน Supabase Storage

---

## Role × Scope Matrix

| Role | Loans | Lands | Dashboard | Settings | Scope toggle |
|------|-------|-------|-----------|----------|--------------|
| **Admin** | all (CRUD + delete) | all (CRUD + delete) | full + custom widgets | ทุก section + custom fields + model picker | All / Company / Personal |
| **Super** | scope='company' only (CRUD) | scope='company' read-only | full (no personal-only widgets) | integrations + account | locked → company |
| **User** (borrower) | own contracts only | none | borrower widgets | own profile + notifs | locked → own |

**Scope filter** (Admin only): `all` / `company` (Sunday Estate Co.,Ltd. + partners) / `personal` (Admin's individual business)

---

## Tech stack

| Layer | Choice | Why |
|-------|--------|-----|
| Frontend | React 18 + Babel-in-browser (bundle as-is) | rapid iteration, no build step; ฟิวเจอร์ migrate Vite+TS |
| Styling | CSS custom properties (3-theme system) | one source of truth, swap via `data-theme` attr |
| Fonts | IBM Plex Sans Thai + IBM Plex Mono + Sarabun | Thai-first typography |
| Charts | Custom SVG (in dashboard.jsx) | no extra lib |
| Backend | FastAPI on Pi5 | proxy for AI/OCR + admin ops |
| Database | Supabase self-host (Pi5 stack `supabasepi5`) | Auth + RLS + Storage + Realtime + Studio |
| Auth | Supabase Auth — Google OAuth + Email/Password | first signup → auto admin |
| AI / OCR | OpenRouter (Admin-selectable model) | free tier (Gemini Flash 2.0, Llama 3.3, Qwen) |
| Deploy | Docker Compose + Cloudflare Tunnel | nginx only public; Supabase/Postgres/Portainer/Bitcoin LAN-only |

---

## Infrastructure on Pi5

- Pi5 รัน Umbrel + Bitcoin node — **ห้ามแตะ**
- Supabase self-host ผ่าน Portainer, stack `supabasepi5`
  - Supabase API/Studio: `http://umbrel.local:8000` (Kong gateway)
  - Pooler ports: `5433` (session), `6543` (transaction) — internal/LAN only
  - PostgreSQL เก่า `webapp_db` ยังอยู่ที่ `5432` — ห้าม overwrite
- Secrets: `/Users/aase7en/supabase-pi5/.env` (ห้าม commit, ห้าม expose `SERVICE_ROLE_KEY` ใน frontend)
- Webapp stack จะลง Portainer แยก: `nginx :8080` + `fastapi :8000` (internal) + `cloudflared` (public profile)

---

## Supabase schema (13 migrations)

ลำดับการรัน — ดู [`sunday-estate-webapp/supabase/README.md`](../../../sunday-estate-webapp/supabase/README.md)

| # | File | Creates |
|---|------|---------|
| 0001–0002 | extensions + enums | pgcrypto, citext, pg_trgm, 19 ENUM types |
| 0003 | profiles | + `handle_new_user` trigger (first user → admin) + role helpers (`is_admin()`, `is_admin_or_super()`, `current_role()`) |
| 0004 | loans | + `loan_payments` (PK `LN-YYYY-NNN`, generated `due` column) |
| 0005 | lands | + `land_costs` / `land_partners` / `land_parcels` |
| 0006 | documents | metadata table; files in Supabase Storage bucket `documents` |
| 0007 | notifications | + `notification_reads` (per-user popover unread) |
| 0008 | audit_log + activity_log | trigger ทุก INSERT/UPDATE/DELETE บน loans/lands/profiles |
| 0009 | custom_field_defs + app_settings + or_model_cache | seeded defaults |
| 0010 | **RLS policies** | DENY-by-default, scope-aware (admin → all, super → company, user → own) |
| 0011 | storage | `documents` bucket (20MB, private) + path-aware policies `<entity>/<id>/file` |
| 0012 | views | `loan_summary`, `loans_aging`, `kpi_snapshot` + RPC helpers |
| 0013 | seed_demo | optional — demo data mirroring bundle |

### Extensibility built-in
- ทุก main table มี `metadata JSONB` + `tags TEXT[]` → เพิ่ม field โดยไม่ต้อง migrate
- `custom_field_defs` table — Admin สร้าง field ใหม่จาก UI; ค่าจริงเก็บใน `loans.metadata->>field_key`
- AI query (Admin only) ใช้ `custom_field_defs` schema → AI รู้จัก fields ทันทีที่สร้าง

---

## Project structure

```
sunday-estate-webapp/
├── GETTING_STARTED.md             ← walkthrough + troubleshooting
├── docker-compose.yml             ← nginx + fastapi + cloudflared
├── .env.example
├── prototype/                     ← React webapp (Babel-in-browser)
│   ├── index.html  styles.css  config.js
│   └── src/  (12 .jsx files: sbclient, data, ui, shell, login,
│              dashboard, loans, lands, borrower, ai, misc, app)
├── backend/                       ← FastAPI
│   ├── main.py  Dockerfile  requirements.txt
│   ├── core/    (config, auth, supabase, openrouter)
│   └── routers/ (ai, ocr, ai_sql, openrouter, custom_fields)
├── supabase/
│   ├── migrations/0001…0013.sql  ← 13 files, 1130 lines
│   └── README.md
└── deploy/
    ├── nginx/nginx.conf           ← static + reverse proxy /api/ + /<auth|rest|storage|realtime>/v1/
    └── cloudflared/config.example.yml
```

---

## Decisions & rationale (session 2026-05-17)

- **Bundle prototype as-is แทน Vite+TS รอบแรก** — speed of iteration ก่อน, migrate ทีหลังถ้าจำเป็น
- **Supabase self-host (Pi5) แทน Cloud** — Pi5 setup ทำไปแล้ว, ไม่ต้องสมัคร, ฟรี, public ผ่าน Cloudflare Tunnel
- **OpenRouter แทน Claude API ตรง** — Admin pick model ฟรี/ถูก (Gemini Flash 2.0, Qwen, DeepSeek) ลด cost
- **Demo mode shim ใน `sbclient.jsx`** — UI ทำงานได้แม้ไม่ตั้ง Supabase (mock auth + queries) → user ทดสอบ flow ได้ก่อน
- **Cache-buster `?v=N` ใน index.html** — Babel-in-browser cache aggressive, ต้อง bump version เมื่อแก้ .jsx
- **AddWidgetModal portal to body** — fade-in parent animation มี `transform` ทำให้ `position: fixed` ตกอยู่ใน parent containing block → ต้อง portal ออกมา
- **First signup → auto admin** — trigger ใน `0003_profiles.sql` ทำให้ Setup ครั้งแรกง่าย
- **service_role = backend only** — FastAPI ใช้สำหรับ admin ops; browser ใช้ ANON_KEY + JWT พร้อม RLS
- **Cloudflare Tunnel เปิดแค่ nginx :80** — Supabase Studio (8000), Portainer (9000), Postgres (5432/5433/6543), Bitcoin ports ยังคงอยู่ใน LAN

---

## Verification status (end of session)

✅ Demo mode end-to-end:
- Login → 3 roles → dashboard, loans, lands, settings, AI, OCR pages render
- Create loan → appears in list (LN-2026-001 created via test)
- Create land → appears in list (LD-008 created via test)
- 3 themes สลับได้, 3 ภาษาเปลี่ยน label, drag-drop ทำงาน, popover unread filter ทำงาน
- Settings → AI & OCR Models / Custom Fields panels load ไม่ error

⚠️ ต้องตั้งเองก่อนใช้จริง (รายละเอียดใน `GETTING_STARTED.md`):
- รัน migrations 0001–0013 ใน Supabase Studio
- ใส่ `SUPABASE_URL` + `SUPABASE_ANON_KEY` ใน `prototype/config.js`
- สมัครคนแรก → auto admin
- (Optional) `docker compose up` backend + `OPENROUTER_API_KEY` สำหรับ AI/OCR
- (Optional) Cloudflare Tunnel สำหรับ public access

## Real Supabase wiring status (2026-05-17)

✅ Applied migrations `0001…0013` to the Pi5 Supabase database via Postgres pooler (`umbrel.local:5433`) after fixing `0004_loans.sql` generated-column syntax.

✅ Verification after migration:
- 15 business tables present
- RLS enabled on 15 public tables
- 33 public RLS policies
- `documents` Storage bucket present
- seed demo data present (`loans=7`, `lands=7`)

✅ Filled `prototype/config.js` with `SUPABASE_URL=http://umbrel.local:8000` + browser-safe `ANON_KEY` only. No `SERVICE_ROLE` key was put in frontend code.

✅ Real auth smoke test passed:
- temporary signup through the web UI succeeded
- first profile became `admin` via `0003_profiles.sql` trigger
- dashboard, loans list, lands list, and Settings → AI & OCR Models loaded in Supabase mode
- temporary test user was deleted afterward, leaving `auth.users=0`, `profiles=0`; the real first account can still become admin

✅ Demo smoke still passed from a temporary demo-mode copy:
- `[sb] DEMO mode` logged
- demo admin login worked
- create loan produced `LN-2026-001`
- create land produced `LD-008`

✅ Production backend deploy via Pi5 Portainer is now live:
- real owner/admin account exists and has role `admin`
- webapp stack `sunday-estate` deploys from private GitHub repo through Portainer repository mode using a read-only GitHub token
- FastAPI + nginx are reachable at `http://umbrel.local:8090`
- `http://umbrel.local:8090/api/health` returns `{"status":"ok","service":"sunday-estate-api"}`
- OpenRouter model cache was synced into `or_model_cache` (`356` models, `28` free, `7` free vision) and `app_settings` points to cache-valid free models

✅ Deployment fixes committed to webapp `main` after Portainer errors:
- `4ebe39d fix: register FastAPI rate limiter` — fixed `se-fastapi` unhealthy by setting `app.state.limiter`
- `07b5faf fix: avoid nginx port 8080 conflict` — changed nginx host port to `NGINX_PORT=8090`
- `93c3840 fix: bake nginx config into image` — removed fragile bind mount for `deploy/nginx/nginx.conf`

✅ Production UI fully verified (2026-05-17 session 2):
- Login page renders correctly (Google OAuth + Email, 3 themes, 3 ภาษา, security badge)
- Login as admin (`aase7en@sunday-estate.com`) → Dashboard loads with real data (KPI widgets, bar chart, portfolio donut, contract table)
- Settings → AI & OCR Models: model list loads from cache correctly
- **Bug found & fixed**: `ดึงรายการใหม่` (sync from OpenRouter) failed with `"Invalid token: The specified alg value is not allowed"` — Supabase Pi5 uses **ES256** (EC P-256 via JWKS), not HS256. Fixed in `backend/core/auth.py` (commit `501c6c7`): fetch JWKS from `<SUPABASE_URL>/auth/v1/.well-known/jwks.json`, decode with algorithm from JWK, fallback to HS256.
- After redeploy: sync succeeded, model list refreshed from OpenRouter (new `openai/gpt-oss-120b:free` appeared)
- AI Chat tested: question "มีสัญญากี่ฉบับในระบบ?" → correct answer "7 ฉบับ" (matches seed data) ✅
- OCR UI renders (page accessible); full OCR test requires a real document image

⚠️ Still pending:
- optional Cloudflare Tunnel public access

---

## Claude handoff prompt (2026-05-17 session 2 — production verified)

Paste this into Claude if continuing from here:

```text
อ่าน CLAUDE.md และ wiki/synthesis/sunday-estate-webapp.md ก่อนเริ่มเสมอ.

Sunday Estate webapp — fully verified production state (2026-05-17):
- Wiki: /Users/aase7en/Desktop/InW-Wiki
- Webapp repo: /Users/aase7en/Desktop/sunday-estate-webapp
- Solo workflow: main only, no branch, no PR.
- Pi5 Supabase: http://umbrel.local:8000, stack supabasepi5. Do not touch Umbrel/Bitcoin/Postgres 5432.
- Webapp Portainer stack: sunday-estate
- Production URL: http://umbrel.local:8090
- Admin login: aase7en@sunday-estate.com (email/password via Supabase)

Everything verified and working:
- Production UI: login page, dashboard (real data), all sidebar pages render
- JWT: Supabase Pi5 uses ES256 (JWKS). Fixed in backend/core/auth.py (commit 501c6c7).
  Backend now fetches JWKS from <SUPABASE_URL>/auth/v1/.well-known/jwks.json (lru_cache).
- Settings → AI & OCR Models: model cache loads, "ดึงรายการใหม่" sync works
- AI Chat: end-to-end via OpenRouter, tested and correct ("7 สัญญา" matched seed data)
- Current models: Chat=deepseek/deepseek-v4-flash:free, OCR=google/gemma-4-31b-it:free

Next tasks (choose one):
A) Cloudflare Tunnel: `cloudflared tunnel create sunday-estate` → bind domain → `docker compose --profile public up -d cloudflared`
B) Test OCR: go to OCR เอกสาร page, upload a real Thai document image, verify JSON extraction
C) Real data: replace seed data with actual Sunday Estate loan/land records
D) New feature on the webapp

No code changes needed unless user picks a specific task.
```

## Future fields to consider (`metadata` JSONB — ไม่ต้องคิดตอนนี้)

- **Loans**: `credit_score`, `legal_status`, `insurance_policy`, `co_signer`, `redemption_history[]`, `previous_loans[]`
- **Lands**: `zoning`, `soil_type`, `utilities {water,electric,sewer,internet}`, `construction_permits[]`, `environmental_assessment`, `tax_history[]`
- **Profiles**: `two_factor_enabled`, `login_history[]`, `api_tokens[]`, `kyc_status`
- **Documents**: `version_history[]`, `signing_status` (DocuSign), `legal_review_status`
- **Analytics tables** (future): `saved_reports`, `custom_kpis`, `scheduled_exports`

---

## Notification roadmap

- Phase 1 (done): in-app popover เท่านั้น
- Phase 6+: Telegram Bot + SMS (ThaiBulkSMS/Twilio) + Email (Resend free 3K/month) + per-user opt-in `notification_channels` table

---

## Open Issues (2026-05-18)

> Synced จาก `session-memory.md` — อัปเดตเมื่อ TODO เสร็จหรือเปลี่ยนสถานะ

| # | Task | Priority | Notes |
|---|------|----------|-------|
| 1 | **Cloudflare Tunnel** — `cloudflared tunnel create sunday-estate` + bind domain + `docker compose --profile public up -d cloudflared` | 🟡 Medium | ทำให้ public access ได้จากนอก LAN |
| 2 | **Pi5 redeploy commit `1e8147c`** (Portainer Re-pull + Redeploy) + hard refresh + verify 14 ปุ่มตาม [[sunday-estate-frontend-qa-2026-05-18]] + OCR PDF editable fields | 🔴 High | frontend batch fix ยังไม่ถูก deploy |
| 3 | **Pi5 git pull webapp** + Portainer "Pull and redeploy" stack `sunday-estate` (commit `73860a0`) → verify `curl http://umbrel.local:8090/api/health` | 🔴 High | email-validator fix ยังไม่ถูก deploy |
| 4 | **ตรวจ `SUPABASE_SECRET_KEY`** (service_role) ใน Portainer stack `sunday-estate` env — ให้ `/api/admin/invite` ทำงาน | 🟡 Medium | ต้องใส่ service_role key ใน Portainer env |

---

## Pi5 Deployment Checklist

### วิธี redeploy ผ่าน Portainer (ทุกครั้งที่ push commit ใหม่)

```bash
# 1. ตรวจก่อน
curl http://umbrel.local:8090/api/health
# → {"status":"ok","service":"sunday-estate-api"}

# 2. บน Pi5 Portainer (http://umbrel.local:9000)
#    Stacks → sunday-estate → "Pull and redeploy"
#    (Portainer ดึง commit ล่าสุดจาก GitHub repo อัตโนมัติ)

# 3. ตรวจหลัง deploy
curl http://umbrel.local:8090/api/health
# hard refresh browser: Cmd+Shift+R (Mac) / Ctrl+Shift+R (Win)
```

### ตรวจ env ใน Portainer stack `sunday-estate`

| Variable | ต้องมี | หมายเหตุ |
|----------|--------|---------|
| `SUPABASE_URL` | `http://umbrel.local:8000` | Kong gateway |
| `SUPABASE_ANON_KEY` | ✅ | browser-safe |
| `SUPABASE_SECRET_KEY` | ✅ service_role key | backend only — ห้าม expose frontend |
| `OPENROUTER_API_KEY` | ✅ | AI/OCR routing |
| `NGINX_PORT` | `8090` | avoid conflict |

### Cloudflare Tunnel setup (ยังไม่ได้ทำ)

```bash
# บนเครื่อง local หรือ Pi5
cloudflared tunnel login
cloudflared tunnel create sunday-estate
# → จด Tunnel ID ที่ได้

# แก้ deploy/cloudflared/config.example.yml
# ใส่ tunnel: <TUNNEL_ID> + credentials-file path
# hostname: sunday-estate.<your-domain>.com → http://nginx:80

# รัน public profile
docker compose --profile public up -d cloudflared
```

---

## Related wiki pages

- [[ai-tools/openrouter-claude-code]] — OpenRouter free models, model selection patterns
- [[synthesis/appsheet-to-webapp-pi5]] — prior wiki note on Pi5 self-hosted webapp architecture
- [[sources/umbrel-pi5-setup]] — Pi5 Umbrel / Portainer setup
- [[concepts/ai-tools/session-setup]] — Pi5 git redirect (`.git` outside Drive) — prerequisite
