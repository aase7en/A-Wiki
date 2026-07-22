# A-Wiki Live Dashboard

Real-time monitor ของ A-Wiki swarm — เห็นว่าใช้ AI ตัวไหน แบ่งงานอะไร อยู่ workflow ไหน
ทำ parallel กี่ model และ hook ตัวไหนทำงาน/บล็อก — แบบ live ผ่าน Server-Sent Events.
รวม **Settings panel** ให้ผู้ใช้เลือก model + ใส่ API key เองได้ และจัดลำดับ model
ตาม **capability** (อ้างอิง leaderboard) โดยยึด cost-first.

รุ่น v2.2 **"Cyber-Clean"**: 3-zone layout, light-first theme + dark toggle, client-derived metrics.

## รัน

```bash
python3 scripts/live-dashboard/server.py        # foreground (Ctrl+C หยุด)
bash scripts/dashboard-ensure.sh                # daemon (idempotent, เปิด browser, idle 30min auto-stop)
bash scripts/dashboard-stop.sh                  # stop daemon
```
เปิด `http://localhost:7790/` ใน browser. Port 7790 (แยกจาก render-html-preview 7788).
มี config ใน `.claude/launch.json` ชื่อ `live-dashboard` ด้วย.

## Auto-start & IDE matrix

A-Wiki เปิด dashboard ให้อัตโนมัติตอนเริ่ม session ผ่าน `session_start.py` hook (`_ensure_dashboard()` →
`dashboard-ensure.sh`, fire-and-forget). `delegate.sh` ก็ ensure ให้ทุกครั้งที่ delegate. idle 30 นาที
ไม่มี SSE client → daemon ปิดเอง (watchdog). guard: `AWIKI_DISABLE_DASHBOARD_AUTOSTART=1`.

| Agent / IDE | Auto-start | กลไก |
|-------------|:----------:|------|
| Claude Code | ✅ | `.claude/settings.json` SessionStart → `session_start.py` |
| Codex | ✅ | `.codex/hooks.json` SessionStart → `session_start.py` |
| Gemini CLI | ✅ | `.gemini/settings.json` SessionStart → `session_start.py` |
| Cline / Cursor / Antigravity | ⚠️ รันเอง | ไม่มีระบบ hook — `bash scripts/dashboard-ensure.sh` ครั้งเดียว (หรือรอ delegation) |

Daemon เขียน PID ที่ `.tmp/live-dashboard.pid`, log ที่ `.tmp/live-dashboard.log`, bind `127.0.0.1`,
มี EADDRINUSE guard (ไม่ทับ process อื่นบน 7790).

## Architecture (3-Zone Layout)

```
┌─ HEADER ───────────────────────────────────────────────────────┐
│ [live-pulse] A-Wiki Live  [SESSION PLAN SWARM COST]  ☀/🌙 ⚙ 🗑│
├─ Z1: METRICS BAR ─────────────────────────────────────────────┤
│ [BASE] MULTI-PROVIDER SWARM · THROUGHPUT 2.1/s · LATENCY 850/  │
│  1200ms · UPTIME 2:30:15 · REQUESTS 142                       │
├─ Z2-LEFT ────────────┬─ Z2-CENTER (SUBAGENTS GRID | FLOW |    │
│                       │  TIMELINE | GRAPH)                     │
│ 🧠 [ORCHESTRATOR]    │ ┌──────────┐ ┌──────────┐              │
│ STATUS: running      │ │[AGENT-01]│ │[AGENT-02]│              │
│ → [ GEMINI ]         │ │●RUNNING  │ │ QUEUED   │              │
│ TIER ▓▓▓▓░░ L-1      │ │[DUR][CNT]│ │ ...      │              │
│ DURATION 2m 30s      │ ├──────────┤ ├──────────┤              │
├─ Z3: RESOURCE MONITOR┴────────────────────────────────────────┤
│ gemini ▓▓▓▓░ 58% · deepseek ▓▓▓▓▓▓ 81% · groq ▓░░░░ 12%      │
│ LOCAL: MAC MINI M4 · 6 PROVIDERS · COST-FIRST ROUTING         │
├─ RECOMMENDATION STRIP ────────────────────────────────────────┤
│ ▌ Monitoring the swarm…  🧬 reason → [Gemini] (reason 85)      │
└───────────────────────────────────────────────────────────────┘
└ (right sidebar) EVENT LOG · (overlay) SETTINGS slide-over
```

