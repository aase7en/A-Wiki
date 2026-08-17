# A-Wiki vNext Migration — Plan & Tracking Log

> Living document for the A-Wiki vNext migration. Active execution branch: **`refactor/awiki-kernel-vnext-clean`** (isolated clean worktree from `origin/main`; forensic branch `refactor/awiki-kernel-vnext` remains preserved per DISC-001).
> Source of authority: A-WIKI-MASTER-DEVELOPMENT-PLAN plus `docs/migration/awiki-agent-review-bus-plan.md`.
> Current execution model: ZCode / GLM-5.3 = executor; ChatGPT = architecture reviewer/QA when invoked. Future reviewers may be automated through the same A-Wiki Review Bus protocol.
> Rule: one phase per review cycle. Security leak / data loss / repo corruption = immediate stop.

## Guardrails (binding for every phase)

1. Work only on `refactor/awiki-kernel-vnext-clean` using its isolated worktree — never `main`, never the contaminated forensic branch.
2. Inspect before delete (`git grep` / `rg` references first) and record evidence.
3. Preserve the public/private boundary; no machine paths, secrets, or private operational data in the public repo.
4. Respect Iron Laws: test-first where applicable, root-cause before fixes, raw immutable, registry as source of truth, claims on shared surfaces.
5. Reuse/consolidate/extract-pattern before adding a dependency, framework, or service.
6. Every phase uses small reversible commits; no giant cross-subsystem refactors.
7. Tests/checks before phase completion; mechanical evidence only.
8. Push only to the migration/review branch; never merge or deploy automatically.
9. An approval applies to an exact reviewed HEAD SHA; a new implementation SHA requires a new review cycle.
10. Agent-to-agent review automation must use durable state (GitHub/review-state protocol), not hidden conversational memory.

## Phase Checklist

