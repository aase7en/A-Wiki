# Plan — A-Wiki Live → "Cyber-Clean Minimalism" (Light, 3-Zone Orchestrator Lab)

> Redesign `scripts/live-dashboard/live-dashboard.html` from the current **dark "Deep-Space Neon"** theme to a **light "Cyber-Clean / High-Tech Lab"** aesthetic with a **3-zone orchestrator layout**, integrating the user's provided design plan — **but mapping every panel onto A-Wiki's REAL data** (no fake NOVITA.AI / KIMI / H100 data).

- **Target file**: `scripts/live-dashboard/live-dashboard.html` (single-file, vanilla HTML/CSS/JS, zero-build, < 60 KB)
- **Server**: `scripts/live-dashboard/server.py` — **untouched** (DOM-agnostic; serves HTML + `/events`, `/api/*`)
- **Tests**: `tests/test_live_dashboard_html.py` (+ graph/events tests) — keep green, add new contracts
- **Docs**: `docs/design/dashboard-design-system.md`, `scripts/live-dashboard/README.md`, `wiki/entities/ai-tools/live-dashboard.md`

---

## 1. Decisions locked (from user Q&A)

| Decision | Choice | Implication |
|----------|--------|-------------|
| Scope | **Full restructure + map real data** | New 3-zone layout; every metric derived from real SSE events. **No fake GPU cluster / single base URL.** |
| Theme | **Light/Dark toggle** (default **Light**) | Add `data-theme` + persist `localStorage`. Reverse design-system.md principle #4 (was dark-native). |
| Typography | **Mono for data + Sans for Thai** | `JetBrains Mono` for metrics/labels/brackets/ASCII; system sans (`-apple-system`) for Thai prose. Preserve Thai readability. |

## 2. Honest data mapping (provided plan → A-Wiki real data)

The user's plan references data A-Wiki does **not** have. This table is the contract for what each panel actually shows:

| Provided plan panel | Provided (fake) data | A-Wiki real mapping | Source |
|---|---|---|---|
| `BASE_URL [ API.NOVITA.AI ]` | single endpoint | `[ MULTI-PROVIDER SWARM ]` + active provider count | `/api/models` enabled set |
| `THROUGHPUT 1,252 TOK/S` | tokens/s (unmeasured) | **events/s** (rolling rate from event timestamps) | client-derived from `/events` |
| `P99 Latency` graph (40 reqs) | per-request latency | **P50/P99 delegation latency** from `delegate_done.duration_ms` (rolling window, sparkline) | client-derived |
| `Uptime 99.9%` | SaaS uptime | **Session/connection uptime** (since `session_start` / SSE open) | client-derived |
| `Total Requests` | API counter | **Total events** counter (existing `s-events`) | existing |
| Orchestrator `ALLOCATED/DURATION/COST` | job budget | Cost-tier progress (L-1→L4) + session duration + tier label | existing `cost_declare` |
| `[ KIMI-K2.5 ]` active model | single model | current/last delegated model in `[ MODEL ]` bracket | `delegate_*` events |
| Subagent cards `SANDBOX/ISOLATION/BILLING` | sandbox runtime | `[ DURATION ] [ COUNT ] [ STATUS ]` real per-model metrics | `delegate_*` events |
| Cluster Node grid `8x H100 / 80GB / NVLink` | GPU hardware | **per-model utilization bars** (delegation share) + real infra footer `LOCAL: MAC MINI M4 · N PROVIDERS · COST-FIRST` | `/api/models` + delegation counts |

**All Zone-1 metrics are computed client-side from the existing event stream — zero server changes.**

## 3. New architecture (3 zones + retained views)

```
┌──────────────────────────────────────────────────────────────────┐
│ HEADER: [ live-pulse ] A-WIKI LIVE   [ SESSION PLAN SWARM COST ]  │  slim brand bar
│        [ hooks ][ models ][ events ][ parallel ]   ⚙ 🗑  ☀/🌙   │  (toggle here)
├──────────────────────────────────────────────────────────────────┤
│ ZONE 1 — GLOBAL METRICS BAR                                       │
│ [ BASE ] MULTI-PROVIDER SWARM · THROUGHPUT · LATENCY P99 ──╲spark │
│   · UPTIME · REQUESTS   (mono, uppercase, bracket labels)         │
├───────────────────────────────┬──────────────────────────────────┤
│ ZONE 2-LEFT — ORCHESTRATOR    │ ZONE 2-CENTER — SUBAGENTS GRID    │
│ [ ORCHESTRATOR ] 🧠 pulse     │ ┌──────────┐ ┌──────────┐         │
│ status: validating…           │ │[AGENT-01]│ │[AGENT-02]│         │
│ active → [ MODEL-NAME ]       │ │●RUNNING  │ │ QUEUED   │         │
│ lifecycle: QUEUED→RUN→DONE    │ │ checklist│ │ checklist│         │
│ ▓▓▓▓░░░░ cost-tier bar        │ │[DUR][CNT]│ │ ...      │         │
│ DURATION · COST tier          │ ├──────────┤ ├──────────┤         │
│                               │ │[AGENT-03]│ │[AGENT-04]│         │
│ [ view: GRID · FLOW · LANE · GRAPH ]                          │  │
├───────────────────────────────┴──────────────────────────────────┤
│ ZONE 3 — RESOURCE MONITOR (real per-model utilization)            │
│ Node/gemini ▓▓▓▓░ 58% · Node/deepseek ▓▓▓▓▓▓ 81% · …             │
│ LOCAL: MAC MINI M4 · N PROVIDERS · COST-FIRST ROUTING            │
└──────────────────────────────────────────────────────────────────┘
└ (side) EVENT LOG retained · (overlay) SETTINGS slide-over retained
```