### Zones

| Zone | ID | Content |
|------|----|---------|
| Header | `#header` | Brand, live pulse, workflow tabs, stat counters, theme toggle, settings/clear buttons |
| Z1 Metrics Bar | `#metrics-bar` | Real-time client-derived: base provider, throughput (events/s), P50/P99 latency (ms), uptime, total requests |
| Z2-Left Orchestrator | `#orchestrator` | Origin card, status label, active model bracket, cost-tier progress bar with shimmer, duration, view toggle |
| Z2-Center | `#center-area` | Default hook strip + subagents grid; toggleable to Flow / Timeline / Graph. Contains `#flow-panel`, `#timeline-panel`, `#graph-vis` for alternate views |
| Z3 Resource Monitor | `#resource-monitor` | Per-model delegation share bars (hi/md/lo) + infra footer |
| Sidebar | `#sidebar` | Event log (timeline of all SSE events) |
| Settings | `#settings` | Slide-over with Models/API Keys/Help tabs |

### Metric Sources

All Z1 metrics are **client-derived** from the SSE event stream — zero server changes:
- **Throughput**: events/second from rolling 10s window of `_eventTimes`
- **Latency**: P50/P99 from `delegate_done.duration_ms` in a `_lat` array (max 100 samples)
- **Uptime**: from `session_start` timestamp
- **Total requests**: total event counter

### Theme Toggle

- Default **light** theme with `[data-theme="light"]`
- Dark override via `[data-theme="dark"]` CSS custom properties
- Persisted in `localStorage` under key `dashboard-theme`
- Initial default respects `prefers-color-scheme: dark`
- Toggle button in header (`#theme-btn`)

### Views (Z2-Center)

| View | Description | JS Entry |
|------|-------------|----------|
| Grid | Agent cards (default) | `renderSubagents()` |
| Flow | Origin→station pipes + particles | `layoutFlow()` + particle engine |
| Timeline | Branching lanes with time axis | `renderLanes()` + `drawBranchLines()` |
| Graph | vis-network knowledge graph | `initGraph()` + `updateGraph()` |

## Endpoints

| Endpoint | Method | Purpose |
|----------|:------:|---------|
| `/` | GET | Dashboard HTML |
| `/events` | GET | SSE stream (tails `.tmp/live-events.jsonl`) |
| `/clear` | GET | เคลียร์ event log |
| `/status` | GET | JSON status |
| `/api/models` | GET/POST | อ่าน/บันทึก model config |
| `/api/keys` | GET/POST | สถานะ key (set/unset, **ไม่คืนค่า**) / บันทึก key |
| `/api/capabilities` | GET | capability scorecard + `recommended_by_task` |

> Server เป็น `ThreadingHTTPServer` — SSE stream ที่ค้างยาวจะไม่บล็อก `/api/*` calls.

## Settings panel (⚙️ models)

- **Models tab** — toggle เปิด/ปิดแต่ละ model, แก้ `model_id`, ดู capability badge
  (SWE-bench · Terminal-Bench · NL2Repo · reasoning · speed). กด "บันทึก Models" →
  POST `/api/models` → เขียน `.tmp/model-config.json` (gitignored) → มีผลรอบ delegate ถัดไป.
- **API Keys tab** — ใส่ API key ต่อ provider → POST `/api/keys`. ถ้าไม่ตั้งอะไร →
  ใช้ default config (GLM ปิดไว้จนกว่าจะใส่ key).

## Key storage (binding กับ Iron Law #6)

Key ที่ใส่ผ่าน dashboard เก็บที่:
1. `.tmp/live-dashboard-keys.env` (gitignored — `export KEY="..."`, delegate.sh `source` เอง)
2. `drive/.secrets` (best-effort ถ้า `drive/` mount อยู่ — cloud-synced, ไม่ขึ้น git)

**ไม่เคย** เขียน key ลง repo file หรือ `.claude/settings.local.json`. โดน `.tmp/` gitignored
จึงไม่ trip `check_secret_leak` hook (ไม่ stage). delegate.sh `source` keys file นี้อัตโนมัติ.

## Model config schema (`.tmp/model-config.json`)

