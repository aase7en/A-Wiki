# A-Wiki vNext Migration — Baseline (Phase 0)

> Capture date: 2026-08-17 · Executor: ZCode/GLM-5.3 · Branch: `refactor/awiki-kernel-vnext`
> Reference: A-WIKI-MASTER-DEVELOPMENT-PLAN (user-provided, external) §41 Phase 0
> Status: **COMPLETE** — awaiting Architecture Review before Phase 1

## 0. Snapshot

| Item | Value |
|---|---|
| Branch | `refactor/awiki-kernel-vnext` — created from local `main` @ `156a104e`; **auto-rebased onto origin/main `e532d2f0` by external automation at 15:29 +0700 mid-session** (see §8.8 / DISC-001); now 25 ahead / 0 behind origin/main |
| origin/main | `e532d2f0` — **local main 27 commits behind** |
| Working tree | 15 changed paths — **rabies WIP from a prior session, preserved untouched** (staged + unstaged, NOT part of this migration) |
| Test baseline | 2,867 collected · **2,856 passed · 9 failed · 2 skipped** (667.96s, full suite) |
| Skill surfaces | `regen-skill-surfaces --check` → No drift (13 surfaces match registry) |

## 1. Repo Health (preflight `scripts/agent-preflight.py`)

| Result | Check | Note |
|---|---|---|
| ❌ FAIL | git branch | Preflight expects `main`; migration branch violates by design (Master Plan §44 rule 1). Preflight needs a migration-branch allowance in a later phase. |
| ❌ FAIL | A-Wiki-Data folders | `waste-reports` missing at drive mount (`<A_WIKI_DRIVE_PATH>/A-Wiki-Data` — machine-local path, resolved via `drive/` junction) — partial Drive link |
| ❌ FAIL | generated wiki context | `wiki/context/wiki-overview.md` out of date — needs `scripts/gen-index.py` |
| ⚠️ WARN | working tree | 15 changed paths (rabies WIP) |
| ⚠️ WARN | cross-device handoff | stale-session advisory |
| ✅ OK | origin reachable / 12 core hooks present / hook command paths / 10 guardrails wired / platform instruction parity | — |

## 2. CI Status (captured 2026-08-17 via `gh run list`)

- 7 of 8 most recent scheduled runs **success**.
- ❌ **Cross-Platform Smoke failing** (run `31993249637`, macOS job): `gen-index --check` → `wiki/context/wiki-capability-map.md is out of date` → exit 1. Same root cause as preflight stale-context FAIL.
- ⚠️ **Daily Maintenance shows "success" but is fail-open**: `daily-maintenance.yml:20` runs `python3 scripts/gen-index.py --check 2>/dev/null || echo "OK"` — false-positive health check (Master Plan §6 evidence, RETIRE candidate).

## 3. Workflow Inventory (13 files in `.github/workflows/`)

| File | Trigger | Master-Plan verdict |
|---|---|---|
| `ci.yml` | push + dispatch | **Split** → `ci-core.yml` + domain CI (§8). Current: single monolithic `verify` job that mixes core checks with Monte Carlo notebook re-execution. Security scan = fragile shell loop (§9). |
| `cross-platform.yml` | schedule | Keep — **currently red** (stale wiki context) |
| `agent-model-scan.yml` | schedule | Consolidate → `model-intel.yml`; currently **auto-commits model swaps to main** (`feat(agents): auto-scan model swap` @ `bf5f63f2` — §4.1 evidence) |
| `model-pool-scout.yml` | schedule | Retarget: runtime cache in `drive/runtime/model-intel/`, stop git telemetry (§4.2) |
| `model-roster-refresh.yml` | schedule | Consolidate → `model-intel.yml` |
| `provider-balance.yml` | schedule | Keep, fix reporting |
| `daily-maintenance.yml` | schedule | **RETIRE** — fail-open (§6) |
| `deploy-awiki-live.yml` | — | **RETIRE** — duplicates `pages-deploy.yml` (§6) |
| `pages-deploy.yml` | — | Keep → `pages.yml` |
| `build-pake-app.yml` | — | Move → `optional/desktop-build.yml` |
| `subagent-eval.yml` | schedule | **Split** → `eval-benchmark.yml` + `routing-promote.yml` (§22) |
| `wiki-health.yml` | — | **Rewrite** with real checks via `scripts/health/wiki_health.py` (§7) |
| `wiki-health-digest.yml` | — | Fold into rewritten `wiki-health.yml` |
| Orphan temp files (`.hermes-tmp.*`, `*.tmp`) | — | **None found** at repo root; 0 tracked `.tmp`/`.log` files — already clean |

