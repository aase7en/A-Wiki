# A-Wiki vNext Migration — Plan & Tracking Log

> Living document for the `refactor/awiki-kernel-vnext` migration.
> Source of authority: A-WIKI-MASTER-DEVELOPMENT-PLAN (user-provided, external — ChatGPT architect + GLM-5.3 executor model).
> Rule: **one phase per review cycle** — implement → test → report → STOP → ChatGPT review verdict (PASS / PASS WITH NOTES / CHANGES REQUIRED / BLOCK) → next phase.
> Discoveries during work (non-blocking) → `awiki-vnext-discoveries.md` (same dir). Security leak / data loss / repo corruption → stop and report immediately.

## Guardrails (binding for every phase)

1. Work only on `refactor/awiki-kernel-vnext` — never `main`.
2. Inspect before delete (`git grep` / `rg` references first) — record evidence.
3. Preserve public/private boundary; no machine paths, no secrets, no real hospital names.
4. Respect Iron Laws (test-first, root-cause, raw immutable, registry SoT, claims on shared surfaces).
5. Reuse/consolidate/extract-pattern before adding any dependency, framework, service.
6. Every phase = separate reversible commit(s); no giant commits.
7. Tests before every phase commit — mechanical evidence only, no "looks correct".
8. **No push without explicit user approval.**

## Phase Checklist

| Phase | Scope | Status | Commit |
|---|---|---|---|
| 0 | Baseline & safety | ✅ COMPLETE (awaiting review) | this branch |
| 1 | Stabilize automation (stop ungated main mutation, retire daily-maintenance/deploy-awiki-live, telemetry → runtime cache, pin Actions) | ⬜ pending review gate | — |
| 2 | CI & health refactor (`ci-core.yml`, domain split, real `wiki_health.py`, Python security scan, MCP/hook smoke, integration-registry validation) | ⬜ | — |
| 3 | Kernel contract (`A-WIKI-KERNEL.md`, `config/awiki.yaml`, `config/integrations.yaml`, intake/storage/project-memory protocols) | ⬜ | — |
| 4 | Project adapter (`scripts/project/{attach,status,validate}.py`, schema, cross-platform tests) | ⬜ | — |
| 5 | Memory layers (L0–L5 separation, experiment memory, promotion pipeline, privacy gate) | ⬜ | — |
| 6 | Hook engine consolidation (lifecycle runner, unit tests for every hard gate) | ⬜ | — |
| 7 | Model control plane (`scripts/lib/providers/`, `config/models/` policy-vs-runtime split) | ⬜ | — |
| 8 | Eval vs routing promotion split (`eval-benchmark.yml` / `routing-promote.yml` + gates) | ⬜ | — |
| 9 | A-Loop v2 (success predicate, baseline, one-change, mechanical verify, plateau states) | ⬜ | — |
| 10 | Optional external modules (world-intel MCP — lazy, no vendoring) | ⬜ | — |
| 11 | Documentation slimming | ⬜ | — |

## Decisions & Deviations Log

| # | Date | Decision / Deviation | Reason |
|---|---|---|---|
| D1 | 2026-08-17 | Branch based on local `main` @ `156a104e`, not origin/main (`e532d2f0`, +27) | Pulling with 15-path uncommitted rabies WIP risks destroying it (documented auto-pull incident). Sync decision deferred to user before Phase 1. |
| D2 | 2026-08-17 | Rabies WIP left untouched in working tree/index | Not migration scope; owner should commit on main separately. Commit for Phase 0 uses pathspec (`docs/migration/` only) so WIP stays staged-but-uncommitted. |
| D3 | 2026-08-17 | Preflight branch-FAIL accepted as intentional | Master Plan mandates migration branch; preflight asserts main-only. Reconcile in Phase 2 (allow known migration branches). |
| D4 | 2026-08-17 | 9 baseline test failures recorded, not fixed | Phase 0 is capture-only per Master Plan discovery protocol. |
| D5 | 2026-08-17 | No `claim_acquire` MCP call at phase start | awiki MCP server not exposed in this executor's tool surface; hook parity for ZCode is manual. Noted as Iron Law #11 gap. |

## Phase 0 Log (2026-08-17)

- Branch created from `156a104e`; sync via `git fetch` (origin advanced cdd042b3→e532d2f0 during session).
- Captured: preflight, CI runs (gh), 13 workflows, 49 hook scripts + 55 wired commands, 243-skill registry (no drift, 13 surfaces), MCP inventory (6 servers, 30 `awiki` tools), full pytest baseline (2,867 collected: **2,856 passed / 9 failed / 2 skipped**), known-failure registry, exit-criteria answers.
- Deliverable: `docs/migration/awiki-vnext-baseline.md`.
- Full report sent to user for ChatGPT architecture review — **stopped before Phase 1** per mandatory stop-point rule.

## Review History

| Phase | Verdict | Date | Notes |
|---|---|---|---|
| 0 | ⏳ awaiting | 2026-08-17 | — |