```json
{ "models": [
  { "id": "zhipu", "name": "GLM 5.2 (Z.ai)", "enabled": false,
    "provider": "zhipu", "key_env": "ZHIPU_API_KEY",
    "model_id": "glm-4.6",
    "api_url": "https://api.z.ai/api/paas/v4/chat/completions" }
]}
```
`enabled:false` → delegate.sh emit `AWIKI_DISABLE_<ID>=1` → engine ตัวนั้นถูกข้าม.
`model_id` แก้ได้ → delegate.sh export ทับ seed (เช่น `ZHIPU_DIRECT_MODEL=glm-5.2`).

## Capability-based routing

`wiki/context/model-capability-scores.json` = scorecard committed (offline-first floor),
keyed by family + `match` substrings, คะแนน 0-100 ต่อ dimension. `scripts/model-capability-scout.py`
refresh best-effort จาก 3 leaderboard (SWE-bench / Terminal-Bench 2.0 / NL2RepoBench) →
`.tmp/model-capability-cache.json`. delegate.sh `_rank_by_capability()` จัดลำดับ engine
ด้วย sort key `(cost_rank ASC, capability_score DESC)` → **paid ห้ามแซง free**; capability
สลับลำดับเฉพาะภายใน cost class. ดู [[zhipu-glm]] · [[model-capability-bench]].

## เพิ่ม model ใหม่

1. Settings → Models → แก้ `model_id` ของ provider ที่มีอยู่ (gemini/deepseek/openrouter/groq/anthropic/zhipu), หรือ
2. แก้ `DEFAULT_MODEL_CONFIG` ใน `server.py` + เพิ่ม `try_<provider>_direct()` ใน `delegate.sh`
   (clone จาก `try_groq_model` ถ้า OpenAI-compatible) + wire ใน `run_tier()`.

## 📦 Dashboard version history (v8–v10)

### 🏗️ v8 — Foundation refactor (esbuild)
HTML/CSS/JS แยกไฟล์: markup อยู่ใน `live-dashboard.html` (markup only), CSS ใน
`styles.css`, JS ใน `src/*.js` (9 ไฟล์) bundle ด้วย esbuild → `app.min.js`. Build:
`cd scripts/live-dashboard && npm run build`. HTML size budget 60KB → markup only.

### ♿ v9 — Accessibility (WCAG AA)
- `.sr-only` + `.sr-only-focusable` + `focus-visible` ring
- `role=tablist/tab` + `aria-selected` + roving `tabindex` + arrow-key nav
- `aria-label` ครบทุก interactive element (static + dynamic)
- focus trap + restore สำหรับ 8 modals
- keyboard nav บน skill cards (arrow/Home/End)
- skip links + screen reader announcements (`#aria-live`) + `prefers-reduced-motion`

### ⚡ v10 — Performance + browser tests (current)
**Goal**: ลด initial paint blocking + ป้องกัน regression ด้วย browser smoke tests.

| Chunk | Feature | Files |
|-------|---------|-------|
| **A10** | CDN scripts `defer` + chart.js lazy-load (removed from `<head>`) | `live-dashboard.html`, `src/analytics.js` |
| **B10** | TTL cache layer (`_ttlCache`) สำหรับ `/api/skills` (60s) + `/api/coverage` (30s) | `src/app.js`, `src/skills.js`, `src/coverage.js`, `src/graph.js` |
| **C10** | `_loaded{}` guard — setView ข้าม heavy-load เมื่อ revisit; particle loop pause เมื่อไม่ใช่ flow view | `src/app.js`, `live-dashboard.html` |
| **D10** | Playwright scaffolding: `@playwright/test`, 5 smoke specs (boot, tabs, skills, keyboard, theme) | `playwright.config.mjs`, `tests-browser/smoke.spec.mjs`, `tests/test_live_dashboard_playwright.py` |
| **E10** | Performance budget specs (LCP/load/DOM/JS eval) + baseline doc | `tests-browser/perf.spec.mjs`, `PERF_BASELINE.md` |
| **F10** | Verify + this changelog | — |

**Install Playwright (optional — dashboard works without it)**:
```bash
cd scripts/live-dashboard
npm install
npx playwright install chromium
npm test              # all specs (smoke + perf)
npm run test:smoke    # just smoke
```

**Why Playwright is optional**: the dashboard is a localhost-served tool; Python
contract tests (`tests/test_live_dashboard_*.py`, 68 tests) guard the API +
markup contracts without a browser. Playwright adds runtime/DOM coverage for
teams that want it — skip if unavailable (pytest wrapper auto-skips).

