# Plan — A-Wiki × Kilo Code Compatibility + Live Dashboard Overhaul

> Goal: make the A-Wiki experience under **Kilo Code Extension** as smooth as under **Claude Code** — fix root-cause breakage, parallel-subagent visibility, cross-platform auto-start, skill overlap, and fully redesign the Live Dashboard with the requested professional animations.

## Decisions confirmed with user
- **Skill de-dup**: Non-destructive + Kilo wiring (expose canonical skills via `kilo.jsonc` `skills.paths`; no file moves/deletes).
- **Kilo auto-start**: VS Code `runOn: folderOpen` task **+** existing `delegate.sh` lazy-start.
- **Dashboard UI**: **Full redesign** of `scripts/live-dashboard/live-dashboard.html`.

---

## Root-cause summary (verified)
| # | Finding | Evidence | Impact |
|---|---------|----------|--------|
| R1 | `scripts/live-dashboard/server.py` has **3 unresolved git merge-conflict blocks** (lines 29-33, 43-120, 649-657) → `SyntaxError` | `ast.parse` fails line 33; `tests/test_live_dashboard_graph.py` collection error | **Dashboard cannot start on ANY platform** (Claude/Codex/Kilo). This is the #1 cause of "กระตุก/สะดุด". |
| R2 | HTML JS references removed DOM (`primary-card`, `connector-zone`, `connector-svg`, `model-grid`) after vis-network migration | `live-dashboard.html:1308,1432-1435,1504-1505`; body only has `#graph-vis` | `onSessionStart()`/`updateConnections()` throw silently; dead code |
| R3 | Graph `parallel_count` always 0 from server | `server.py:148` `_process_graph_event` handles only `agent_spawn/agent_done`; `delegate.sh` emits only `delegate_start/done/fail` | Parallel subagents never render in the graph |
| R4 | Kilo has **no hooks system** | `kilo-config` skill; `kilo.jsonc` empty | No SessionStart auto-start in Kilo |
| R5 | Kilo sees only `.kilo/skills/` (38 generic skills) — A-Wiki skills invisible | `skills/` & `agent-skills/` not in Kilo discovery paths | debug-mantra/scrutinize/delegation/ingest-source unavailable in Kilo |
| R6 | `.kilo/agents/code-skeptic.md` references `.kilocode/**/*.md` (non-existent) | lines 31, 55 (also mirrored in global `~/.config/kilo/kilo.jsonc`) | Dead enforcement; project uses `.kilo/` |
| R7 | `tests/test_dashboard_autostart.py` references removed API (`maybe_autostart_dashboard`, `_port_open`, `AWIKI_DASHBOARD_AUTOSTART`) | vs `session_start.py` has `_ensure_dashboard` / `AWIKI_DISABLE_DASHBOARD_AUTOSTART` | Autostart tests fail |
| R8 | `scripts/ecosystem/link-my-skills.sh` ECC whitelist 12/16 stale; `skills/README.md` incomplete | explore report | Skill linking partially broken |

---

## Phase 0 — Unblock: fix `server.py` merge conflicts (prerequisite for everything)
**File:** `scripts/live-dashboard/server.py`

Resolve all 3 blocks by **keeping the merged (4ec6b650) side** (it is the feature-complete version; the rest of the file — daemon, `/api/models`, `/api/keys`, `/api/capabilities`, PID/keys/TASK_DIMENSION — depends on its symbols). The HEAD side's `ensure_dashboard_html()` render-html auto-render is dropped; the merged side serves the source HTML directly with a fallback.

- **Block 1 (imports, ~29-33):** keep `import signal` + `import socket` (needed by daemon/port logic).
- **Block 2 (~43-120):** keep merged side: `DASHBOARD_HTML = scripts/live-dashboard/live-dashboard.html`, `DASHBOARD_HTML_FALLBACK = exports/html/...`, `MODEL_CONFIG_FILE`, `DASHBOARD_KEYS_FILE`, `CAPABILITY_*`, `PID_FILE`, `DAEMON_LOG`, `IDLE_TTL_S`, `TASK_DIMENSION`, `DEFAULT_MODEL_CONFIG`, `_clients = []`.
- **Block 3 (~649-657):** keep merged `_serve_html` (serve source or fallback).
- Remove all `<<<<<<<`, `=======`, `>>>>>>>` markers.

**Verify:** `python3 -c "import ast; ast.parse(open('scripts/live-dashboard/server.py').read())"` succeeds; `python3 scripts/live-dashboard/server.py --help` runs.

---

## Phase 1 — Parallel subagent correctness (user point 2) — TDD
**Goal:** make the dashboard graph + `parallel_count` reflect real delegations across all platforms.