**P0 evidence — runtime telemetry flooding git**: 28 `chore(swarm): auto-update model pool [skip ci]` commits on origin/main in the last 7 days alone; local main is 27 commits behind almost entirely because of them.

## 4. Hooks

- `scripts/hooks/`: **49 files** (47 Python + 2 shell + 1 YAML patterns).
- Wiring in `.claude/settings.json`: **55 hook commands** — PreToolUse 24 · SessionStart 12 · PostToolUse 8 · Stop 7 · UserPromptSubmit 3 · PostCompact 1.
- Architecture = per-event subprocess fan-out (one event → many subprocess spawns) — consolidation target per Master Plan §32.
- **Enforcement gap**: hooks fire only inside Claude Code. Other surfaces (ZCode, Codex web, Cursor, …) rely on manual checks + CI parity (AGENTS.md warning). Hard-gate CI parity is a Phase 2/6 deliverable.

## 5. Skill Registry & Generated Surfaces

- `skills-registry.json`: **243 skills**, `schema_version: 3`, `generated_at: 2026-08-09`, all `status: canonical`.
- Generated surfaces (never hand-edit): 11 files in `scripts/skills_registry/generated/` + `wiki/A-ROUTER.md` + `wiki/SKILL-INDEX.md` + AGENTS.md tables.
- Drift check: **clean** — the modified registry/surfaces in the working tree are the rabies WIP's internally-consistent edits, not drift.

## 6. MCP Inventory

- `.mcp.json` servers: `filesystem`, `github`, `sequential-thinking`, `awiki`, `gitnexus`, `trello`.
- `awiki` server (`scripts/mcp-wiki-server.py`): **30 tools**
  - wiki core (9): `wiki_search`, `wiki_semantic_search`, `wiki_graph_neighbors`, `wiki_graph_hubs`, `wiki_get_page`, `wiki_regen_index`, `wiki_ingest_route`, `wiki_batch_status`, `wiki_batch_collect`
  - neural-spine namespace (21, via `scripts/lib/neural_spine_mcp.py`): `memory_recall`, `memory_semantic_recall`, `memory_remember`, `bb_post`, `bb_read`, `bb_reply`, `task_add`, `task_claim`, `task_release`, `task_list`, `task_update`, `skill_route`, `focus_set`, `focus_get`, `focus_advance`, `focus_clear`, `claim_acquire`, `claim_list`, `claim_release`, `claim_advance`, `design_quality_gate`
- External MCP lazy-loading (§37): **not implemented** — gitnexus/trello are statically configured.

## 7. Test Baseline (full suite, `python -m pytest tests/`)

**9 failed · 2,856 passed · 2 skipped · 2,867 collected · 667.96s**