**Cache invalidation triggers** (B10):
- SSE `registry_update` → invalidate skills + coverage caches
- Inline edit (coverageEditSave, togglePin) → invalidate both caches
- Refresh button on Coverage → `_cacheInvalidate('coverage')` before reload

### 💾 v11 — Backup + Smart Suggestions (current)
**Goal**: localStorage backup/restore (4 chunks) + client-side skill suggestions (2 chunks).

| Chunk | Feature | Files |
|-------|---------|-------|
| **A11** | Backup pane + `exportAllBackup()` — collect 24 awiki-* keys → JSON | `live-dashboard.html`, `src/app.js` |
| **B11** | Import + selective restore — validate schema, per-key checkboxes | `src/app.js` |
| **C11** | Auto-backup every 7 days — `awiki-auto-backups` (max 3 FIFO) | `src/app.js` |
| **D11** | Usage meter + per-key Clear button (reclaim quota) | `src/app.js` |
| **E11** | `smartSuggestions()` — frequency (40%) × recency (30%) × co-occurrence (30%) | `src/skills.js` |
| **F11** | "💡 แนะนำ" chips in discovery bar with "why" tooltip | `src/skills.js` |

**Backup** (Settings → 💾 Backup tab):
- Export: downloads `awiki-backup-YYYYMMDD.json` (version:1 schema, all awiki-* keys)
- Import: validate → selective restore modal (per-key checkboxes, shows จะทับ/ใหม่)
- Auto-backup: weekly snapshot stored in localStorage itself (max 3, FIFO)
- Usage meter: green <60% / yellow <85% / red of 5MB quota
- Per-key 🗑 Clear button reclaims quota granularly

**Smart Suggestions** (Skills tab → discovery bar):
- Scoring: `frequency (30d) × 40 + recency × 30 + co-occurrence_with_last × 30`
- Excludes skills opened in last 24h (user just saw them)
- Returns empty if <5 total opens (no random suggestions without telemetry)
- Chip tooltip: "เปิด N ครั้งใน 30ว · ใช้ร่วมกับล่าสุด N · N วันที่แล้ว"

**Iron Laws**: #1 (pure-function tests for scoring + validation), #6 (backup stays in browser — never disk/repo), #10 (no registry edit)

### 🎨 v12 — Theme Editor + Mobile Responsive (current)
**Goal**: visual theme editor (8 color tokens, 4th "custom" mode) + mobile critical fixes (6 chunks).

| Chunk | Feature | Files |
|-------|---------|-------|
| **A12** | Theme pane + `custom` mode (4th in cycle: auto→dark→green-white→custom) | `live-dashboard.html`, `src/theme.js` |
| **B12** | Color pickers + live preview (8 `<input type=color>` tokens, onchange re-injects `<style>`) | `src/theme.js` |
| **C12** | Theme export/import + 3 preset seeds (Ocean/Sunset/Forest) | `src/theme.js` |
| **D12** | `.view-toggle-bar` horizontal scroll on mobile (12 tabs no longer clip) | `styles.css` |
| **E12** | `#skills-grid` minmax 260→150px + toolbar gap shrink on mobile | `styles.css` |
| **F12** | Modals 95vw + `#skills-detail` 100vw on mobile | `styles.css` |

**Theme Editor** (Settings → 🎨 Theme tab):
- 4 modes: auto (follows OS) / dark / green-white / custom (your colors)
- 8 editable tokens: `--accent-brand`, `--accent-warm`, `--accent-cool`, `--accent-violet`, `--accent-success`, `--accent-danger`, `--elev-0`, `--text-primary`
- Live preview: color picker `onchange` re-injects `<style id=custom-theme-style>` immediately
- Export/import theme JSON, save/load presets
- 3 built-in presets: Ocean (blue), Sunset (warm), Forest (green)

**Mobile Responsive** (`@media(max-width:600px)`):
- `.view-toggle-bar`: `overflow-x:auto` + hidden scrollbar (12 tabs scroll horizontally)
- `#skills-grid`: `minmax(150px,1fr)` (2 cards per row on 375px phones)
- `#skills-toolbar`: tighter gap + `min-width:120px` inputs
- Modals: `max-width:95vw; max-height:90vh`
- `#skills-detail`: `width:100vw` (full-screen drawer on mobile)

### 🎓 v13 — Onboarding + Help Refresh (current)
**Goal**: make dashboard self-explanatory for new users + refresh Help content for v8-v12.

