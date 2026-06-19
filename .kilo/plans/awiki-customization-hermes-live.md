# A-Wiki Customization Plan — Hermes Integration + Live Dashboard v3

**วันที่**: 2026-06-20  
**ผู้จัดทำ**: Kilo AI (Plan Mode)  
**สถานะ**: ✅ ตัดสินใจแล้ว — พร้อม implement

---

## ภาพรวม

แผนนี้ครอบคลุมความต้องการ 10 ข้อ ใช้แนวทาง **Progressive Enhancement** — ต่อยอดจากของที่มี เปลี่ยนน้อยที่สุดแต่ได้ผลมากที่สุด

---

## ✅ Decisions Made

| # | Question | Decision |
|---|----------|----------|
| 1 | Admin key gate | **Dashboard UI password** — เพิ่ม login page/password gate ใน Settings |
| 2 | Agent types config | **แยก `agent-registry.json`** — standalone, clear separation |
| 3 | Hermes scheduler | **cron + Bash wrapper** — zero dependency |
| 4 | Chat storage | **Persist `.tmp/chat-log.jsonl`** — same pattern as event log |
| 5 | Drag-and-drop library | **SortableJS CDN** — mobile-friendly, less code |

---

## 📦 Requirement Mapping

| # | ความต้องการ | Approach |
|---|------------|----------|
| 1 | Hook ลด token/cost, ป้องกัน workflow หลุด | `check_token_waste.py` hook + cron audit script |
| 2 | Chat + file upload ใน A-Wiki Live | SSE-based chat endpoint + drag-drop upload |
| 3 | 2 themes: เขียวขาว และ ดำนีออน | CSS custom properties toggle (ต่อยอดจาก dark/light) |
| 4 | Workflow tree animation แบบมินิมัล | Particle flow SVG (ที่มีอยู่แล้ว) → refine to minimal |
| 5 | Drag-and-drop agent ordering + API key per agent | SortableJS ใน Settings → POST `/api/agent-order` |
| 6 | Scan benchmark + task schedule ผ่าน Hermes | `model-capability-scout.py` → cron via Bash wrapper |
| 7 | Hermes บน Raspberry Pi 5 + A-Wiki Live chat + Telegram | Wiki doc + Docker compose + integration guide |
| 8 | Docker บน Pi 5 + old projects + Supabase | Audit existing Dockerfiles + Supabase schema check |
| 9 | API key gate: free-only without admin password | Dashboard UI password → `check_apikey.py` enhancement |
| 10 | Agent types (12 types) + drag-and-drop + effort config | Agent registry JSON + SortableJS agent chain UI |

---

## รายละเอียดแต่ละข้อ

### 1. Token/Cost Reduction Hook + Workflow Guard

**สิ่งที่ต้องสร้าง/แก้ไข**:
- ไฟล์ใหม่: `scripts/hooks/check_token_waste.py` — PreToolUse hook ที่ monitor:
  - consecutive read-only tool calls (Read/Glob/Grep > 10 ครั้งไม่มี Write → ปิด context ก่อน)
  - large file reads (>2000 lines) → suggest delegate
  - context window usage alert
- ไฟล์ใหม่: `scripts/cron-audit.sh` — ใช้ cron รายวัน audit:
  - `.tmp/live-events.jsonl` → สรุป cost/delegation pattern
  - log ไป `.tmp/cost-audit-YYYY-MM-DD.json`
- แก้ไข: `scripts/hooks_runner.py` — register `check_token_waste`
- แก้ไข: `.claude/settings.json` / `.codex/hooks.json` — register new hook

**เหตุผล**: ใช้ pattern เดียวกับ hooks ที่มีอยู่ (stdin JSON → exit code 0/2)

---

### 2. Chat + File Upload in A-Wiki Live

**สิ่งที่ต้องสร้าง/แก้ไข**:
- แก้ไข: `scripts/live-dashboard/server.py` — เพิ่ม endpoints:
  - `POST /api/chat` — ส่งข้อความ → log event → broadcast via SSE
  - `POST /api/upload` — รับ multipart file → save to `.tmp/uploads/`
  - `GET /api/uploads/<id>` — serve uploaded file