| Phase | Scope | Status | Commit |
|---|---|---|---|
| 0 | Baseline & safety | ✅ **PASS** — clean branch isolation independently verified: 4 commits ahead / 0 behind, diff limited to 3 migration docs | `7aae5935` `857faf57` `5b4e297d` `4d9c40b3` |
| 1 | Stabilize automation (Priority #1: harden `session_start.py::git_pull`; stop ungated main mutation; retire duplicate/fail-open workflows; remove model telemetry Git churn; pin/fix Actions) | ▶ NEXT | — |
| 2 | CI & health refactor (`ci-core.yml`, domain split, real `wiki_health.py`, Python security scan, MCP/hook smoke, integration-registry validation) | ⬜ | — |
| 3 | Kernel contract (`A-WIKI-KERNEL.md`, `config/awiki.yaml`, `config/integrations.yaml`, intake/storage/project-memory protocols) + formalize `awiki-review/v1` protocol/schema design | ⬜ | — |
| 4 | Project adapter (`scripts/project/{attach,status,validate}.py`, schema, cross-platform tests) | ⬜ | — |
| 5 | Memory layers (L0–L5 separation, experiment memory, promotion pipeline, privacy gate) | ⬜ | — |
| 6 | Hook engine consolidation (lifecycle runner, unit tests for every hard gate) | ⬜ | — |
| 7 | Model control plane (`scripts/lib/providers/`, `config/models/` policy-vs-runtime split) | ⬜ | — |
| 8 | Eval vs routing promotion split + first automated reviewer adapter/review-state foundations | ⬜ | — |
| 9 | A-Loop v2 + connect improvement-loop states to review verdict/state machine | ⬜ | — |
| 10 | Optional external modules (world-intel MCP — lazy, no vendoring) | ⬜ | — |
| 11 | Documentation slimming + review-bus operator docs | ⬜ | — |

## Parallel Track — Agent Review Bus

Architecture plan: `docs/migration/awiki-agent-review-bus-plan.md`.

Purpose: remove the user as the copy/paste transport between executor and reviewer agents.

Near-term mode while Codex is unavailable:

```text
GLM executor
  -> implement/test/commit/push
  -> structured GitHub review handoff
  -> ChatGPT reads branch directly when invoked
  -> verdict/finding IDs
  -> GLM fixes and resubmits
```

Future mode:

```text
GLM executor
  -> GitHub Review Bus
  -> automatic reviewer adapter (Codex/OpenAI API/other)
  -> normalized awiki-review/v1 findings
  -> GLM auto-fix/retest/re-review
  -> READY only when review + CI gates pass
```

Important: do **not** pause Phase 1–2 to build a large orchestrator. Phase 3 defines the protocol formally; Phase 8–9 implements automation after the safety/CI foundations are stable.

## Decisions & Deviations Log

| # | Date | Decision / Deviation | Reason |
|---|---|---|---|
| D1 | 2026-08-17 | Initial migration branch started from local `main` instead of current `origin/main` | Dirty unrelated WIP made an in-place sync unsafe. Later superseded by D6/D7. |
| D2 | 2026-08-17 | Rabies WIP was intentionally left outside migration commits | It was not migration scope and had a separate owner/history. |
| D3 | 2026-08-17 | Preflight branch failure accepted during Phase 0 | Existing preflight assumed `main`; migration intentionally requires a review branch. Reconcile later without weakening branch safety. |
| D4 | 2026-08-17 | Nine baseline test failures recorded instead of fixed | Phase 0 was capture-only; failures become scoped work in later phases. |
| D5 | 2026-08-17 | No live claim MCP call from ZCode | The MCP surface was not exposed to that executor; this is a cross-agent parity gap to address later. |
| D6 | 2026-08-17 | **INCIDENT:** SessionStart executed `git pull --rebase origin main` on the migration branch | Concurrent-session automation rewrote branch history and partially lost regenerable uncommitted generated-surface edits. Root cause recorded in DISC-001. |
| D7 | 2026-08-17 | Created isolated clean worktree/branch directly from `origin/main`, cherry-picked only Phase 0 docs, normalized timeline | Restored attributable history and protected unrelated WIP. Original forensic branch/checkout left untouched. |
| D8 | 2026-08-17 | Added A-Wiki Agent Review Bus as a parallel architecture track | Reduce human relay work while keeping execution/review vendor-neutral and auditable. Implementation is deliberately deferred until core safety/CI foundations are stable. |

## Phase 0 Log (2026-08-17)

- Captured workflows, hooks, skill registry, MCP inventory, CI state, generated surfaces, full pytest baseline, preflight failures, and known risks.
- Baseline full suite: 2,867 collected — 2,856 passed / 9 failed / 2 skipped.
- DISC-001 captured the SessionStart auto-rebase/data-loss-class incident and confirmed the `session_start.py::git_pull()` root cause.
- First remediation was rejected because the migration branch contained 24 unrelated carried commits.
- Clean remediation branch was created directly from `origin/main`; final independent GitHub review confirmed `ahead=4`, `behind=0`, and only the 3 migration docs differ from `main`.
- Phase 0 is therefore closed as PASS.

## Review History

| Phase | Verdict | Date | Notes |
|---|---|---|---|
| 0 | PROVISIONAL PASS WITH NOTES | 2026-08-17 | Report quality looked good, but commits were not yet visible remotely. |
| 0 | CHANGES REQUIRED | 2026-08-17 | Formal GitHub review found branch contamination: 24 unrelated commits / 63-file diff. |
| 0 | **PASS** | 2026-08-17 | Clean branch verified independently: 4 commits ahead, 0 behind, docs-only 3-file diff. Phase 1 authorized. |

## Phase 1 Entry Order

GLM must execute Phase 1 in this order unless new evidence makes a safety stop necessary:

1. **P1.1 — Fix `scripts/hooks/session_start.py::git_pull` first.** Add tests before/with the fix. Non-main branches must never be silently rebased/pulled onto `origin/main`; synchronization must not endanger dirty working trees.
2. **P1.2 — Stop ungated model-policy mutation of `main`.** Convert scheduled mutation to candidate/report/recommendation behavior; promotion requires explicit gate.
3. **P1.3 — Stop model-pool/runtime telemetry commits.** Preserve capability while moving observations to runtime cache/artifact/private runtime storage as appropriate.
4. **P1.4 — Retire `daily-maintenance.yml` fail-open behavior and old duplicate Pages deployment workflow only after reference/dependency inspection.**
5. **P1.5 — Fix `provider-balance.yml` reporting/pinning/minimal permissions as scoped by the master plan.**
6. Run targeted tests after each coherent change; run the required Phase 1 regression set before requesting review.
7. Return a structured Phase 1 review handoff and STOP before Phase 2.

## Current Instruction to GLM 5.3

Phase 0 is approved. Begin **Phase 1 only** on the clean isolated worktree/branch. Read `docs/migration/awiki-agent-review-bus-plan.md` as an additional architecture constraint, but do not build the full review orchestrator during Phase 1. The immediate safety priority is P1.1 (`session_start.py`).
