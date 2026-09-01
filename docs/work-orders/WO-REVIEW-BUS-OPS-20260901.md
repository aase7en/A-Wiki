# WO-REVIEW-BUS-OPS-20260901 — Operational no-human-relay hardening

Status: PRIMARY_INTEGRATION_GREEN / PR_PENDING
Executor: GLM5.3-ZCode-MAX (implementation) + GPT-5.6-Sol (integration/review)
Integrity / final reviewer: GPT-5.6-Sol exact-SHA gate; independent transport required when available
Branch: `fix/wo-review-bus-ops-primary-integration`
Base: `cdee1a36e9722470508144ba9960d495528ced0f`

## Goal

Make the existing A-Wiki Review Bus reliable in isolated Git worktrees and prove the thinnest safe seam to the already-shipped A-Conductor stable external-agent mailbox. Do not build a second orchestrator, scheduler, mailbox, task store, or review protocol.

Reuse classification: **REUSE / WRAP**.

Read first: `BRAIN-ENTRY.md` -> `COLLAB.md` -> this WO -> `docs/migration/awiki-agent-review-bus-plan.md` -> `docs/runbooks/review-bus.md` -> relevant code/tests.

## Baseline authority

- `scripts/lib/review_bus.py` core: **18 passed** on this branch base.
- `tests/test_a_loop_review.py`: **5 failed / 1 passed** in a real isolated worktree.
- The same five failing nodeids are present in the M1 and M8 regression baselines; classify them **PRE_EXISTING**, not new regressions.
- Root cause already reproduced: `ALoopReview.head_sha()` assumes `.git` is a directory and reads `.git/HEAD`; in a linked worktree `.git` is a pointer file.
- A-Conductor PR #168 (`feat(agents): add stable external mailbox`) is COMPLETE/MERGED/POST_MAIN_GREEN. It owns the stable per-agent mailbox/task-result relay. A-Wiki must not duplicate it.

## Claimed scope

Allowed mutation:
- `COLLAB.md`
- this work order
- `scripts/lib/a_loop_review.py`
- `tests/test_a_loop_review.py`
- `docs/runbooks/review-bus.md`

Forbidden unless Primary expands the claim:
- `scripts/lib/review_bus.py` and `schemas/**` (core is green; do not churn it)
- A-Conductor repository files
- `AGENTS.md` / `CLAUDE.md`
- unrelated portability baseline failures
- `main`, destructive Git, force-push, or automatic merge

## Micro-steps

