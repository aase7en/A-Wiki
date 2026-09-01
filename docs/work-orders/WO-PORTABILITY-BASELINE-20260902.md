# WO-PORTABILITY-BASELINE-20260902 — Windows portability baseline burn-down

Status: CLAIMED_P0_INVENTORY
Executor: GLM5.3-ZCode-MAX
Integrity / final reviewer: GPT-5.6-Sol
Branch: `fix/wo-portability-baseline-glm-20260902`
Worktree: `<WORKTREE>/A-Wiki-portability-glm-20260902`
Base: `8dfcbe068a00cdfa6671eef3e4e603c4552aa6d0`
Claim checkpoint: `64272cd06ae6b128fcce09217373c988390c4c07`

## Goal

Burn down current, reproducible Windows portability baseline debt using bounded root-cause families and deterministic TDD. Prioritize cp874/subprocess encoding and Git-Bash/MSYS/path behavior. Do not chase environment-only failures merely to make a count green.

Use ZCode Goal Mode + `$a-loop` for the long execution loop. Keep this Work Order as the only durable task/checkpoint file for this lane.

## Baseline authority

- M1 full Windows baseline: `58 failed / 3398 passed / 19 skipped` at `71406f8a...`.
- M8: `54 failed / 3531 passed / 19 skipped`; all 54 replayed and failed at M1, so they were PRE_EXISTING.
- Known families include Windows cp874 console/subprocess decoding, Git-Bash/MSYS path or symlink assumptions, linked-worktree assumptions, and Windows FTS runtime/tool debt.
- PR #46 is now merged at base `8dfcbe06`; it already fixed the Review Bus linked-worktree `gitdir:` family. Re-measure current baseline instead of assuming 54 remain.

## P0 — inventory before production mutation

Current claim allows mutation of only:
- `COLLAB.md`
- this Work Order

Until P0 is complete, all code/test inspection is READ-ONLY.

P0 required evidence:
1. Recover `BRAIN-ENTRY.md` -> `PROJECT-GRAPH.yaml` -> `COLLAB.md` -> this WO -> `AGENTS.md` applicable rules.
2. Verify worktree/branch/HEAD/dirty state and `python -m conductor status --json`.
3. Run native Windows `python -m pytest tests -q` with no UTF-8 environment override.
4. Record every failing nodeid and exact summary in this WO.
5. Compare failures with M1/M8 evidence in `docs/work-orders/WO-RFR-20260824.md`.
6. Classify by root-cause family: CP874/ENCODING, GIT_BASH_MSYS_PATH, WORKTREE_GIT, FTS_ENVIRONMENT, OTHER.
7. For each family, identify likely production/test files and run GitNexus impact before proposing mutation.
8. Update this WO with a failure matrix and the smallest exact file scope for the first independent family.

Before any production/test edit, expand the existing claim to that exact family scope, commit+push the claim expansion, then continue. Never claim broad `scripts/**` or `tests/**`.

## Priority order

PB-0 — fresh baseline + family matrix.
PB-1 — cp874 / subprocess decoding / console-output defects.
PB-2 — Git-Bash / MSYS / path / symlink deterministic defects.
PB-3 — remaining linked-worktree/path assumptions only if still reproducible and not already covered by PR #46.
PB-4 — full regression, audit, checkpoint, Primary handoff.

## Parallel-lane boundaries

GPT Primary concurrently owns the ZCode runtime repair lane. Do NOT modify:
- `scripts/setup_zcode_hooks.py`
- `tests/test_setup_zcode_hooks.py`
- `docs/work-orders/WO-ALOOP-ZCODE-20260901.md`
- branch/worktree `fix/wo-aloop-zcode-runtime-matchers`

Avoid Review Bus surfaces unless a fresh baseline proves a remaining independent defect and Primary explicitly expands scope:
- `scripts/lib/a_loop_review.py`
- `tests/test_a_loop_review.py`
- `docs/runbooks/review-bus.md`
- `docs/work-orders/WO-REVIEW-BUS-OPS-20260901.md`

Never modify `AGENTS.md`, `CLAUDE.md`, `raw/`, secrets, the primary checkout, or A-Conductor. Do not install FTS/OpenSSL/system DLLs in this WO. Classify environment-only FTS debt rather than mutating the machine.

## Per-family Loop Engineer contract

For each claimed family:
`RECOVER -> VERIFY -> IMPACT -> RED -> ROOT CAUSE -> IMPLEMENT -> SELF REVIEW -> FOCUSED TEST -> RELATED REGRESSION -> SAFETY GATES -> detect_changes -> CHECKPOINT -> COMMIT/PUSH -> NEXT FAMILY`

Production fixes require a failing test first. Do not weaken tests or hide failures with global UTF-8 environment overrides. Fix the owning code boundary when the behavior is repo-owned.

After each coherent family, append exact evidence to this same WO: HEAD, files, RED/GREEN commands, results, defect mechanism, residual risk, and next safe action. Commit+push each resumable checkpoint.

## Verification minimum per production family

- focused RED/GREEN regression(s)
- relevant related tests
- `git diff --check`
- `python scripts/check-privacy.py`
- `python scripts/security/scan_repo.py --ci --baseline scripts/security/baseline.txt`
- `python scripts/check-stale-specs.py`
- `python scripts/health/wiki_health.py`
- GitNexus impact before symbol edit and `detect_changes` before commit

Tool failure is `UNVERIFIED — tool failure`, never PASS.

## Completion / handoff

Do not merge. GPT Primary owns exact-SHA independent review, remote diff audit, CI verdict, merge and post-merge verification.

The Goal is complete only when PB-0 is measured, every safely claimable high-value portability family is either fixed with deterministic evidence or explicitly classified with a reason not to mutate, the final full regression is recorded, all required gates pass, and this WO identifies any residual environment-only debt.

Stop only for `HUMAN_DECISION_REQUIRED`, `OWNERSHIP_CONFLICT`, `SAFETY_BLOCK`, or scope expansion that Primary must authorize. Do not ask the human to relay detailed results; persist them here and push the branch.