- **ZONE 2 center defaults to the new Subagents Grid** (model delegation stations as cyber-clean cards).
- **Retained alternate views** (restyled, toggled from the view bar): **Flow** (origin→station pipes+particles, light-styled), **Lane/Timeline** (keeps `lane`+`axis` contract), **Graph** (vis-network).
- **Event Log** stays as a right sidebar (collapses on mobile).
- **Settings slide-over** (Models / API Keys / Help) stays, restyled to light glass; keeps `glow-toggle`, `glass-card`, `backdrop-filter`.

## 4. Token system (light default + dark override)

`:root` = **Light** (default). `[data-theme="dark"]` = retained neon dark.

| Token | Light | Dark |
|---|---|---|
| `--bg` | `#f6f8f7` (off-white) | `#06060d` |
| `--surface` | `#ffffff` (crisp white cards) | `#14142a` |
| `--surface-2` | `#f1f5f4` | `#1e1e3a` |
| `--border` | `#e2e8e4` | `#26265a` |
| `--text` | `#0f172a` (charcoal, high contrast) | `#f1f5f9` |
| `--text-2/--text-3` | `#475569 / #94a3b8` | `#cbd5e1 / #64748b` |
| `--accent` | `#4ADE80` (mint) | `#5eead4` (teal) |
| `--accent-2` | `#A3E635` (lime) | `#fbbf24` (amber) |
| `--ok/--warn/--bad` | `#16a34a / #d97706 / #dc2626` | `#34d399 / #fbbf24 / #f87171` |
| `--glow-bg` | radial lime+mint at corners (very soft) | nebula+stars |
| `--shadow-card` | soft drop shadow `0 4px 14px rgba(0,0,0,.06)` | dark elevation |
| `--font-mono` | `'JetBrains Mono','SF Mono',ui-monospace,monospace` | same |
| `--font-sans` | `-apple-system,'SF Pro Text',system-ui,sans-serif` (Thai) | same |

- Radii: keep 4–8 px (sharp/minimal per plan).
- Fonts loaded from Google Fonts CDN (`JetBrains Mono`) — same single external-CDN pattern as current vis-network; no build step.
- **Aesthetic details**: bracket labels `[ "TEXT" ]`, UPPERCASE metrics, glowing pulse dots for active states, thin black progress bars + shimmer, subtle vector connector lines (node-based feel).

## 5. Test contracts to PRESERVE (existing — must stay green)

From `tests/test_live_dashboard_html.py` (currently **11 pass / 2 fail**). All of these substrings/tokens must remain in the file:

1. No dead refs: `primary-card`, `connector-svg`, `model-grid`
2. **File < 60 KB** (currently 70.9 KB → **must shrink** via leaner rewrite)
3. SSE/API: `/events`, `/api/graph`, `/api/models`, `/api/keys`, `/api/capabilities`, `EventSource`
4. `prefers-reduced-motion` honored
5. Animated Counter: `requestAnimationFrame` + (`data-counter` | `animateCounter`)
6. Glow Line Divider: `glow-divider` + `@keyframes`
7. **Progress Bar + shimmer**: literal `progress-bar` **AND** `shimmer` ← *currently failing; add `progress-bar` literal class*
8. Typed Rotator: `data-typed` | `typedRotator` | `typeRotate`
9. Fade Word Cycle: `fade-cycle` | `fadeWord`
10. Animated Gradient: `gradient-shift` | `animated-gradient`
11. Glow Toggle: `glow-toggle`
12. Glassmorphism: `glass-card` + `backdrop-filter`
13. Branching timeline: `lane` + (`time-axis` | `axis`)

