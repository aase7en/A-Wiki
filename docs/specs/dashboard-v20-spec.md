# Dashboard v20 — "Activity Story" Redesign Spec

**Status**: proposed · **Date**: 2026-08-03 · **Author**: zcode (a-loop Phase 1-2)
**ADR**: `decisions/0013-dashboard-v20-activity-story-redesign.md`
**Mockup**: `scripts/live-dashboard/v20-mockup.html` (open in browser)
**Research basis**: Stripe/PostHog/Linear/Vercel/Apple WWDC803/Material 3/Okabe-Ito/NN/g

---

## 🎯 Goal (the user's actual words)

> "ถ้าให้รื้อระบบแสดง animation virtual data ของ A-wiki live ใหม่ทั้งระบบ โดยใช้แนวคิดหลักการประมาณเดิมและการออกแบบแบบใหม่ที่ทำให้ง่ายต่อการใช้งาน สำหรับผู้ใช้ที่ไม่จำเป็นต้องมีความรู้ด้านเทคนิค"

**Translation**: change the dashboard's PRIMARY audience from swarm-operator (engineer) to **non-technical user**, without destroying existing capability (keep behind a "Pro mode" toggle).

---

## 🧠 Design direction (chosen)

**Concept A — Activity Story (Stripe/PostHog-inspired)** — research's #1 recommended pattern.

| Element | Old (v19) | New (v20) |
|---|---|---|
| **Landing view** | Summary (13 tabs visible) | **Home** — 1 plain-language sentence + 4 story tiles + funnel |
| **Hero metric** | none (metrics bar with THROUGHPUT/LATENCY) | **1 sentence**: "AI ช่วยคุณทำงาน N งาน · ประหยัด $X" |
| **Top-level items** | 13 tabs | **5 max** (Home + Pro mode button + Cmd+K + theme + settings) |
| **Data flow viz** | vis-network node-graph + particles | **Horizontal funnel** (Think→Plan→Build→Verify→Ship) |
| **Live activity** | Timeline strip (raw events) | **Stream rows** with data→insight→action inline |
| **Jargon** | MULTI-PROVIDER SWARM, TIER L-1, hook_check | "AI 3 ตัวกำลังทำงาน", "โมเดลฟรี", "ระบบตรวจสอบบล็อก" |
| **Animation** | 17 @keyframes, decorative | **Unified system**: count-up (once), skeleton, stagger, spring 80% |
| **Onboarding** | typed-intro "Monitoring the swarm…" | **Help strip** + plain-language callout |
| **13 old views** | all visible | **hidden behind "Pro mode" toggle** — code unchanged |

---

## 📦 Functional requirements (FR)

### FR-1: New "Home" view as landing default
- `view-home` panel becomes the first child of `#main`
- `setView('home')` is the default call on boot (was `setView('summary')`)
- URL hash `#home` is the new default
- The 13 old view-btns move into a collapsible "Pro mode" section in `#view-toggle-bar`

### FR-2: Plain-language hero
- One sentence: `วันนี้ AI ช่วยคุณทำงานได้ {N} งาน`
- Meta line: `ประหยัด ${X} เทียบกับใช้โมเดลเสียเงิน · ป้องกันความเสี่ยง {R} ครั้ง`
- Count-up animation **once on mount** (cubic-bezier enter, 900ms)
- Updated by SSE events (delegate_done → +1 done, cost_declare → recompute saved, hook_check block → +1 risk)

### FR-3: 4 story tiles (Miller's Law cap)
1. **กำลังทำงาน** (Active) — count = `S.activeCount`; drill → Pro/Flow
2. **ทำเสร็จวันนี้** (Done) — count = `S.delegateFree + S.delegatePaid`; drill → Pro/Timeline
3. **ประหยัดไป** (Saved) — count = computed (paid-tier rate × delegations); drill → Pro/Cost
4. **ป้องกันความเสี่ยง** (Risks) — count = `S.failCount` (hook blocks); drill → Pro/Timeline (filtered)

Each tile: icon (colorblind-safe Okabe-Ito) + big number (count-up) + plain label + 1-sentence explainer + drill-down link.

### FR-4: Horizontal funnel (replaces particle graph as primary)
- 5 stages: Think → Plan → Build → Verify → Ship (matches `wf-tabs` already in HTML)
- Each stage: icon + label + status (done/active/waiting) + count
- Active stage = `var(--brand)` + pulse-ring animation (`@keyframes pulse-ring`)
- Click → drill into corresponding Pro view

### FR-5: Live stream with data→insight→action
- Reuse `pushTimeline()` infrastructure but rewrite rendering
- Each row: avatar (color-coded by model/role) + plain sentence + meta + optional action button
- Block events get `<span class="tag tag-block">บล็อก</span>` + action "ตรวจสอบ →"
- Pass events get `<span class="tag tag-pass">ผ่าน</span>`
- New events animate in with `slide-in` (60ms stagger)