| Chunk | Feature | Files |
|-------|---------|-------|
| **A13** | Help pane refresh — JS-rendered content (พื้นฐาน + ใหม่ใน v10-v12 + Tips) + version badge | `src/app.js` |
| **B13** | First-run toast tour — 7 steps (welcome → Skills → Recommender → Settings → Theme → Backup → Shortcuts) | `src/app.js` |
| **C13** | Dashboard health check — 5 async checks (SSE/API/localStorage/CDN/Playwright) with 5s timeout | `src/app.js` |
| **D13** | "What's new" badge — red dot on Settings cog when version changes | `src/app.js`, `live-dashboard.html` |

**Onboarding** (auto for new users):
- Tour: 7-step overlay with Next/Skip, auto-starts 2.5s after boot (if not completed)
- State: `awiki-tour-completed` + `awiki-tour-step` (resume capable)
- `_tourActive` flag suppresses other toasts during tour
- Re-run: clear `awiki-tour-completed` from localStorage

**Help pane** (Settings → 📖 คู่มือ):
- Refreshed content covering v8-v12 features (backup, theme, mobile, suggestions, performance, Playwright)
- Version badge from `DASHBOARD_VERSION` constant
- Health check button: "🩺 ตรวจสุขภาพ Dashboard" — runs 5 checks, shows ✅/❌/ℹ️ checklist

**What's new badge**:
- Red dot on ⚙️ when `awiki-seen-version` ≠ `DASHBOARD_VERSION`
- Clicking Settings clears the badge

### 📊 v14 — New Visualizations (current)
**Goal**: เพิ่ม 3 visualizations ใหม่ + KPI cards จาก data ที่มีอยู่ (5 chunks).

| Chunk | Feature | Files |
|-------|---------|-------|
| **A14** | Agent capability radar — Chart.js radar, 5 axes (SWE/Term/Repo/Reason/Speed), top 4 families | `src/analytics.js`, `live-dashboard.html` |
| **B14** | Cost projection — linear regression + 7-day forecast (dashed line) + ±20% confidence band | `src/analytics.js`, `live-dashboard.html` |
| **C14** | Skill dependency heatmap — domain × lifecycle_phase matrix, click to filter | `src/skills.js`, `live-dashboard.html` |
| **D14** | Summary KPI cards — 4 clickable cards (skills/health/models/cost) | `src/app.js`, `live-dashboard.html` |

**Agent Capability Radar** (Settings → 🤖 Agents):
- Chart.js radar comparing top 4 model families on 5 capability dimensions
- Fetches `/api/capabilities`, overlaid polygons with distinct colors

**Cost Projection** (💰 Cost tab):
- Linear regression over historical cost data → 7-day forecast
- Solid line = actual, dashed line = forecast, shaded band = ±20% confidence
- Weekly cost estimate in chart title

**Skill Heatmap** (🧩 Skills tab, above walkthroughs):
- Domain × lifecycle phase matrix table
- Cell opacity = skill count (darker = more)
- Click cell → filter skills by domain

**KPI Cards** (📊 Summary tab):
- 4 cards: Total Skills, Avg Health %, Active Models, Weekly Cost
- Click → navigate to related view
- TTL cached (60s) for skills data

### 🔍 v15 — Event Log Power + Chat Persistence (current)
**Goal**: event log search/bookmark/export + chat history ไม่หายเมื่อ refresh (5 chunks).

| Chunk | Feature | Files |
|-------|---------|-------|
| **A15** | Event ring buffer (500 max) + text search (debounced 250ms) | `src/graph.js`, `live-dashboard.html` |
| **B15** | Event bookmark/pin (⭐ persist via `awiki-event-bookmarks`) + filter option | `src/graph.js`, `live-dashboard.html` |
| **C15** | Event log export JSON (`awiki-events-YYYYMMDD-HHmm.json`) | `src/graph.js`, `live-dashboard.html` |
| **D15** | Chat history persistence (`awiki-chat-history`, max 50 msgs) + clear button | `src/chat.js`, `live-dashboard.html` |

**Event Log** (sidebar, right):
- 🔍 Search box: case-insensitive substring filter on event text
- ⭐ Bookmark: click star next to any event — bookmarked rows survive the 120-row DOM cap
- 📥 Export: download all 500 buffered events as JSON (includes bookmark flag)
- Filter dropdown: All / ⭐ Bookmarked / Blocks / Cost / Delegate

