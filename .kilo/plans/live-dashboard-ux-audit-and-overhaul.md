# A-Wiki Live Dashboard — UX/UI Audit + Overhaul Plan

> **Scope**: Full audit + phased implementation plan + tests/Definition-of-Done for `scripts/live-dashboard/live-dashboard.html`.
> **Direction**: Shift from the current "deep-space neon" demo aesthetic to the **clean, Grafana-grade operator console** defined in `docs/design/dashboard-design-system.md`.
> **Priority axes**: (1) Operator value / data-viz · (2) Accessibility & robustness · (3) Visual polish & consistency — **all three**.
> **Target user**: Thai-first reader · desktop-first operator (Work PC) · monitoring swarm activity, cost tier, hook health, and model routing in real time.

---

## 0. Method & Evidence Base

This audit is grounded in a full read of the current implementation, not heuristics:

- `scripts/live-dashboard/live-dashboard.html` — **1074 lines / 70.3 KB** (the entire CSS 1–399, body markup 400–545, JS 547–1074).
- `docs/design/dashboard-design-system.md` — canonical tokens + 10-dimension targets + anti-patterns + DoD.
- `scripts/live-dashboard/README.md` — endpoints, event schema, settings/key model.
- `skills/render-html/fixtures/live-dashboard.json` — sample event stream.
- `tests/test_live_dashboard_html.py` — 8-component + size/contract guard tests.

Each finding cites `file:line` evidence so an implementer (human or AI) can navigate directly.

---

## 1. Executive Summary

The dashboard is **technically rich** (live SSE, 3 visualization modes, real model/key/capability config) but is **aesthetically and ergonomically misaligned** with its own design system and its stated "operator-first" principle. It currently behaves more like a **demo/showpiece** than a **monitoring console**:

1. **Decorative noise dominates durable signal** — nebula, 70 twinkling stars, 14 ambient floating "thoughts", pipe particles, ~11 concurrent animation loops. These are anti-patterns the design system explicitly bans ("glass morphism without purpose", "AI demo whitespace").
2. **It fails its own size contract** — 70.3 KB vs the 60 KB limit enforced by `test_file_under_60kb` (the test is currently red).
3. **Operator-critical state is poorly surfaced** — failures, cost, and routing rationale are transient (≤2.4 s) or buried in a flat 120-row, unfilterable event log.
4. **Accessibility is far below the 9/10 target** — emoji-as-icon, disabled-color timestamps (~2.8:1 contrast), no focus-visible rings, no focus trap / Esc in modal, no ARIA on custom toggles.
5. **The implementation has drifted from its own design tokens** — the "deep-space" theme overrides the cleaner elevation/text system in `dashboard-design-system.md`.

**Verdict**: keep the data contracts and the 3-view concept; **subtract** the decoration, **promote** operator signal, **harden** accessibility and edge states.

---

## 2. Current-State Assessment (what works — preserve these)

