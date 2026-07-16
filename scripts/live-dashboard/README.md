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

## Troubleshooting

- **Dashboard ว่าง/offline overlay** → server ยังไม่รัน. รัน `python3 scripts/live-dashboard/server.py`.
- **GLM ไม่ทำงาน** → ใส่ ZHIPU_API_KEY (Settings → API Keys) + เปิด toggle GLM + Save.
  ตรวจ endpoint Z.ai สากล `api.z.ai` (ไม่ใช่ `bigmodel.cn` ของ mainland).
- **capability ไม่อัปเดต** → `python3 scripts/model-capability-scout.py` (best-effort; ถ้า leaderboard
  parse ไม่ได้จะคง committed score). `--offline` = ใช้ committed อย่างเดียว.