### 1a. Server-side: derive agent activity from `delegate_*` events
**File:** `scripts/live-dashboard/server.py` (`_process_graph_event`, ~:148)
- Add handling so a `delegate_start` synthesizes an **agent node** keyed by a stable id (e.g. `agent:<model>`) with `role="executioner"` (or `model`'s implied role), `model=<model>`, status `active`, and adds it to `_active_agents`. `delegate_done` → status `completed`, remove from `_active_agents`. `delegate_fail` → status `failed`, remove.
- This makes `parallel_count = len(_active_agents)` accurate for delegations, populates agent nodes in `/api/graph`, and keeps the existing `agent_spawn` path working (tests in `test_live_dashboard_graph.py` must still pass).
- Also surface `delegate_start`'s `task` and `prompt_preview`, and `delegate_done`'s `duration_ms`, on the node for the UI.

### 1b. Race mode emits distinct parallel agents (optional polish)
**File:** `scripts/swarm/delegate.sh` (`run_race`, ~:449)
- Before backgrounding each racer, emit `agent_spawn` with a per-racer `agent_id` (e.g. `racer-<i>-<model>`), `agent_role=executioner`, `model=<model>`. On winner selection, emit `agent_done` for losers (killed) + winner. This gives the graph visually distinct parallel racers (not required for correctness — 1a already covers it).

### 1c. Tests (Iron Law #1 — write failing tests first)
**File:** `tests/test_live_dashboard_graph.py` (extend)
- `test_delegate_start_creates_agent_node_and_active`: feed `delegate_start` → assert agent node exists, `status==active`, `parallel_count>=1`, id in `active_agents`.
- `test_delegate_done_removes_from_parallel`: feed `delegate_start`→`delegate_done` → `status==completed`, not in `active_agents`.
- `test_delegate_fail_marks_failed`: feed `delegate_start`→`delegate_fail` → `status==failed`, not in `active_agents`.
- Keep all existing `agent_spawn`/`task_*`/`tool_cluster` tests green.

---

## Phase 2 — Cross-platform auto-start (user point 3)
**Target parity:** Claude (✓ hooks today) · Codex (✓ hooks today) · **Kilo (✗ → add)**.

### 2a. Reconcile stale autostart tests (Iron Law #1)
**File:** `tests/test_dashboard_autostart.py`
- Rewrite tests to match the **actual** `session_start.py` API: `_ensure_dashboard()` (no repo arg), env guard `AWIKI_DISABLE_DASHBOARD_AUTOSTART`, and that it spawns `dashboard-ensure.sh` via `subprocess.Popen` (start_new_session) when not running. Use `monkeypatch` on `subprocess.Popen` + a PID-file/port sentinel.
- Add a test that `dashboard-ensure.sh` is idempotent (no duplicate spawn when PID file valid) — mirror the script's PID check at `dashboard-ensure.sh:12-18`.

### 2b. Kilo auto-start via VS Code folderOpen task
**File:** `.vscode/tasks.json`
- Add task `"A-Wiki: Live Dashboard (auto)"` with `"runOn": "folderOpen"`, `command: "bash scripts/dashboard-ensure.sh"`, `presentation: {reveal:"silent", panel:"shared", close:true}`, `problemMatcher: []`. This fires when the workspace opens in VS Code (where Kilo runs), mirroring Claude's SessionStart. (One-time VS Code "allow folder-open tasks" prompt is expected.)
- Keep the existing manual `"A-Wiki: Open Live Dashboard"` task.

### 2c. Kilo manual command (fallback / explicit)
**File (new):** `.kilo/command/awiki-dashboard.md`
- Frontmatter `description: Start/stop the A-Wiki Live Dashboard`. Body: instruct to run `bash scripts/dashboard-ensure.sh` (start) / `bash scripts/dashboard-stop.sh` (stop) and open `http://localhost:7790`.

### 2d. Verify Claude & Codex unchanged
- `.claude/settings.json` SessionStart → `session_start.py` (no change).
- `.codex/hooks.json` SessionStart → `session_start.py` (no change).
- Both now actually work once Phase 0 is fixed.

### 2e. Update dashboard help/autostart table
**File:** `scripts/live-dashboard/live-dashboard.html` (help pane) + `docs/protocols/model-switching.md` autostart note: add **Kilo Code (VS Code)** → "✅ auto (folderOpen task)".

---

## Phase 3 — Skill de-dup (non-destructive) + Kilo wiring (user point 1)

### 3a. Expose A-Wiki skills to Kilo
**File:** `.kilo/kilo.jsonc` (currently just `{"$schema":...}`)
- Add `skills.paths` pointing at canonical A-Wiki skill roots so Kilo discovers them:
  `"./agent-skills", "./skills/claude-code", "./skills/engineering", "./skills/productivity", "./skills/delegation", "./skills/wiki", "./skills/research", "./skills/automation", "./skills/domain", "./skills/claude-thai", "./skills/render-html"`.
- Per `kilo-config` skill, `skills/<name>/SKILL.md` is the discovery contract — these dirs satisfy it. This makes debug-mantra, scrutinize, post-mortem, delegation-protocol, ingest-source, lint-wiki, etc. visible in Kilo without moving files.

### 3b. Fix stale `.kilocode` references
**Files:** `.kilo/agents/code-skeptic.md` (lines 31, 55) and the mirrored text in **global** `~/.config/kilo/kilo.jsonc`.
- Replace `.kilocode/**/*.md` → `AGENTS.md` (+ `.kilo/` agents) and the rule list with A-Wiki's actual Iron Laws (raw immutable, no prod code without test, etc.) instead of generic TS/actor-system rules that don't apply to this repo.

### 3c. Reconcile `.kilo/agents/` overlaps with engineering skills
- **code-reviewer.md** (18-line generic stub): trim to a clear, distinct role (PR/diff review) and cross-link `skills/engineering/scrutinize` for systematic review — remove functional duplication.
- **code-skeptic.md**: keep as the aggressive evidence-gatekeeper, but point to `agent-skills/engineering/scrutinize` (Iron-Law-enforcing variant) as the canonical systematic-review skill. Remove the `.kilocode` actor-system rules (3b).
- **code-simplifier.md** (73 lines): verify it's distinct (refactor focus) — leave as-is unless it duplicates scrutinize; if so, narrow scope.

### 3d. Fix broken skill-linking scripts
**File:** `scripts/ecosystem/link-my-skills.sh`
- Update the `ECC_INCLUDE` whitelist to existing ecosystem dirs (replace 12 stale names: `automated-testing`→`automation-audit-ops`, `code-review`→`code-tour`, `continuous-integration`→`content-engine`, `project-planning`→`project-flow-ops`, `python-development`→`python-patterns`, `research-paper`→`research-ops`, `terminal-commands`→`terminal-ops`, remove `bash-scripting/commit-message/markdown/technical-writing/web-development` if no match) so linking actually links.

### 3e. Document canonical skill sources
**File:** `skills/README.md`
- Add a "Canonical source per skill" table; note diverged copies (`skills/engineering` = full content, `agent-skills/engineering` = Iron-Law-enforcing variant) and that `.kilo/skills/` are Kilo-bundled generic skills (Angular/Vercel/dbt). Fix the stale `productivity/excel-generator` path → `domain/excel-generator`.

### 3f. Test (TDD)
**File (new):** `tests/test_kilo_skill_discovery.py`
- Assert `kilo.jsonc` parses as JSONC and `skills.paths` resolves to existing dirs.
- Assert no `.kilocode` references remain in `.kilo/agents/*.md`.
- Assert `link-my-skills.sh` whitelist entries all exist in `skills/ecosystem/`.

---

## Phase 4 — Dashboard full redesign with animations (user point 4)
**File:** `scripts/live-dashboard/live-dashboard.html` (full rewrite, served by `server.py`)

### 4a. Contracts to preserve (do not break)
- SSE: `GET /events`; event types: `session_start, hook_check, cost_declare, delegate_start, delegate_done, delegate_fail, task_start, task_complete, agent_spawn, agent_done, route_plan, graph_update, backlog_complete, log_cleared, config_update`.
- Fetch: `GET /api/graph` `{nodes,edges,parallel_count,active_agents}`, `GET/POST /api/models`, `GET/POST /api/keys`, `GET /api/capabilities`, `GET /clear`.
- Design tokens from `docs/design/dashboard-design-system.md` (elevation, accents, role colors, 8-stop type ramp, 4px spacing, radii, shadows). **No hardcoded hex outside `:root`.**

### 4b. Definition of Done (from design-system.md)
- `grep -c "primary-card|connector-svg|model-grid" live-dashboard.html` = 0
- File size < 60KB (vis-network stays CDN-loaded, not counted)
- All dashboard tests pass (`test_live_dashboard_graph.py`, `test_live_dashboard_events.py`, `test_dashboard_capabilities.py`)
- Accessible: contrast ≥ 4.5:1, focus rings, keyboard nav, `prefers-reduced-motion` honored (animations disable gracefully)

### 4c. Layout — branching timeline (centerpiece)
- **Primary node** (Senior Critic / host agent) on the left as the origin.
- **Branching swimlanes**: each active/completed delegation = a lane branching off the primary over a **time axis** (Gantt-style). Bars represent `delegate_start→done` (green) / `fail` (red) / running (pulsing). Parallel lanes fan out and converge back to primary on completion — "แตกแขนงคล้ายเส้นเวลา".
- Secondary **graph view** (keep vis-network from CDN) for session/task/agent/tool-cluster topology (toggle between Timeline ↔ Graph).
- Right sidebar: live **event timeline** (color-coded by type), header **KPI strip**, bottom **recommendation strip**.

### 4d. The 8 animation components (map to elements)
1. **Animated Counter** — every numeric KPI (`hooks`, `models`, `events`, `parallel`, `tier` L-number) counts up via `requestAnimationFrame` easing (old→new). Respects `prefers-reduced-motion`.
2. **Glow Line Divider** — section separators between KPI strip / timeline / graph: an animated horizontal gradient bar with a traveling glow highlight.
3. **Progress Bar + shimmer overlay** — cost-tier indicator (L-1→L4) and per-delegation progress; a diagonal `::after` shimmer sweeps left→right while active.
4. **Typed Rotator** — the recommendation/intro strip: types a phrase char-by-char, holds, backspaces, advances to the next phrase (loop). e.g. "🧬 reason → DeepSeek R1", "🔍 search → Gemini Flash".
5. **Fade Word Cycle** — status pill word cycles (e.g. validating → delegating → watching) with cross-fade.
6. **Animated Gradient** — header/brand background slowly shifts hue/position (subtle, not "AI purple→cyan"; use teal/amber brand accents).
7. **Glow Toggle** — settings model/key toggles emit a brand-glow when on (leveraging existing `.cfg-slider`).
8. **Glassmorphism Cards** — **active** agent/primary cards use `backdrop-filter: blur()` + translucent elevation bg + 1px inner highlight (purposeful: signals "live/active", per anti-pattern guard). Idle cards stay flat.

### 4e. Accessibility & robustness
- Wrap every `document.getElementById(...)` use in null-guards so missing elements never throw (fixes R2 class of bugs permanently).
- `prefers-reduced-motion: reduce` → disable counter easing, shimmer, gradient shift, typed-rotator (show static text), keep instant updates.
- Keep SSE auto-reconnect + offline overlay (from current impl).

### 4f. Tests (TDD — Iron Law #1)
**File (new):** `tests/test_live_dashboard_html.py`
- Parse `live-dashboard.html`; assert: no `primary-card|connector-svg|model-grid`; size < 60KB; references `/events`, `/api/graph`, `/api/models`, `/api/keys`, `/api/capabilities`; contains the 8 animation markers (e.g. `@keyframes shimmer`, `data-typed`, `class="glass-card"`, etc.); contains `prefers-reduced-motion`.

---

## Phase 5 — Validation
1. `python3 -m pytest tests/test_live_dashboard_graph.py tests/test_live_dashboard_events.py tests/test_dashboard_capabilities.py tests/test_dashboard_autostart.py tests/test_kilo_skill_discovery.py tests/test_live_dashboard_html.py -q` → all green.
2. `python3 -c "import ast; ast.parse(open('scripts/live-dashboard/server.py').read())"` → ok.
3. Manual: `bash scripts/dashboard-ensure.sh` → `http://localhost:7790` loads redesigned UI; run a `bash scripts/swarm/delegate.sh lookup "test"` → see a branching lane appear with counter/progress animations; check `parallel_count>0`.
4. Kilo path: open workspace in VS Code → folderOpen task starts dashboard; `/awiki-dashboard` command works.
5. Grep checks: `grep -rn ".kilocode" .kilo/` → none; `grep -c "primary-card\|connector-svg\|model-grid" scripts/live-dashboard/live-dashboard.html` → 0.

## Iron Laws & guardrails honored
- **#1** failing test first for all new logic (Phases 1c, 2a, 3f, 4f).
- **#5** only edits requested config (`kilo.jsonc`, `.vscode/tasks.json`, `.kilo/agents`, `.kilo/command`, skills/README) — **no AGENTS.md/CLAUDE.md edits**.
- No `raw/` mutation; no secrets touched; dashboard keys stay gitignored in `.tmp/`.
- Commits per sub-step to `main` (no branches/PR).

## Out of scope
- Replicating Claude's `PreToolUse` guardrails (cost-tier, raw-immutable, harness-routing) inside Kilo — Kilo has no hook system; only dashboard auto-start parity is in scope.
- Deduplicating the 232 `skills/ecosystem/` ECC upstream skills.
- Editing global `~/.config/kilo/kilo.jsonc` beyond the `.kilocode` text fix (will note but ask before touching global).