| Strength | Evidence |
|---|---|
| Live, robust SSE pipeline with auto-reconnect + offline overlay | `live-dashboard.html:880-888`, `:290-300` |
| Three genuinely different views (Flow particle hub-and-spoke · Gantt lanes · vis-network graph) | `:136-247`, `:800-876` |
| Real settings surface: model toggle + `model_id` edit + capability badges + key status | `:1009-1056`, README "Settings panel" |
| Cost-first routing logic exists server-side (paid can't surpass free) | README "Capability-based routing" |
| `prefers-reduced-motion` block already present (animation kill-switch) | `:386-393` |
| Idempotent, PID-guarded daemon; idle auto-stop | `dashboard-ensure.sh`, README |
| Good radii/spacing token foundation already declared in `:root` | `:8-33` |

These are the load-bearing assets. The overhaul **must not break** the SSE/API/event-schema contracts (listed in §7).

---

## 3. Audit Findings

Severity legend: **🔴 Critical** (breaks contract / blocks operator) · **🟠 High** (major friction) · **🟡 Medium** · **🔵 Low/polish**.

### A. Operator value & data visualization

| ID | Severity | Finding | Evidence | Impact |
|---|---|---|---|---|
| A1 | 🔴 | **No persistent failure surfacing.** Hook blocks + `delegate_fail` appear only as: a red hook badge (auto-removed at 8 items), a red thought bubble (~2.4 s), a red event row (scrolls out of a 120-cap list). No failure KPI, no errors panel, no filter. | `:917-923`, `:947-952`, `:970` | Operator's #1 question ("what failed?") is unanswerable at a glance. Violates Principle #1 "operator-first". |
| A2 | 🔴 | **Cost tier is nearly invisible.** Principle #2 ("cost tier visible at all times") is served by a 6 px sliver + tiny label, no KPI tile, no cumulative `$` estimate, no free-vs-paid ratio. | `:432-436`, `:369-376` | Cost discipline — the dashboard's reason for existing — is easy to miss. |
| A3 | 🟠 | **Event Log is a flat, lossy, unfilterable stream.** Newest-on-top, capped 120, silently dropped, no grouping/filter/search/severity/pause/export. | `:962-971`, `:257-277` | Debugging a blocked hook means scrolling a flat list; history vanishes silently. |
| A4 | 🟠 | **Routing rationale is invisible.** `delegate.sh` ranks models by `(cost_rank ASC, capability_score DESC)` but the UI never shows *why* a model is ranked where it is, nor which free model beat which paid one. | README "Capability-based routing"; capability badges `:1033` | "Cost-first" is asserted, not demonstrated; trust gap. |
| A5 | 🟠 | **Capability scores are opaque.** Raw 0–100 numbers (SWE/Term/Repo/reason/speed) with no legend, benchmark source, or scale reference; `.hi` flips at an undocumented ≥60. | `:1032-1034`, `:342-344` | "reason 72" is meaningless without a reference. |
| A6 | 🟡 | **Default view is the least informative at rest.** Flow view shows origin + empty-state text + ambient thoughts when idle, while the genuinely useful Event Log is shrunken to ~24 vw. | `:449-466`, `:106-108` | Landing surface wastes the operator's first 5 seconds. |
| A7 | 🟡 | **Client state not replayed on refresh.** Reload zeroes hook/event/model KPIs and the event timeline; only `backlog_complete` re-renders lanes/flow (`:894`). | `:894`, boot `:1067-1071` | Refresh destroys the impression of history the UI implies. |
| A8 | 🔵 | **Workflow tabs are false affordances.** `Session/Plan/Swarm/Cost` light up on events but clicking does nothing — status indicators styled as tabs. | `:414-419`, `:913-916` (only `hotWf`, no click handler) | Misleads users into expecting a filter. |

### B. Accessibility & robustness

| ID | Severity | Finding | Evidence | Impact |
|---|---|---|---|---|
| B1 | 🔴 | **Timestamps use disabled-level color.** `.ev-time` → `--text-disabled` `#475569` on `--elev-0` ≈ **2.8:1** (fails 4.5:1). Timestamps are critical data. | `:272` `color:var(--text-disabled)`; token `:19` | Critical data unreadable for low-vision; fails WCAG AA. |
| B2 | 🟠 | **Emoji used as the entire icon system.** Header tabs, view buttons, station icons, event icons, settings all use emoji — no `aria-label`, lost to screen readers, copy/paste, colorblind users. Anti-pattern: "Generic emoji icons in header (use SVG or remove)". | `:415-418`, `:444-446`, `:972-973` | Fails the design-system anti-pattern list; a11y gap. |
| B3 | 🟠 | **No focus-visible rings / no keyboard path for modal.** `*{margin:0;padding:0}` reset with no `:focus-visible` restoration; settings slide-over has no focus trap and no Escape-to-close. | `:34`, absent focus styles, `:503-505` backdrop only | Keyboard users can't navigate or escape the modal; fails Principle target a11y 9/10. |
| B4 | 🟠 | **Custom toggles lack accessible labels.** `.glow-toggle` checkbox has no `<label>` text / `aria-label`; AT announces only "checkbox". | `:1036-1037`, `:330-336` | Screen-reader users can't tell which model they're toggling. |
| B5 | 🟡 | **Graph view is a silent single point of failure.** `vis-network` loads from `unpkg` CDN; if blocked/offline, Graph silently never initializes (`initGraph` guards `window.vis` but shows nothing). | `:395`, `:857-864` | "Zero-dep, single-file" claim broken for one view; no fallback state. |
| B6 | 🟡 | **Per-frame DOM thrash.** Particle loop rebuilds `particleG.innerHTML=''` + N circle nodes each frame (`:720-728`); lanes rebuild all rows on a 500 ms RAF loop while active (`:838`). | `:710-734`, `:812-839` | Risk on the stated low-end "Work PC" target. |
| B7 | 🔵 | **Locale inconsistency in timestamps.** `toLocaleTimeString('th')` can render Thai digits, inconsistent with the mono "data" font expectation. | `:823`, `:966` | Scannability/copy-paste friction. |
| B8 | 🔵 | **No `aria-live` for state changes.** Failures/cost-tier changes are visual-only; screen readers get no announcement. | throughout event handlers | a11y gap for dynamic content. |

### C. Visual polish & consistency

| ID | Severity | Finding | Evidence | Impact |
|---|---|---|---|---|
| C1 | 🔴 | **Implementation diverged from its own design system.** Deep-space palette (`--space-*`, nebula, stars) overrides the cleaner tokens; e.g. `--text-tertiary #7c8aa5` vs doc `#64748b`; `--elev-2 #0b0b1d` vs doc `#14142a`. | `:9-19` vs `dashboard-design-system.md:24-60` | The doc and the product disagree; redesign target is unverifiable. |
| C2 | 🟠 | **~11 concurrent always-on animation systems.** Stars + nebula drift + origin rings + origin spin + pipe particles + thoughts + tier shimmer + lane shimmer + glow-divider sweep + brand gradient-shift + caret + fade-cycle. | `:41-103`, `:155-203`, `:370-384` | Animations no longer signal change; constant motion undermines scannability ("density without clutter" violated). |
| C3 | 🟠 | **Purely decorative "thoughts" layer.** Ambient phrases ("monitoring the swarm…", "Iron Laws enforced") spawn every ~5 s when idle, capped at 14 — zero information value, pure noise competing with real data. | `:739-784`, `AMBIENT_POOL :739` | Directly contradicts Principle #1. |
| C4 | 🟡 | **Glow is the default, so it signals nothing.** Brand, stats, stations, pipes, thoughts, toggles all glow; anti-pattern: "Drop shadows on every element". | `:28-29`, `:88`, `:159`, `:181` | Emphasis hierarchy collapses; nothing reads as "important". |
| C5 | 🟡 | **Thai/English mixed without rules.** Tabs/stats in English; empty states/notes/help/toasts in Thai. | `:415-425` vs `:463`, `:513`, `:525-541` | "Thai-readable" principle undermined by inconsistent zones. |
| C6 | 🔵 | **60 KB contract already breached.** 70.3 KB → `test_file_under_60kb` is red. Decoration is the bulk. | `live-dashboard.html` (70.3 KB), `test_live_dashboard_html.py:32-34` | Definition-of-Done failure; blocks clean CI. |

---

## 4. Design Inconsistencies (token-level)

| Token | CSS value | Design-system value | Fix |
|---|---|---|---|
| `--text-tertiary` | `#7c8aa5` | `#64748b` | adopt doc value |
| `--elev-0` | `#03030a` (`--space-0`) | `#06060d` | adopt doc value |
| `--elev-1` | `#070713` | `#0c0c18` | adopt doc value |
| `--elev-2` | `#0b0b1d` | `#14142a` | adopt doc value |
| `--elev-3` | `#11112a` | `#1e1e3a` | adopt doc value |
| Glow tokens | `--glow-cyan/-gold/-violet` (3) | single `--shadow-glow` | collapse to one purposeful glow |
| Decoration | nebula + stars (≈70 nodes) | none | remove |

Net effect: **delete `--space-*`, `#nebula`, `#stars`, and the `--glow-*` triplet; adopt the documented elevation + shadow system verbatim.**

---

## 5. Recommendations (brainstormed, prioritized)

### 5.1 Operator value / data-viz
- **R-A1 Persistent failure center.** Add a **Failures/Blocks KPI tile** (red) + a **collapsible Errors rail** that retains all `result==block` / `delegate_fail` with timestamp, hook/model, and reason (not auto-purged). Make it the loudest element when non-zero.
- **R-A2 Promote cost to a first-class KPI.** Cost-tier tile (L-1→L4 with color), cumulative `$` estimate (from `route_plan.est_cost`), and a free-vs-paid usage ratio derived from `delegate_done` events.
- **R-A3 Make the Event Log queryable.** Severity filter (all/blocks/fails/cost/delegate), free-text search, "group by model", pause-on-hover, and a "keep last N with overflow → 'N older' expander" instead of silent drop. Export current view to clipboard/JSON.
- **R-A4 Show routing rationale inline.** On each delegation, surface the rank position + the cost-class note ("free class", "paid class — cannot surpass free") + the deciding capability dimension. Tooltip/expand on the model station.
- **R-A5 Capability legend.** Render scores on a 0–100 micro-bar with benchmark source label and a "good/strong" threshold documented in the legend; hover shows the leaderboard family.
- **R-A6 Reconsider the default landing surface.** Default to a **Summary view**: KPI strip (incl. cost + failures) + live Event Log as the hero, with Flow/Timeline as secondary "live activity" visualizations. Operators get value in the first second.
- **R-A7 Replay client state on load.** On `backlog_complete`, also restore hook/event KPIs and re-render the Event Log from the backlog (server already tails `.tmp/live-events.jsonl`), so refresh is non-destructive.
- **R-A8 Make workflow tabs real filters or restyle them.** Either clicking a tab filters the Event Log (true affordance), or convert them to a passive "activity ribbon" with no tab chrome.

### 5.2 Accessibility & robustness
- **R-B1 Fix timestamp contrast.** Use `--text-secondary` (≥4.5:1) for `.ev-time`; reserve `--text-disabled` strictly for disabled UI.
- **R-B2 SVG icon system.** Replace all functional emoji with inline SVGs (status: pass/block/warn; role: primary/architect/executioner/tool; actions: settings/clear/retry) with `aria-hidden` + adjacent text labels.
- **R-B3 Keyboard & focus.** Add `:focus-visible` rings (brand-glow outline) on every interactive control; trap focus in the settings modal; add `Escape` to close; move focus into the modal on open and restore on close.
- **R-B4 Label the toggles.** Give each `.glow-toggle` an accessible name (visible `<span class="sr-only">Enable {model}</span>` or `aria-label`).
- **R-B5 Make Graph view resilient.** Show an explicit "Graph unavailable offline" state if `window.vis` is missing; vendor `vis-network` locally (or gate the view behind successful load) to restore the zero-dep claim.
- **R-B6 Stop per-frame DOM thrash.** Pool particle/lanes DOM nodes (reuse elements, toggle `hidden`) instead of `innerHTML=''` rebuilds; cap by time budget, not just count.
- **R-B7 Normalize timestamps.** Render HH:MM:SS with ASCII digits + `lang`/`aria-label` full timestamp.
- **R-B8 `aria-live="polite"` region** for failures and tier changes so AT users get announcements.

### 5.3 Visual polish & consistency
- **R-C1 Token reconciliation.** Adopt `dashboard-design-system.md` tokens verbatim; remove `--space-*`, nebula, stars, and the extra `--glow-*` set.
- **R-C2 Animation-as-signal discipline.** Keep motion only for **state transitions** (a delegation starts/ends, a hook blocks, a counter ticks). Remove all always-on ambient loops (nebula drift, starfield, ambient thoughts, brand gradient-shift, glow-divider sweep, idle origin rings).
- **R-C3 Remove the ambient "thoughts" layer entirely** (or convert to an optional "verbose" mode). It is the single biggest noise/cost contributor.
- **R-C4 Restore emphasis hierarchy.** Reserve `--shadow-glow`/glow for **active** states only; idle cards stay flat (matches the design-system "Glassmorphism … purposeful: signals live/active" note).
- **R-C5 Language policy.** Define zones: **data labels/timestamps/identifiers in English mono** (operator data), **prose/help/toasts in Thai**; apply consistently and document it.
- **R-C6 Get under 60 KB.** Removing decoration + collapsing tokens + SVG icon set (vs emoji) is expected to bring the file back under the contract limit; verify with the existing test.

---

## 6. Phased Implementation Plan

Each phase ends with green tests and a commit (`type(scope): …` to `main`, per AGENTS.md). TDD per Iron Law #1 — failing test first.

### Phase 0 — Reconcile tokens + size (unblocks the contract)
- Adopt documented elevation/text/shadow tokens; delete `--space-*`, `#nebula`, `#stars`, `--glow-*` triplet (R-C1).
- **Failing test first**: extend `test_live_dashboard_html.py` — assert no `--space-` / `#nebula` / `#stars` references; assert `:root` declares the documented `--elev-*` and `--text-tertiary:#64748b`; assert `< 60 KB`.
- DoD: `test_file_under_60kb` green; token-drift tests green.

### Phase 1 — Subtract decoration (R-C2, R-C3, R-C4)
- Remove ambient thoughts engine + `AMBIENT_POOL` + `scheduleAmbient`; convert thoughts to opt-in "verbose" mode (off by default).
- Remove always-on loops: nebula-drift, starfield gen, brand gradient-shift, glow-divider sweep, idle origin rings.
- Keep transition-only motion (counter tick, station activate/done/fail, lane shimmer **only while active**, pipe particles **only while a delegation is active**).
- DoD: `test_prefers_reduced_motion_honored` still green; new test asserts no `@keyframes` runs `infinite` on non-status elements.

### Phase 2 — Operator signal (R-A1, R-A2, R-A6)
- Add **Failures/Blocks** KPI tile + Errors rail (persistent). Add **Cost** tile (tier + cumulative `$` + free/paid ratio).
- Add **Summary** view as the new default; demote Flow/Timeline/Graph to secondary tabs.
- **Failing test first**: assert `#kpi-fail`, `#kpi-cost`, `#errors-rail`, `#view-summary` exist; assert a `delegate_fail`/`block` increments the failures tile and appends to the rail (DOM-simulated event test).
- DoD: failures + cost remain visible after the transient animations end.

### Phase 3 — Event Log power tools (R-A3, R-A7)
- Severity filter, search, group-by-model, pause-on-hover, overflow expander, export.
- Replay Event Log + KPIs from backlog on `backlog_complete`.
- **Failing test first**: assert filter/search controls exist; assert `backlog_complete` repopulates counters.
- DoD: refresh is non-destructive; a 500-row stream doesn't silently lose blocks.

### Phase 4 — Routing rationale + capability legend (R-A4, R-A5)
- Show rank/cost-class on delegations; capability scores as 0–100 micro-bars with source + threshold legend.
- **Failing test first**: assert rank/cost-class rendering hook exists; assert capability legend present.

### Phase 5 — Accessibility hardening (R-B1 → R-B4, R-B8)
- Timestamp contrast; SVG icon system with labels; `:focus-visible`; modal focus-trap + `Esc` + focus management; `aria-live` region.
- **Failing test first**: assert no functional emoji in header/view/action controls; assert `.ev-time` color is not `--text-disabled`; assert `:focus-visible` rule present; assert settings has `Esc` handler + focusable container.
- DoD: axe-core / keyboard-only manual pass; contrast ≥ 4.5:1 on all data text.

### Phase 6 — Robustness + polish (R-B5, R-B6, R-B7, R-A8, R-C5)
- Graph offline state + local `vis-network` (or gated load); DOM pooling; ASCII timestamps; language-zone policy; make workflow tabs real filters or restyle as activity ribbon.
- DoD: Graph shows a real state when offline; no per-frame `innerHTML=''` rebuilds.

### Phase 7 — Validation
1. `python -m pytest tests/test_live_dashboard_html.py tests/test_live_dashboard_graph.py tests/test_live_dashboard_events.py tests/test_dashboard_capabilities.py -q` → green.
2. `python -c "import ast; ast.parse(open('scripts/live-dashboard/server.py').read())"` → ok.
3. Manual: start dashboard → Summary loads with cost+failures; trigger a `delegate.sh` → see station activate then complete; trigger a block → failures tile + Errors rail light and **persist**; reload → state restored.
4. Keyboard-only + screen-reader spot check; axe-core clean.
5. `grep -c "primary-card\|connector-svg\|model-grid"` → 0 (preserved contract).

---

## 7. Contracts to preserve (do NOT break)

Implementers must keep these intact — other systems and tests depend on them:

- **SSE**: `GET /events`; event types `session_start, hook_check, cost_declare, delegate_start, delegate_done, delegate_fail, route_plan, graph_update, backlog_complete, log_cleared, config_update`.
- **Fetch**: `GET /api/graph {nodes,edges,parallel_count,active_agents}` · `GET/POST /api/models` · `GET/POST /api/keys` · `GET /api/capabilities` · `GET /clear`.
- **Dead-ref guard**: `primary-card|connector-svg|model-grid` must stay absent.
- **Animation-component guard** (`test_live_dashboard_html.py`): the 8 components + `prefers-reduced-motion` must remain (they map to **transition** motion, not ambient — Phase 1 preserves them by relocating, not deleting).
- **Settings/key model**: keys write to `.tmp/live-dashboard-keys.env` + best-effort `drive/.secrets`; never the repo. (Iron Law #6 alignment, README §"Key storage".)

---

## 8. Updated Definition of Done (aligned to `dashboard-design-system.md`)

- [ ] All CSS uses tokens; **no hardcoded hex outside `:root`**; token values match the doc.
- [ ] `grep -c "primary-card\|connector-svg\|model-grid"` = 0.
- [ ] HTML `< 60 KB` (`test_file_under_60kb` green).
- [ ] No always-on ambient animation; motion is transition-only; `prefers-reduced-motion` honored.
- [ ] Failures + Cost persist beyond transient animation; both visible in the default Summary view.
- [ ] Data-text contrast ≥ 4.5:1; `:focus-visible` on all controls; modal focus-trap + `Esc`.
- [ ] Functional icons are SVG with labels (no functional emoji).
- [ ] Event Log: filter + search + non-destructive refresh; Errors rail retains blocks/fails.
- [ ] Graph view degrades gracefully when offline.
- [ ] Language zones applied consistently (data = English mono; prose = Thai).
- [ ] All dashboard tests green; manual desktop + mobile breakpoint check.

---

## 9. Target score deltas (from the 10-dimension baseline)

| Dimension | Current | Target | Primary owner |
|---|---|---|---|
| Color consistency | 4 | 9 | Phase 0 (R-C1) |
| Typography hierarchy | 5 | 9 | Phase 0 |
| Spacing rhythm | 4 | 9 | Phase 0 |
| Component consistency | 3 | 9 | Phase 0 + 5 |
| Responsive | 6 | 9 | Phase 6 |
| Dark mode | 7 | 10 | Phase 0 |
| Animation | 5 | 8 | Phase 1 (R-C2) |
| Accessibility | 4 | 9 | Phase 5 |
| Information density | 5 | 9 | Phase 2 + 3 |
| Polish | 4 | 9 | Phase 1 + 6 |

---

## 10. Out of scope / risks

- **Server-side** (`server.py`) changes are **out of scope** unless a Phase needs a new endpoint (e.g., a persistent failures feed). Any such need is flagged as a follow-up, not done silently.
- The current `server.py` has **3 unresolved git-merge-conflict blocks** (per `.kilo/plans/kilo-compatibility-dashboard-overhaul.md` R1) causing a `SyntaxError` — the dashboard cannot run at all until that is fixed. **This is a prerequisite**, tracked separately in that plan; the present audit assumes Phase 0 of *that* plan lands first.
- Deduplicating `skills/ecosystem/` skills, Kilo hook wiring, and global config edits are explicitly out of scope.
- Touching `AGENTS.md` / `CLAUDE.md` is out of scope (Iron Law #5).