- แก้ไข: `scripts/live-dashboard/live-dashboard.html`:
  - Chat panel (slide-over หรือ tab ขวาล่าง) — รองรับ Markdown + file preview
  - File upload drag-drop zone
  - SSE event type `chat_message` และ `file_uploaded`
- ไฟล์ใหม่: `.tmp/uploads/.gitkeep`

**เหตุผล**: SSE infrastructure มีอยู่แล้ว — chat/upload เป็นแค่ event type ใหม่ + UI component
**Chat storage**: Persist `.tmp/chat-log.jsonl` (same pattern as event log)

---

### 3. Two Themes: Green-White และ Black-Neon

**สิ่งที่ต้องแก้ไข**:
- แก้ไข: `scripts/live-dashboard/live-dashboard.html` — CSS:
  - Replace `[data-theme="light"]` → `[data-theme="green-white"]`
  - Replace `[data-theme="dark"]` → `[data-theme="black-neon"]`
  - Green-White palette: `--bg:#f0faf5`, `--a0:#16a34a`, `--a1:#4ade80`, `--s0:#ffffff`, etc.
  - Black-Neon palette: `--bg:#05050a`, `--a0:#00ff88`, `--a1:#00ffcc`, `--t0:#e0f0e0`, `--s0:#0a0a14`, etc.
  - ปรับ `toggleTheme()` สลับระหว่างสองธีม
  - localStorage key `dashboard-theme` → `green-white`/`black-neon`
  - Theme toggle icon เปลี่ยนตามธีม

**เหตุผล**: ต่อยอดจาก custom property system ที่มีอยู่ — แค่เปลี่ยน color palette

---

### 4. Minimal Workflow Tree Animation

**สิ่งที่ต้องแก้ไข**:
- แก้ไข: `scripts/live-dashboard/live-dashboard.html` — Flow view:
  - Refine particle system: ลดความถี่ลง, ใช้เส้นเรียบ (bezier curve ตรง)
  - animation timing สอดคล้องกับ real event flow
  - Agent → Agent arrows แสดงทิศทางข้อมูล (ไม่ใช่แค่ Origin → Station)
  - เพิ่ม edge label บอก event type (`spawn`, `delegate`, `result`)
  - Remove redundant/high-frequency particles

**เหตุผล**: Particle engine มีอยู่แล้วใน `lf()`, `fAct()`, `pL()` — แค่ปรับให้ workflow-aware

---

### 5. Drag-and-Drop Agent Ordering + API Key Per Agent

**สิ่งที่ต้องสร้าง/แก้ไข**:
- ไฟล์ใหม่: `.tmp/agent-config.json` (gitignored)
- แก้ไข: `scripts/live-dashboard/server.py`:
  - `GET /api/agents` — ส่ง agent list รวม order, effort, api_key status
  - `POST /api/agents` — บันทึก agent order + api keys
  - `POST /api/agents/reorder` — update order ล้วนๆ
- แก้ไข: `scripts/live-dashboard/live-dashboard.html`:
  - Settings → Agent Chain tab (เพิ่มจาก Models/API Keys)
  - SortableJS CDN (`https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js`)
  - Agent card: icon, name, type selector (12 types), effort slider
  - API key per agent: `key_env` field

**เหตุผล**: Settings panel architecture มีอยู่แล้ว — แค่เพิ่ม pane ใหม่ + SortableJS

---

### 6. Benchmark Scan + Hermes Scheduler

**สิ่งที่ต้องสร้าง/แก้ไข**:
- ไฟล์ใหม่: `scripts/cron-benchmark-scan.sh` — Bash wrapper ที่:
  1. เรียก `python3 scripts/model-capability-scout.py --refresh-all`
  2. เรียก `python3 scripts/batch/scout.py --refresh`
  3. เรียก `python3 scripts/batch/scout.py --propose`
  4. สรุปผล → log `.tmp/benchmark-YYYY-MM-DD.json`
  5. Optional: ส่งผลทาง Telegram