### FR-6: Plain-language translation layer (`src/plainlang.js`, NEW)
- Maps every event type + technical field to a plain-Thai sentence
- `hook_check` → "ระบบตรวจสอบ {ผ่าน/บล็อก/ระวัง} {short_name}"
- `delegate_start` → "{Model} เริ่มงาน: {task}"
- `delegate_done` → "{Model} ทำเสร็จ · {duration}s"
- `cost_declare` → "ใช้โมเดล {tier} สำหรับ {task}"
- `tier L-1` → "โมเดลฟรี", `L4` → "โมเดลหลัก"
- Exposed as `window._plain(ev)` returning `{sentence, meta, action}`

### FR-7: Unified animation system (`styles.css` refactor)
- Collapse 17 @keyframes → **8 intentional keyframes**:
  1. `count-up` (JS-driven, not keyframe — count via rAF)
  2. `fade-up` (hero/tile enter)
  3. `stagger-in` (list cascade)
  4. `slide-in` (stream rows)
  5. `pulse-ring` (active funnel/agent)
  6. `heartbeat` (live-dot)
  7. `skeleton-shimmer` (loading state, replaces spinner)
  8. `badge-in` (kept from v19, used for hook badges)
- Easing: `--ease-standard: cubic-bezier(0.2,0,0,1)` + `--ease-enter: cubic-bezier(0.05,0.7,0.1,1)`
- Durations: `--t-fast:120ms`, `--t-normal:200ms`, `--t-slow:320ms`
- All animations respect `prefers-reduced-motion`

### FR-8: Onboarding (NEW — non-existent in v19)
- Help strip under the stream: "💡 คำแนะนำ: คลิกตัวเลข · ⌘K ค้นหา · Pro mode มุมมองวิศวกร · สีเขียว=สำเร็จ"
- Plain-language callout at bottom: explains what "AI 3 ตัว" and "ป้องกันความเสี่ยง" mean
- Dismissible (localStorage `awiki-onboarded-v20`)

### FR-9: Pro mode toggle
- Header button "⚙ Pro mode" — toggles `body.pro-mode` class
- When on: 13 view-btns visible in `#view-toggle-bar`; Home is just another tab
- When off (default): only Home + Pro-mode button visible in toggle bar
- Persists in localStorage `awiki-pro-mode`

### FR-10: Skeleton loaders
- Replace any spinner with skeleton screen for loads >300ms
- Skeleton = gray block with `skeleton-shimmer` animation
- Used by: tiles while data loads, funnel while graph initializes

---

## 🚫 Non-functional requirements (NFR)

| ID | Requirement | Verification |
|---|---|---|
| NFR-1 | Bundle: `app.min.js` ≤ 280 KB (was 242KB, +Motion One ~22KB, +plainlang ~8KB) | `npm run size` |
| NFR-2 | HTML: `live-dashboard.html` ≤ 78 KB (was 71.8KB, +Home panel +Pro wrapper) | `wc -c` |
| NFR-3 | 0 console errors runtime | Playwright `tests-browser/v20_runtime.py` |
| NFR-4 | All 164 existing tests pass (no regressions in Pro mode) | `pytest tests/test_live_dashboard_html.py` |
| NFR-5 | +12 new v20 tests pass | same pytest run |
| NFR-6 | WCAG AA contrast (Okabe-Ito ≥ 4.5:1 on text) | `axe-core` Playwright |
| NFR-7 | Colorblind-safe: every color state also has icon/label | manual + test |
| NFR-8 | `prefers-reduced-motion` kills all animations | manual + test |
| NFR-9 | Privacy: no `<HOSPITAL>`, no real names, no secrets | `python scripts/check-privacy.py` |
| NFR-10 | Backward-compat: `?view=summary` URL still works (auto-enables Pro mode) | runtime test |

---

## ✅ Acceptance criteria

1. **Default landing** = Home view (not Summary) — verified by hash + DOM check
2. **Hero sentence** updates from SSE: send `delegate_done` event → done count +1 within 200ms
3. **4 tiles** each count-up on mount, each clickable → opens Pro view
4. **Funnel** reflects current lifecycle phase (active stage pulses)
5. **Stream** shows last 8 events with plain-Thai sentences
6. **Pro mode toggle** reveals 13 view-btns, persists across reload
7. **No regressions**: all 164 v19 tests pass
8. **Onboarding** visible on first visit, dismissible, not on second visit

---

## 📦 CHUNK BREAKDOWN (8 chunks — each starts with Iron Law #1 failing test)

### 🟢 CHUNK A20 — Plain-language translation layer [next: B20]
- **New file**: `src/plainlang.js` (~150 lines)
- **Exports**: `window._plain(ev)` → `{sentence, meta, action, tone}`
- **Maps**: all 7 SSE event types + tier (L-1→"โมเดลฟรี") + hook names (check_cost_tier→"ตรวจสอบค่าใช้จ่าย")
- **Iron Law #1 test**: `test_v20_plainlang_maps_all_event_types` — assert every type returns non-empty sentence
- **Size**: ~150 lines