| ID | Goal | State | Required evidence |
|---|---|---|---|
| RB-0 | Recover actual state and map the 12 Review Bus v1 criteria as VERIFIED/PARTIAL/MISSING | DONE (see checkpoint 2026-09-01 #1) | evidence links/functions/tests written here |
| RB-1 | Fix worktree-safe exact HEAD resolution TDD-first | DONE (see checkpoint 2026-09-01 #1) | deterministic regression that fails before fix; all 6 A-Loop tests green in linked worktree |
| RB-2 | Realistic local review-cycle E2E in the isolated worktree | DONE (see checkpoint 2026-09-01 #1) | exact SHA request -> finding/verdict -> retest/CI -> READY/stale-SHA reopen |
| RB-3 | Audit compatibility with A-Conductor Stable External Mailbox | DONE (mapping only — see checkpoint 2026-09-01 #1; cross-repo wiring = DECISION_REQUIRED for Primary) | REUSE/WRAP mapping only; no A-Conductor mutation |
| RB-4 | Self-review, GitNexus impact, safety gates, checkpoint, PR | DONE for this slice; PR handoff to Primary (see checkpoint) | exact commands/results + clean claimed diff |

## Checkpoint — 2026-09-01 #1 (GLM5.3-ZCode-MAX)

Branch `fix/wo-review-bus-ops-20260901` · base `c9b09944` · HEAD at checkpoint start `1c27ce46` (claim commit).
Conductor at recover: exactly one active claim (this lane) — no overlapping mutable scope.
Files changed this slice: `scripts/lib/a_loop_review.py`, `tests/test_a_loop_review.py`, `docs/runbooks/review-bus.md`, this WO.

### RB-0 — Review Bus v1 criteria map (§16 of `docs/migration/awiki-agent-review-bus-plan.md`)

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 1 | executor publishes review request without human relay | VERIFIED | `ReviewBus.publish()` / `open_review_for_task` — core tests green (18/18) |
| 2 | reviewer targets exact HEAD SHA | PARTIAL → FIXED by RB-1 | schema `_SHA_RE` pins shape; `head_sha()` was broken in linked worktrees (gitfile) — now resolves via plumbing; pinned-to-exact-head proven in RB-2 step 1 |
| 3 | findings have stable IDs | VERIFIED | `R-<phase>-NNN` (`_next_finding_no`) |
| 4 | executor ingests findings automatically | VERIFIED | `load()`/findings list + `task_gate` returns blocker ids |
| 5 | fixes map back to finding IDs | VERIFIED | `resolve_finding(fix_sha=...)` |
| 6 | tests re-run after fixes | VERIFIED | `record_retest(sha, ok)` |
| 7 | new SHA invalidates old approval | VERIFIED | `record_retest` invalidation branch; `test_stale_sha_reopens...` |
| 8 | CI status in readiness | VERIFIED | `record_ci` + `readiness` |
| 9 | open blockers prevent READY | VERIFIED | `set_verdict` raises; `readiness` reasons |
| 10 | no automatic merge | VERIFIED | engine is state-only (zero git calls); runbook policy |
| 11 | state survives restart | VERIFIED | per-cycle JSON via `atomic_write` |
| 12 | reviewer swappable, protocol unchanged | VERIFIED | reviewer is data (name+transport) |

### RB-1 — worktree-safe HEAD resolution (TDD)

Approaches compared (per §Engineering constraints):
1. Extend pure file-IO (gitfile → `gitdir` → `commondir` → loose/packed refs) — REJECTED: reimplements git internals (packed-refs, commondir edge cases), zero existing A-Wiki precedent (repo grep found no gitfile parsers), highest blast radius for exact-SHA semantics.
2. Bounded git plumbing `git --git-dir <resolved> rev-parse HEAD` — CHOSEN: matches 7 existing repository call sites (`awiki-doctor.py:53`, `hooks/git_safety_backup.py:57`, `hooks/check_history_divergence.py:126`, `hooks/session_start.py:74`, `a_escalate.py:105`, `check-stale-specs.py:48`); git resolves commondir/packed-refs/detached uniformly; only the one stable `gitdir:` pointer line is parsed; every failure raises `ReviewBusError` (no silent fallback); 15s subprocess timeout. Trade-off: adapter is no longer "pure file IO (no subprocess)" — docstring + runbook amended (that claim was the broken assumption).

RED evidence (before fix): `tests/test_a_loop_review.py` → 9 failed / 3 passed — the 5 pre-existing baseline failures UNCHANGED plus 4 new regressions red (`linked_worktree_gitfile`, `missing_git_dir`, `invalid_gitfile`, `never_falls_back_on_git_failure`); `normal_checkout` + `detached_head` guards green pre-fix.

Implementation: `ALoopReview._resolve_git_dir()` (dir | gitfile→`gitdir:` | else explicit error) + `head_sha()` via `git --git-dir <dir> rev-parse HEAD` with rc+SHA-regex validation (`_SHA_RE`).

GREEN evidence: `python -m pytest tests/test_a_loop_review.py -q` → **12 passed** (6 original + 6 new; original six now green INSIDE the linked worktree). Combined: `python -m pytest tests/test_review_bus.py tests/test_a_loop_review.py -q` → **30 passed**. Core untouched (`review_bus.py`/schemas unmodified).

Self-review (adversarial checklist): normal checkout ✓ test · linked worktree ✓ test (real `git worktree add`) · detached HEAD ✓ test · missing/invalid metadata ✓ 2 tests raise `ReviewBusError` · subprocess failure wrapped (OSError/TimeoutExpired→`ReviewBusError`) ✓ · unexpected output rejected by `_SHA_RE` ✓ · stale-SHA approval invalidation unchanged ✓ test · Windows paths ✓ (all evidence executed on Windows in this worktree) · Py3.8-safe syntax (no 3.9+ runtime features; `capture_output/text` are 3.7+) ✓. Blast radius: grep shows zero callers of `a_loop_review` outside its test file. GitNexus MCP unavailable in this session (tool unavailability, not code failure); manual impact analysis performed instead.

### RB-2 — realistic E2E in this isolated worktree (executed)

`.tmp/review-bus-rb2`, phase RB2, `git_dir=<worktree>/.git` (real gitfile):
1. publish head pinned exact == `git rev-parse HEAD` (`1c27ce46`) ✓
2. gate REVIEW_REQUESTED / allow=False ✓
3. blocker `R-RB2-001` + CHANGES_REQUIRED → blocked with finding id ✓
4. resolve→verify→PASS→retest@head→CI → READY / allow=True ✓
5. retest at new SHA → REVIEW_REQUESTED / allow=False (stale approval reopened) ✓

### RB-3 — A-Conductor Stable External Mailbox compatibility (mapping only)

Conductor status (`python -m conductor status --json`) works from this worktree; claim schema `awiki-conductor/v1` is the runtime authority. Review Bus seam analysis:
- Review Bus `transport` field (`"local-mcp"` default) is the ONLY transport touchpoint — no mailbox/scheduler code exists or is needed in A-Wiki for the state machine.
- A-Conductor PR #168 stable per-agent mailbox OWNS external-agent relay. Any A-Wiki↔mailbox wiring (e.g., transport adapter publishing review requests into a mailbox) is cross-repo and Primary-owned: **DECISION_REQUIRED — not implemented here** (per Goal constraint + this WO).
- No duplication introduced: no new orchestrator/scheduler/mailbox/task-store/protocol/lifecycle in this slice.

### Gates (all executed in this worktree)

`git diff --check` CLEAN · `check-privacy.py` clean · `scan_repo.py --ci` 6,314 files / 51 baseline / **0 new** · `check-stale-specs.py` OK (full-history variant on this base) · `wiki_health.py` 0 hard / 352 advisory.

### Defects / risks / next

- No new defects found. Pre-existing portability baseline failures elsewhere were NOT touched (constraint honored).
- Residual risk: `head_sha()` now shells out to `git` — environments without git on PATH fail explicitly (by design, `ReviewBusError`), not silently.
- Next safe action: Primary (GPT-5.6 Sol) exact-SHA review of this branch → PR → CI (`py38-smoke` will confirm 3.8 syntax) → merge decision remains Primary-owned.


## Engineering constraints

For RB-1 compare at least two approaches before production edit:
1. extend pure file-I/O resolution to understand gitfile/worktree `gitdir`, `commondir`, loose/packed refs;
2. use bounded Git plumbing (`git rev-parse HEAD`) following existing repository patterns.
Choose the smallest cross-platform design that preserves exact-SHA semantics; record the trade-off here. Do not weaken tests to accommodate the bug.

Use Loop Engineer: `RECOVER -> VERIFY -> CLAIM -> IMPACT -> RED -> IMPLEMENT -> SELF REVIEW -> TEST/E2E -> DEFECT MEMORY -> AUDIT -> detect_changes -> COMMIT/PUSH -> PR/CI`.

## Acceptance

- Existing Review Bus core stays green: `python -m pytest tests/test_review_bus.py -q`.
- A-Loop review suite becomes 6/6 green in an isolated linked worktree, with explicit regression coverage for the gitfile/worktree case.
- Review request remains pinned to the exact current HEAD; stale SHA approval still reopens the cycle.
- No new task lifecycle/mailbox/reviewer protocol is added to A-Wiki.
- A-Conductor stable mailbox is treated as external runtime authority; any required cross-repo code change is `DECISION_REQUIRED`, not silently implemented here.
- Privacy/security/stale-spec/wiki-health and `git diff --check` pass; GitNexus `detect_changes` is run before every implementation commit.
- Every bounded checkpoint updates this same WO and is committed+pushed. Do not create duplicate status/handoff/memory files.

## Handoff/result rule

ZCode may use Goal/Plan and relevant A-Wiki skills (`a-plan`, `a-debug`, `a-claim`, `a-loop`). Continue autonomously through READY micro-steps inside the claimed scope. Stop only for `HUMAN_DECISION_REQUIRED`, `OWNERSHIP_CONFLICT`, `SAFETY_BLOCK`, or required scope expansion. Write the requested machine-readable result to the task packet's declared destination; GPT will also recover state from this WO and Git, so the human must not relay detailed results.

## Checkpoint — 2026-09-02 #2 (GPT Primary integration)

GLM candidate `02c9ea17edd7c64d950d65fa992d34518d52a59f` was clean/pushed and explicitly handed off to Primary. Main had advanced six commits to `cdee1a36e9722470508144ba9960d495528ced0f`; `git merge-tree` found no conflict. Primary claimed isolated branch `fix/wo-review-bus-ops-primary-integration` at claim commit `421fd36b` and cherry-picked only the GLM implementation commit as `d7bc1808` (the GLM claim commit was not duplicated).

Independent review found RB-1A: Git 2.49 supports relative worktree metadata, but `_resolve_git_dir()` treated `gitdir: ../...` relative to process CWD instead of the gitfile parent. A synthetic gitfile pointing relatively to a real repository reproduced `ReviewBusError: git rev-parse HEAD failed (rc=128)` before the production repair. The deterministic regression is `test_head_sha_resolves_relative_linked_worktree_gitfile`.

Repair keeps the original design: parse only the stable `gitdir:` line; reject an empty pointer; absolute pointers remain unchanged; relative pointers resolve from `git.parent`; Git plumbing remains the authority for HEAD/packed refs/detached state. The stale test-module claim of “pure file IO” was corrected. Review Bus/schema SHA width remains unchanged (7–40 hex) because that is the existing protocol authority and is outside this repair.

GREEN: target regression 1/1; `test_a_loop_review.py + test_review_bus.py + test_kernel_contracts.py` = 74 passed; broader set adding `test_a_loop_zcode_hooks.py` = 91 passed; `py_compile` PASS. Privacy PASS; security 6,322 tracked / 51 baseline / 0 new; stale-spec PASS; wiki-health 0 hard / 352 advisory; `git diff --check` clean. GitNexus pre-edit impact for `head_sha`: LOW, one direct caller (`open_review_for_task`), zero execution flows. Durable defect memory is the new regression test; no duplicate memory/handoff file is created.

Next safe action: finish fresh GitNexus index + staged `detect_changes`, commit/push the repaired exact candidate, open draft PR to current `main`, audit remote diff/CI, exact-SHA re-audit, then authorized merge/fetch/post-merge verification. Independent reviewer transport remains separate evidence; no PASS may be inferred from tool unavailability.