→ Keep all class names verbatim (restyle their visual rules, don't rename).

## 6. New test contracts to ADD (in `test_live_dashboard_html.py`)

- `test_theme_toggle_present`: `data-theme` attribute + light/dark switching JS + `localStorage` persist token.
- `test_three_zones_present`: zone IDs `metrics-bar`, `orchestrator`, `subagents` (grid), `resource-monitor` exist.
- `test_real_data_not_fake`: assert the fake strings `NOVITA`, `KIMI-K2.5`, `H100`, `TOK/S` are **absent** (guards honesty).
- `test_latency_window_logic`: a delegation duration rolling-window helper exists (e.g. `_latency` / `p99` token).

## 7. Documented deviations from the provided plan (and why)

1. **No React / Framer Motion** — A-Wiki dashboard is **single-file, zero-build, < 60 KB, no npm** (design-system.md principle #6; Iron Law: don't bloat the brain). All requested animations (pulse, fade, smooth progress, vector paths) are replicated in **vanilla CSS/JS** (several already exist). Adding a framework would break portability + budget.
2. **No fake GPU/cluster/hardware** — A-Wiki delegates to cloud LLM APIs; there is no local H100 cluster. Zone 3 shows **real per-model utilization** instead (per user's "map real data" choice).
3. **No single `BASE_URL`** — A-Wiki is multi-provider; show `[ MULTI-PROVIDER SWARM ]` + provider count.
4. **Throughput ≠ TOK/S** — tokens aren't measured; show real **events/s** (labeled honestly).
5. **Mono split, not full-mono** — Thai readability preserved (per user choice).
6. **Glassmorphism used purposefully** (light, subtle) — design-system.md anti-pattern warned against *purposeless* glass; this is intentional + tested.

## 8. Implementation chunks (cross-agent handoff: commit each to `main`, push at handoff)

> Per `docs/protocols/cross-agent-plan-handoff.md`. Each chunk = atomic commit `chunk(Rn): … [next: R(n+1)]`.

- **R1 — Tokens + base reset + glow bg** (light default + dark override, fonts, corner radial glow, surfaces, slim header with theme toggle). Structure unchanged; verify all 13 existing contract substrings present + tests run. *Commit.*
- **R2 — Zone 1 Global Metrics Bar** (throughput/latency-p99/uptime/requests client-derived + latency sparkline; bracket/uppercase styling). *Commit.*
- **R3 — Zone 2-Left Orchestrator** (origin as `[ ORCHESTRATOR ]` card, active-model bracket, cost-tier `progress-bar` with `shimmer`, lifecycle, duration/cost). *Commit.*
- **R4 — Zone 2-Center Subagents Grid** (delegation stations as cyber-clean cards w/ checklist + `[ DONE/RUNNING/QUEUED ]` badges + `[ DURATION ][ COUNT ][ STATUS ]`). Restyle Flow/Lane/Graph tabs (light). Keep particle engine (lighter). *Commit.*
- **R5 — Zone 3 Resource Monitor** (per-model/provider utilization bars = real delegation share + real infra footer). Replace fake GPU. *Commit.*
- **R6 — Theme toggle wiring + reduced-motion + a11y polish** (persist pref, `prefers-color-scheme` default, contrast ≥ 4.5:1, focus rings, mobile breakpoints). *Commit.*
- **R7 — Tests + docs** (add new test contracts #6; fix `progress-bar`; update `dashboard-design-system.md`, README, wiki entity; run full `tests/`). *Commit + push.*

## 9. Definition of Done

- [ ] `live-dashboard.html` < 60 KB, light by default, dark toggle works + persists.
- [ ] 3 zones present + every metric traces to real A-Wiki data; fake strings absent.
- [ ] All 13 existing HTML contract tests pass **+** 4 new tests pass (18/18).
- [ ] `prefers-reduced-motion` honored; contrast ≥ 4.5:1; mobile breakpoint OK.
- [ ] No dead DOM refs; all retained class tokens (`glow-divider`, `glass-card`, `glow-toggle`, `fade-cycle`, `data-typed`, `gradient-shift`, `progress-bar`, `shimmer`, `lane`+`axis`, `data-counter`) present.
- [ ] `server.py` untouched (DOM-agnostic); endpoints unchanged.
- [ ] Docs updated: design-system, README, wiki entity.

## 10. Risk & rollback

- **Risk**: heavy rewrite breaks an SSE/event-render path. **Mitigation**: keep event-dispatch switch (`session_start/hook_check/cost_declare/delegate_start|done|fail/graph_update/...`) and `pushTimeline`/`evText`/`evIcon` logic intact; only restyle DOM.
- **Risk**: > 60 KB after adding zones. **Mitigation**: lean shared-token CSS, drop redundant per-component rules; the light theme is inherently leaner than the dark glow stack.
- **Rollback**: single-file change → `git checkout` the file reverts instantly; server unaffected.
- **Fallback file**: `exports/html/live-dashboard.html` is a server fallback — sync at end of R7 (or remove the fallback line if stale).