| # | Failing test | Area | Preliminary note |
|---|---|---|---|
| 1 | `test_codex_hook_parity.py::test_codex_pretooluse_edit_hooks_match_claude` | hook parity | May correlate with uncommitted `.codex/config.toml` WIP in working tree — verify after WIP resolution |
| 2 | `test_hook_python_resolver.py::test_scanner_actually_flags_a_planted_secret` | security scanner | Scanner misses a planted secret — security-relevant, feeds Phase 2 scan refactor |
| 3 | `test_hooks_subprocess_encoding.py::test_text_mode_subprocess_pins_encoding[check_test_before_code.py]` | hooks | encoding pin missing in one hook |
| 4 | `test_live_dashboard_html.py::test_file_under_60kb` | dashboard | HTML size budget exceeded |
| 5 | `test_neural_spine_mcp.py::test_tools_dict_has_all_neural_spine_tools` | MCP | TOOLS dict incomplete vs test expectation |
| 6–9 | `test_waste_ocr_userscript.py` (4 tests: weight expression, OCR teaching history ×2, two-digit-year prompt) | userscript | Suspected external-editor drift (Iron Law #7 territory — live Tampermonkey copy vs git baseline) |

Per Master Plan discovery protocol these are **recorded, not fixed** in Phase 0.

## 8. Known Failures / Risks (baseline registry)

1. **Cross-Platform Smoke CI red** — stale `wiki/context/wiki-capability-map.md` (+ `wiki-overview.md` per preflight). Fix = run `gen-index.py` + commit (Phase 1/2 scope).
2. **Bot auto-mutation of main** (§4.1 P0): `agent-model-scan.yml` committed `feat(agents): auto-scan model swap` directly to main; `model-pool-scout.yml` commits telemetry (§4.2 P0).
3. **Fail-open health check**: `daily-maintenance.yml` (`|| echo "OK"`).
4. **Drive link partial**: `waste-reports` folder missing from `A-Wiki-Data` mount.
5. **Local main 27 commits behind origin/main** — mostly telemetry churn; migration branch is based on local HEAD. **Decision needed before Phase 1**: how to sync (and who commits the rabies WIP).
6. **Rabies WIP uncommitted (15 paths)** — ownership/handoff issue outside migration scope; preserved byte-for-byte.
7. **Security scanner gap** (test #2 above).
8. **INCIDENT 2026-08-17 15:29 (HIGH — data-loss class, damage regenerable)** — external automation ran `git pull --rebase origin main` on the migration branch mid-session (reflog evidence; not from git hooks; source unidentified — suspected concurrent agent session's SessionStart auto-pull, the documented 2026-07-27 incident class). Effects: branch base rewritten to latest origin/main (ungated but net-desirable); rabies WIP restored only partially — working-tree modifications to 3 generated surfaces (`gemini.skills.json`, `zcode.skills.manifest.json`, `skills-index.md`) vanished, present in no stash (all 5 stashes are from July–early Aug) and no commit. Recoverable via `regen-skill-surfaces.py` from the surviving modified `skills-registry.json`. Full record: `awiki-vnext-discoveries.md` DISC-001. Strongest live evidence for Master Plan §4.1/§4.3.

## 9. Phase 0 Exit Criteria — Answers

| Question | Answer |
|---|---|
| อะไรผ่าน | Unit suite 2,856/2,867 · skill surfaces no-drift · registry consistent · preflight core-hooks/paths/guardrails OK · origin reachable · CI 7/8 green |
| อะไร fail | 9 unit tests (§7) · Cross-Platform Smoke · preflight stale-context + drive waste-reports |
| อะไร flaky | None observed flaky this run (single run; no rerun statistics collected) |
| อะไร generated | 11 `scripts/skills_registry/generated/` surfaces · `wiki/A-ROUTER.md` · `wiki/SKILL-INDEX.md` · `wiki/context/*` overviews (gen-index) · AGENTS.md tables |
| อะไร runtime | model pool / roster / provider balance telemetry (28 commits/7d) — target home `drive/runtime/model-intel/` |
| อะไร critical | Bot can mutate main without promotion gate (§4.1) · runtime telemetry in git (§4.2) · fail-open health (§4 P0) · secret-scanner gap |

## 10. Rollback

Phase 0 added docs only. Rollback = `git checkout main && git branch -D refactor/awiki-kernel-vnext` (working-tree WIP unaffected).