- แก้ไข: `scripts/live-dashboard/server.py` — endpoint `POST /api/benchmark/run`
- เอกสาร: `docs/runbooks/benchmark-cron-schedule.md`

**หมายเหตุ**: ใช้ **system cron + Bash wrapper** (ไม่ต้องติดตั้ง Hermes)

---

### 7. Hermes on Raspberry Pi 5 + Telegram Integration

**สิ่งที่ต้องสร้าง**: ไฟล์เอกสาร (ไม่แก้ code, เป็นการตรวจสอบ)
- ไฟล์ใหม่: `docs/runbooks/hermes-raspberry-pi5.md`:
  - Hermes installation on ARM64
  - Docker compose config
  - Telegram bot setup
  - Performance notes (RAM/CPU on RPi 5 8GB/16GB)
  - A-Wiki Live integration (dashboard client on RPi)
- แก้ไข: `wiki/entities/ai-tools/hermes-agent.md` — add RPi5 section

---

### 8. Docker on Pi 5 + Old Projects + Supabase Audit

**สิ่งที่ต้องสร้าง**: ไฟล์ตรวจสอบ (audit)
- ไฟล์ใหม่: `docs/runbooks/rpi5-docker-audit.md`
  - Docker compatibility on ARM64
  - Multiarch image check
  - Performance benchmarks
- ไฟล์ใหม่: `docs/runbooks/supabase-legacy-audit.md`
  - รายการโครงการเก่าที่ใช้ Supabase
  - Connection secrets in `drive/.secrets`
  - Data migration notes for RPi5

---

### 9. API Key Gate — Dashboard UI Password

**สิ่งที่ต้องแก้ไข**:
- ไฟล์ใหม่: `scripts/set-admin-password.py` — CLI tool สำหรับ set/reset password
  - เขียน bcrypt hash ไป `.tmp/admin-password.hash`
- แก้ไข: `scripts/hooks/check_apikey.py`:
  - เช็ค `.tmp/admin-password.hash` existence
  - ถ้าไม่มี hash → force FREE-ONLY mode (ALL paid models disabled)
  - ถ้ามี hash → check session token (dashboard)
- แก้ไข: `scripts/live-dashboard/server.py`:
  - Settings → Admin tab → password field
  - `POST /api/admin/auth` — verify password → set session cookie
  - `GET /api/admin/status` — check if authenticated
  - ถ้าไม่ authenticated → show warning + block paid models
- แก้ไข: `scripts/delegate.sh` — `force_free` mode

**Flow**:
1. First run: `python3 scripts/set-admin-password.py` → prompt for password → save hash
2. Dashboard → Admin tab → enter password → `POST /api/admin/auth` → session cookie
3. ถ้า authenticated → paid models unlock
4. ถ้าไม่ → `AWIKI_DISABLE_*=1` for all paid providers

---

### 10. Agent Types Registry + Drag-and-Drop + Effort Config

**12 Agent types**:

| Type | Role | Default Effort |
|------|------|----------------|
| plan | วางแผนงาน | 80 |
| architect | ออกแบบระบบ | 90 |
| ask | ตอบคำถาม | 30 |
| code | เขียนโค้ด | 70 |
| code-reviewer | review โค้ด | 60 |
| code-simplifier | simplify code | 50 |
| code-skeptic | ตรวจสอบข้อผิดพลาด | 40 |
| debug | debug bug | 85 |
| documentation-specialist | เขียน doc | 50 |
| frontend-specialist | frontend dev | 75 |
| orchestrator | orchestrate agents | 95 |
| test-engineer | เขียน test | 70 |