**Chat** (💬 Chat tab):
- Messages persist across refresh (max 50, FIFO)
- 🗑 Clear button in input bar (with confirm)
- Boot auto-restores history

### 🔬 v16 — Integration Audit Fixes
**Goal**: dashboard ผ่าน debug-mantra 4-step audit + Playwright runtime check. เน้น "ใช้ได้จริงทั้งระบบ" ไม่ใช่แค่ syntax (5 chunks).

| Chunk | Fix | Files |
|-------|-----|-------|
| **A16** | `subagent_invoke` SSE handler — hook `log_subagent_result.py` ส่ง event ทุกครั้งที่เรียก subagent จริง แต่ client ไม่มี handler (default pushTimeline เท่านั้น). เพิ่ม `onSubagentInvoke()`: bump model KPI + flowComplete + spawn 🤖 thought + failure notification | `src/graph.js` |
| **B16** | vis-network fallback auto-retry — ถ้า user คลิก Graph tab ตอน defer script ยังโหลดไม่เสร็จ เดิมจะติด "Graph unavailable offline" ตลอดไป. เพิ่ม poll 250ms × 10 ครั้ง | `src/graph.js` |
| **C16** | Revive dead writes — `awiki-compare-last` + `WORKSPACE_LAST_KEY` เขียนมาตั้งแต่ v8 แต่ไม่มี reader. เพิ่ม `restoreLastCompare()` + `restoreLastWorkspace()` + badge "● ล่าสุด" ใน workspace list | `src/skills.js`, `src/modals.js` |
| **D16** | Auto-clear sim timers on view switch — `_simTimer` (coverage) + `_wfTimer` (analytics) เดิม clear เฉพาะตอน user กด stop. ถ้าเริ่ม sim แล้ว switch view จะ churn DOM ที่ซ่อนอยู่ตลอด. เพิ่ม guard ใน `setView()` | `src/app.js` |