### 🟢 CHUNK B20 — Animation system refactor [next: C20]
- **File**: `styles.css` (consolidate 17 → 8 keyframes), `src/app.js` (add `--ease-enter` token)
- **Drop**: `ripple`, `bounce`, `msgIn` (merged into fade-up), `tab-glow`, `tick-glow`, `origin-ring`, `station-pulse`, `station-flash`, `flow-r`, `bar-pulse`, `caret`, `fade-cycle`, `sim-ring` (9 removed, replaced by 3 generic)
- **Keep/add**: fade-up, stagger-in, slide-in, pulse-ring, heartbeat, skeleton-shimmer, badge-in
- **Iron Law #1 tests**: `test_v20_animation_system_collapses_to_8_or_fewer_keyframes` + `test_v20_easing_tokens_defined`
- **Size**: ~60 line deletions + ~30 additions

### 🟢 CHUNK C20 — Home view panel + landing default [next: D20]
- **File**: `live-dashboard.html` (add `<div id="view-home" class="view-panel">` at top of #main), `src/app.js` (default `setView('home')`, hash routing)
- **HTML**: hero section + 4 tile shells (empty, filled in D20) + funnel shells + stream container
- **Iron Law #1 tests**: `test_v20_home_panel_exists_and_first` + `test_v20_default_view_is_home` + `test_v20_summary_url_enables_pro_mode`
- **Size**: ~80 lines HTML + ~20 lines JS

### 🟢 CHUNK D20 — Hero sentence + 4 tiles (data binding) [next: E20]
- **Files**: `src/home.js` (NEW ~200 lines), `src/app.js` (call `homeMount()` from boot)
- **Logic**: count-up rAF (once), SSE-driven updates (`onDelDone → bumpDone`, `onHook block → bumpRisk`, `onCost → recomputeSaved`)
- **Tiles**: render from state `S`, each tile onclick → `setView('summary', {pro:true})` etc.
- **Iron Law #1 tests**: `test_v20_hero_sentence_present` + `test_v20_four_tiles_present` + `test_v20_countup_function_exists`
- **Size**: ~200 lines new

### 🟢 CHUNK E20 — Funnel + stream rewrite [next: F20]
- **Files**: `src/home.js` (extend), `src/graph.js` (rewrite `pushTimeline` to render to Home stream when `currentView==='home'`)
- **Funnel**: 5 stages, state from `S._wfStage` (already exists in wf-tabs logic), active pulses
- **Stream**: reuse `_plain(ev)` from A20, render avatar + sentence + meta + action
- **Iron Law #1 tests**: `test_v20_funnel_has_5_stages` + `test_v20_stream_uses_plainlang` + `test_v20_block_event_has_action`
- **Size**: ~180 lines

### 🟢 CHUNK F20 — Onboarding + plain-language callout [next: G20]
- **Files**: `live-dashboard.html` (help-strip + callout markup), `src/home.js` (dismiss logic + localStorage)
- **Iron Law #1 tests**: `test_v20_help_strip_present` + `test_v20_callout_present` + `test_v20_onboarding_dismissible`
- **Size**: ~50 lines

### 🟢 CHUNK G20 — Pro mode toggle [next: H20]
- **Files**: `live-dashboard.html` (wrap view-toggle-bar in collapsible, add header button), `src/app.js` (toggle + localStorage), `styles.css` (`.pro-mode` body class hides/shows bar)
- **Iron Law #1 tests**: `test_v20_pro_mode_toggle_present` + `test_v20_pro_mode_hides_old_views_by_default` + `test_v20_pro_mode_persists`
- **Size**: ~70 lines

### 🟢 CHUNK H20 — Verify + ship [done]
- **Files**: `src/app.js` (bump DASHBOARD_VERSION v19→v20), `package.json` (19→20), `README.md` (v20 section), `wiki/context/session-memory.md`
- **Regression**: 164 + 12 = 176 tests pass
- **Runtime**: 0 console errors (Playwright v20_runtime.py)
- **Bundle**: ≤280KB
- **Privacy**: `python scripts/check-privacy.py` clean
- **Visual audit**: re-score (target 9.5+, was 9.3 from v18)

---

## 🚫 Out of scope (v21+)

- Replacing vis-network with custom SVG graph in Pro mode (keep as-is)
- Adding Motion One library (use vanilla rAF + CSS — saves 22KB)
- PWA service worker upgrades
- Localization framework (current = Thai only, that's fine for target)
- Voice/narration (TTS) — consider for accessibility v21
- Mobile gestures (swipe between views)

---

## 🔒 Constraints (from grill + Iron Laws)

1. **Iron Law #1**: failing test first in every chunk
2. **Iron Law #5**: AGENTS.md / CLAUDE.md not touched (no permission)
3. **Iron Law #6**: no real hospital/work names — use placeholders
4. **Iron Law #11**: claim registered `zcode-v20-redesign-*` (4h TTL)
5. **Bundle**: ≤280KB app.min.js (current 242KB + ~35KB new = 277KB)
6. **Backward-compat**: `?view=summary` URL must still work (auto-enables Pro mode)
7. **No Motion One** (saves 22KB, vanilla rAF + CSS sufficient per research)
8. **0 console errors** runtime (Playwright)
9. **prefers-reduced-motion**: all animations honor it
10. **164 existing tests pass** — Pro mode preserves all v19 behavior