**สิ่งที่ต้องสร้าง/แก้ไข**:
- ไฟล์ใหม่: `scripts/live-dashboard/agent-registry.json` (tracked) — schema + defaults
- ไฟล์ใหม่: `scripts/agent-config.schema.json`
- แก้ไข: `scripts/live-dashboard/server.py`:
  - `GET /api/agents/types` — registry + defaults
  - `POST /api/agents/effort` — adjust per agent
  - Agent chain CRUD
- แก้ไข: `scripts/live-dashboard/live-dashboard.html`:
  - Settings → Agent Chain tab
  - SortableJS agent list with drag handles
  - Effort slider (0-100) per agent
  - Visual chain flow preview

---

## 📁 Files Changed Summary

### New files (14)
1. `scripts/hooks/check_token_waste.py`
2. `scripts/cron-audit.sh`
3. `scripts/cron-benchmark-scan.sh`
4. `scripts/set-admin-password.py`
5. `.tmp/uploads/.gitkeep`
6. `scripts/live-dashboard/agent-registry.json`
7. `scripts/agent-config.schema.json`
8. `docs/runbooks/hermes-raspberry-pi5.md`
9. `docs/runbooks/rpi5-docker-audit.md`
10. `docs/runbooks/supabase-legacy-audit.md`
11. `docs/runbooks/benchmark-cron-schedule.md`

### Modified files (7)
1. `scripts/live-dashboard/server.py` (+chat, upload, agents, auth, benchmark endpoints)
2. `scripts/live-dashboard/live-dashboard.html` (themes, chat, drag-drop, agent chain UI, admin auth)
3. `scripts/hooks/check_apikey.py` (admin password gate)
4. `scripts/delegate.sh` (force_free mode)
5. `scripts/hooks_runner.py` (register new hook)
6. `wiki/entities/ai-tools/hermes-agent.md` (Pi 5 section)
7. `.claude/settings.json` / `.codex/hooks.json` (register check_token_waste)

---

## 🧮 Implementation Order (Dependency-Aware)

```
Phase 1: Foundation (items 1, 3)
  ├── 1. Token waste hook + cron audit script (no dependency)
  └── 3. Green-white + black-neon themes (no dependency)

Phase 2: Core Features (items 9, 10, 5)
  ├── 9. Admin password gate (requires server modification)
  ├── 10. Agent types registry (standalone JSON schema)
  └── 5. Drag-and-drop agent ordering (requires 10 for agent types list)

Phase 3: UI Enhancement (items 2, 4)
  ├── 2. Chat + file upload panel (requires server + SSE)
  └── 4. Minimal workflow animation (requires existing Flow view)

Phase 4: Deploy & Docs (items 6, 7, 8)
  ├── 6. Benchmark cron + Bash wrapper (standalone scripts)
  ├── 7. Hermes on Pi 5 docs (research + doc only)
  └── 8. Docker/Pi 5 + Supabase audit (research + doc only)
```

---

## 📐 Architecture Notes

- **Hooks pattern**: stdin JSON → exit 0 (pass) / exit 2 (block)
- **SSE events**: append JSON to `.tmp/live-events.jsonl` → dashboard reads via EventSource
- **Config storage**: `.tmp/` (gitignored) สำหรับ runtime config, `scripts/live-dashboard/` สำหรับ tracked JSON schema
- **Secrets**: `drive/.secrets` + `.tmp/live-dashboard-keys.env` (gitignored)
- **Themes**: CSS custom properties + `localStorage` persistence
- **Admin auth**: bcrypt hash → session cookie (no full login system needed)

---

## 🚨 Risks / Notes

1. **check_token_waste hook** → ต้องระวัง false positive (งาน legitimate ที่ต้องอ่านเยอะ). เสนอ allowlist pattern
2. **Dashboard admin password** → ใช้ simple cookie ไม่ใช่ JWT/OAuth — พอสำหรับ local dev
3. **Agent types** → 12 types เป็น initial set, สามารถเพิ่ม schema ได้ในภายหลัง
4. **Pi 5 Docker** → บาง image อาจไม่มี ARM64 build → ต้อง rebuild หรือใช้ alternative