**Audit methodology** (debug-mantra 4-step + Iron Law #2):
1. Static dead-ref scan — 92 inline handler fns ทั้งหมด resolve ✓
2. Runtime Playwright — 0 console errors / 0 pageerrors / 0 request failures (13 views × 8 settings)
3. localStorage read/write cross-check — 2 dead writes (C16)
4. SSE event-type diff (client handlers vs server emitters) — 1 missing handler (A16)

**Audit artifacts** (gitignored runtime reports):
- `tests-browser/runtime_audit.py` — full Playwright audit driver
- `tests-browser/runtime_audit_live.py` — `_eventLog` ring buffer live check (via `exportEventLog()` API)
- `tests-browser/runtime_audit_subagent.py` — A16 handler verification
- `tests-browser/audit-report.json` — last run output

### 🎨 v17 — Pure Minimal redesign (Linear-style) (current)
**Goal**: visual audit 5/10 → 8.8/10. เอาออกทุก AI-slop pattern (gradient/glass/neon-glow). Pure minimal + Neutral+accent palette. Generated by `design-system` skill (4 chunks + design system docs).

| Chunk | Change | Files |
|-------|--------|-------|
| **A17** | `:root` re-define เป็น 11-step neutral scale + single `--brand` accent. Legacy aliases (`--elev-*`, `--accent-*`, `--text-*`) re-point ที่ neutral scale เก่าใช้ได้. Strip slop: 16 gradient/glass/shadow patterns (header, brand, stat-val, view-btn, glass-card, skill-card, tier-fill, etc) | `styles.css` |
| **B17** | Finish slop removal: `.skill-sim-btn`, `#sim-stage`, `#sim-progress`, 12 neon glow box-shadows, `var(--shadow-glow)` alias | `styles.css` |
| **C17** | Declutter: 22 `rgba(94,234,212,...)` teal refs → `var(--brand-muted)`. Drop `📡` emoji หน้า offline `<h2>`. Header padding tighten | `styles.css`, `live-dashboard.html` |
| **D17** | version bump v16→v17, README v17 section, design artifacts ship | `src/app.js`, `package.json`, `README.md` |

**Design system artifacts** (committed):
- `DESIGN.md` — rationale, principles, audit score targets, component patterns
- `design-system.json` — 11-step neutral scale + accent + status tokens
- `design-preview.html` — self-contained before/after comparison (open in browser)

**Before/After slop counts**:

| Pattern | v16 | v17 |
|---------|-----|-----|
| `linear-gradient()` | 20 | 0 |
| `backdrop-filter:blur()` | 7 | 0 |
| neon glow `box-shadow` | 12+ | 0 |
| `var(--shadow-glow)` refs | many | 0 |
| `rgba(94,234,212,...)` teal | 22+ | 0 |
| `.brand` rainbow text | yes | flat color |
| emoji-prefix headings | 12/12 | reduced (HTML h2 done; JS-rendered in v18) |

**What stayed** (not slop):
- 4 shadow tokens (`--shadow-sm`/`md`/`lg` + `none`)
- 3 motion durations (`--t-fast`/`normal`/`slow`) on single easing curve
- vis-network particle bg in Flow view (content, not decoration)
- Fluid `clamp()` type scale

### ⌨️ v18 — Cmd+K palette upgrade + Polish (current)
**Goal**: design score 8.4 → 9.3+. เคลียร์ backlog 2 จุด (emoji-headings + transition tokens) และอัปเกรด Cmd+K palette (4 chunks).

| Chunk | Change | Files |
|-------|--------|-------|
| **A18** | ลบ emoji prefix 8 `<h5>` headings ใน skill detail panel (📝 📋 💡 📌 🎬 🔗 📋 🔍) — plain text headings ตาม DESIGN.md Typography | `src/skills.js` |
| **B18** | Migrate 26 hardcoded `transition: X .Ys` → `var(--t-fast/normal/slow)` + `--ease`. Hardcoded count 23 → 0 | `styles.css` |
| **C18** | Palette visual minimal: PALETTE_ICONS 🧩🌊📊⌨️ → ◆ ● ◇ geometric shapes (color-coded). Drop `backdrop-filter:blur(3px)` ใน palette-backdrop. palette-row hover → `--brand-muted` + `--t-fast` | `src/modals.js`, `live-dashboard.html`, `styles.css` |
| **D18** | ⌘K hint badge ใน header (Mac=`⌘K`, Win/Linux=`Ctrl K`) + recent commands tracking (`awiki-palette-recent`, max 5 FIFO) | `live-dashboard.html`, `src/modals.js`, `styles.css` |

**Runtime discovery (A-Plan Stage 4)**: ตอนเริ่ม plan ผมรัน Playwright จริง → พบว่า Cmd+K ทำงานอยู่แล้วตั้งแต่ CHUNK EE (แต่ user ไม่รู้). v18 ≠ "เพิ่ม Cmd+K" แต่ = "อัปเกรด Cmd+K ให้ minimal + discoverable + smart".

**Design direction**: A4 Mixed (polish 2 จุด + Cmd+K upgrade). ผ่าน `a-plan` skill 5-stage chain (A-Think → grill-with-docs → spec → mockup → plan-orchestrate).

**Plan artifacts**:
- `decisions/0010-dashboard-v18-cmdk-palette-polish.md` — ADR + glossary
- `docs/specs/dashboard-v18-spec.md` — FR/NFR/AC
- `scripts/live-dashboard/v18-mockup.html` — visual mockup (open in browser)

**Before/After**:

| Metric | v17 | v18 |
|--------|-----|-----|
| Emoji-prefix `<h5>` (skills.js) | 8 | 0 |
| Hardcoded transitions | 23 | 0 |
| Palette icons | emojis | geometric shapes |
| backdrop-filter:blur (palette) | yes | removed |
| ⌘K hint badge | none | header right |
| Recent commands tracking | none | last 5 (localStorage) |

**Known followups (v19+)**:
- 9 emoji-headings ยังอยู่ใน coverage/analytics JS-rendered panels
- inline-style padding (87 border-radius count)
- 5 sibling backdrop-filter:blur ใน compare/workspace/notif/keybind/shortcuts backdrops

## Troubleshooting

- **Dashboard ว่าง/offline overlay** → server ยังไม่รัน. รัน `python3 scripts/live-dashboard/server.py`.
- **GLM ไม่ทำงาน** → ใส่ ZHIPU_API_KEY (Settings → API Keys) + เปิด toggle GLM + Save.
  ตรวจ endpoint Z.ai สากล `api.z.ai` (ไม่ใช่ `bigmodel.cn` ของ mainland).
- **capability ไม่อัปเดต** → `python3 scripts/model-capability-scout.py` (best-effort; ถ้า leaderboard
  parse ไม่ได้จะคง committed score). `--offline` = ใช้ committed อย่างเดียว.
