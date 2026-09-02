# WO-REVIEW-BRIDGE-20260902 — Thin conductor Review Bridge (WRAP/EXTEND)

Status: READY_FOR_GPT_PRIMARY_REVIEW
Executor: GLM5.3-ZCode-MAX
Integrity / final reviewer: GPT-5.6-Sol (exact-SHA review, PR/CI/merge authority)
Branch: `feat/wo-review-bridge-glm-20260902`
Base: `fc9a981d08785ee684a2f1f0616dc254f6855c0c` (origin/main at lane start)
Worktree: `<WORKTREE>/A-Wiki-review-bridge-glm-20260902`

## Goal

Expose the existing ReviewBus (`scripts/lib/review_bus.py`, the ONLY review-state
authority) and the A-Conductor Stable External-Agent Mailbox seam through a thin
brain-side conductor adapter (`conductor/review_bridge.py` + `python -m conductor
review …`) so A-Conductor/external reviewers can drive review cycles without
human result copy/paste — with ZERO duplicate orchestration.

Proven seam (binding, from WO-REVIEW-BUS-OPS-20260901 RB-3 + A-Conductor PR #168):
ReviewBus → thin conductor review adapter → transport=`remote-queue` → A-Conductor
mailbox/external reviewer → durable review result → thin adapter ingestion →
ReviewBus findings/verdict → independent retest → independent CI → READY.
A reviewer PASS alone NEVER yields READY.

## Reuse classification — WRAP/EXTEND, not NEW

Reused as-is (no modification): `scripts/lib/review_bus.py` (engine), `schemas/awiki-review/v1.schema.json`,
`scripts/lib/a_loop_review.py` (task↔cycle map + worktree-safe exact-HEAD), the
`remote-queue` transport enum (already in schema), A-Conductor mailbox (external
runtime authority, zero A-Wiki code). The bridge adds NO scheduler, mailbox,
provider registry, state machine, or task/result lifecycle.

## Brain improvement gate

- Gain: A-Conductor/external agents drive the canonical ReviewBus through a thin
  machine-readable brain API; no human relay of review results.
- Lightweight: adapter only; every state transition delegates to ReviewBus.
- Cost: deterministic local state transitions; model execution stays outside A-Wiki.
- Cross-platform: no personal paths, no provider assumptions; bounded git plumbing
  only (same precedent as a_loop_review RB-1).
- Public safety: no credentials/private payloads; results are bounded validated data.
- Verification: focused contract tests + ReviewBus/conductor regression + repo gates.

## Claimed scope

- `COLLAB.md`
- this work order
- `conductor/review_bridge.py` (new)
- `conductor/cli.py` (review subcommand wiring)
- `tests/test_conductor_review_bridge.py` (new)
- `tests/test_conductor.py` (only if CLI contract coverage belongs there)
- `docs/runbooks/review-bus.md` (only if operator docs need the new command)

Forbidden: `scripts/lib/review_bus.py`, `schemas/**`, A-Conductor repo, `AGENTS.md`,
`CLAUDE.md`, `raw/**`, secrets, portability files owned by GPT Primary
(`scripts/setup_zcode_hooks.py`, `tests/test_setup_zcode_hooks.py`,
`docs/work-orders/WO-ALOOP-ZCODE-20260901.md`), and anything in
`fix/wo-portability-*` lanes.

## Micro-steps

| ID | Goal | Evidence required |
|---|---|---|
| RB-1 | bounded safe task identity (`^task-<id>.json` filename reach) | adversarial RED→GREEN: traversal/slash/control/empty/oversized rejected, no silent sanitize |
| RB-2 | `review open` — exact current HEAD, clean-worktree required, transport=remote-queue, JSON | RED→GREEN + dirty-tree fail-closed test |
| RB-3 | `review ingest` — bounded validated external result (task_id, reviewed_head, task_sha256?, model?, verdict, findings) | fail-closed on wrong task/head/verdict/oversized; extra fields never trusted |
| RB-4 | severity map P0/P1/P2→blocker, P3→note via ONE explicit function; PASS + blocking finding rejected | unit + adversarial tests |
| RB-5 | idempotent replay of the same durable result | same digest re-ingest → no duplicate findings/state corruption |
| RB-6 | thin finding lifecycle: status / resolve(fix_sha) / verify-finding | adapter delegates to engine; no repair execution |
| RB-7 | trusted-evidence separation: record-retest / record-ci / status; reviewer can never forge READY | reviewer PASS alone → allow_complete=false; only verdict+no-blocker+retest@head+CI → READY |
| RB-8 | new SHA invalidates old approval (engine rule preserved) | adapter-level coverage |
| RB-9 | restart durability — fresh bridge instance resumes the same cycle | test with a second instance over the same state dir |
| RB-10 | CLI `python -m conductor review …` — JSON, bounded errors, no traceback for validation failures, no process spawning | subprocess-level CLI tests |

## Verification minimum

- `python -m pytest tests/test_conductor_review_bridge.py -q`
- `python -m pytest tests/test_review_bus.py tests/test_a_loop_review.py tests/test_conductor.py tests/test_kernel_contracts.py -q`
- `python -m py_compile` on changed files; managed Python 3.8 compile smoke
- `git diff --check`, privacy, security scan (--ci baseline), stale-spec, wiki-health
- GitNexus impact before production symbol edits; `detect-changes` before every production commit (Windows FTS extension failure = tool limitation)

## Checkpoints

### 2026-09-02 #1 — RB-1..RB-10 implemented GREEN (GLM5.3-ZCode-MAX)

Commits on this lane: `2a306a32` (claim+WO, gate GO) → `0e456634` (bridge+CLI+contract tests) → `7a5bc5cd` (tmp-repo unit harness + status/resolve contract fixes) → `45bce005` (CLI unknown-task = NO_REVIEW rc 0, aligned with API). Tree clean at each commit.

**RED evidence:** `env -u PYTHONUTF8 -u PYTHONIOENCODING python -m pytest tests/test_conductor_review_bridge.py -q` = collection error `ModuleNotFoundError: No module named 'conductor.review_bridge'` (full contract RED before implementation); then 20 failed / 22 passed against the first implementation draft (dirty-tree fail-closed + API shape defects — see below).

**Design decisions / root causes fixed during GREEN:**
- Unit tests bind to a throwaway real git repo under `tmp_path` (`_mkrepo`), not this development worktree — the exact-clean-HEAD contract otherwise chicken-and-eggs with uncommitted test edits. CLI tests intentionally run against `REPO_ROOT` (clean tree at commit boundaries).
- `status()` on an unknown task returns a bounded `NO_REVIEW` answer (rc 0) — same contract as `ALoopReview.task_gate`; only validation failures are rc 1.
- Dirty probe moved out of gitignored `.tmp` (invisible to `git status --porcelain`).
- `resolve`/`verify_finding` spread the finding fields top-level (machine-readable CLI contract).
- Oversized-result (>64,000 bytes) and >50 findings are separate fail-closed bounds.

**GREEN evidence:** `tests/test_conductor_review_bridge.py` = **43 passed in 19.35s** at `45bce005` (clean tree). Coverage: RB-1 (11 adversarial identity cases incl. `../x`, `..\x`, separators, absolute, control chars, empty, oversized, leading punctuation; no file written before rejection), RB-2 (exact HEAD == `git rev-parse HEAD`, transport=remote-queue, dirty-tree fail-closed, bounded non-empty tests), RB-3 (wrong task / stale+wrong head / unknown verdict / oversized / malformed findings / unknown task / extra fields incl. forged `retest`/`ci`/`ready`/`merge` ignored), RB-4 (`SEVERITY_MAP` P0/P1/P2→blocker P3→note via the single `map_severity`; unknown fails; PASS+P1 rejected with cycle untouched), RB-5 (same-digest replay `duplicate:true`, no finding duplication; different digest same cycle fails closed), RB-6 (resolve bad-sha fail / resolve+verify roundtrip; NO_REVIEW status), RB-7 (PASS alone → `allow_complete:false` with retest+ci reasons; +record-retest still false; +record-ci → READY `allow_complete:true`), RB-8 (`record_retest` at a new sha → `REVIEW_REQUESTED`, approval revoked), RB-9 (fresh instance over same state dir resumes cycle; cross-process: API-opened cycle read by separate CLI subprocess), RB-10 (CLI open→ingest→record-retest→record-ci→READY lifecycle; bounded JSON errors rc 1 without traceback; resolve/verify-finding CLI roundtrip; unknown-task NO_REVIEW rc 0).

**Related regression:** `tests/test_review_bus.py tests/test_a_loop_review.py tests/test_conductor.py tests/test_kernel_contracts.py` = **110 passed / 2 failed** — both failures are the known pre-existing cp874 conductor-search tests on main base `fc9a981d` (root signal `'charmap' codec can't encode '\xab'`; same family as the 21-failure portability baseline), already fixed by the pending `fix/wo-portability-baseline-glm-20260902` PR and outside this lane's claimed scope. NOT caused by this change (this lane does not touch `conductor/__main__.py`).

**Reuse audit:** zero modification to `scripts/lib/review_bus.py`, `scripts/lib/a_loop_review.py`, `schemas/**`; no new transport enum (reuses schema `remote-queue`); no scheduler/mailbox/provider/process spawning anywhere in the bridge; every state write goes through `ReviewBus.publish/add_finding/set_verdict/resolve_finding/verify_finding/record_retest/record_ci`.

**Gates:** `git diff --check fc9a981d..HEAD` PASS · Python 3.8 `py_compile` on all 3 changed py files PASS · privacy "no personal data detected" PASS · security 6,325 tracked / 51 baseline / **0 new** · stale-spec `[OK] no stale specs` · wiki-health **0 hard / 352 advisory**.

**GitNexus:** fresh `analyze --index-only` for this worktree (85,199 nodes / 124,884 edges / 700 flows; FTS extension unavailable on this Windows runtime = tool limitation, graph/impact/detect-changes usable). Impact `conductor/cli.py:main` (the only edited existing symbol) = **LOW / 2 direct / 0 processes**. `detect-changes --scope compare --base-ref fc9a981d` = 5 files / 82 symbols / 3 processes / **risk MEDIUM** (new-file symbols dominate; below the HIGH/CRITICAL stop threshold).

**Remaining:** broad regression sweep, final verdict, handoff.

Next safe action: run the broader conductor/hooks-adjacent regression, then set READY_FOR_GPT_PRIMARY_REVIEW.

### 2026-09-02 #2 — final verdict (GLM5.3-ZCode-MAX)

**Broad conductor-cluster regression:** `tests/test_conductor.py tests/test_conductor_review_bridge.py tests/test_awiki_cli.py tests/test_kernel_contracts.py tests/test_review_bus.py tests/test_a_loop_review.py tests/test_graph_yaml.py tests/test_check_pr_loop.py` = **169 passed / 4 failed in 47.04s**. All 4 failures (conductor TestBridgeSearch ×2, graph-yaml CLI, pr-loop CLI) show the exact `'charmap' codec` cp874 signature — **pre-existing baseline debt on main base `fc9a981d`**, each already fixed by the pending `fix/wo-portability-baseline-glm-20260902` PR (awaiting Primary review), outside this lane's claimed scope. Zero failures attributable to the review bridge.

**Acceptance map (goal criteria → evidence):**
1. Thin bridge on isolated branch — `conductor/review_bridge.py` (+CLI wiring) on `feat/wo-review-bridge-glm-20260902` ✓
2. ReviewBus only review-state authority — every write delegates to `ReviewBus.*`; engine untouched ✓
3. remote-queue transport reused — schema enum, no new transport ✓
4. No schema/core churn — `git diff fc9a981d..HEAD -- scripts/lib/review_bus.py schemas/` empty ✓
5. No A-Conductor mutation — diff touches only the 5 claimed files ✓
6. Safe bounded task identity — RB-1 tests (11 adversarial cases) ✓
7. Exact clean-HEAD binding — RB-2 tests (dirty-tree fail-closed) ✓
8. External result ingestion safe — RB-3 tests (6 fail-closed cases + extra-field ignore) ✓
9. P0/P1/P2 block, P3 notes — `SEVERITY_MAP` + PASS+blocking rejection ✓
10. Replay idempotent — RB-5 same-digest no-op / different-digest fail-closed ✓
11. Reviewer cannot forge retest/CI/READY — RB-7 forged-field test + trusted-op separation ✓
12. Resolve/verify lifecycle — RB-6 + CLI roundtrip ✓
13. New SHA invalidates approval — RB-8 ✓
14. Restart durability — RB-9 fresh instance + cross-process CLI ✓
15. Focused (43/43) + related (110/112, 2 pre-existing cp874) + adversarial pass ✓
16. Privacy/security/stale/wiki-health/diff gates — all PASS (checkpoint #1) ✓
17. GitNexus evidence recorded — checkpoint #1 (impact LOW, detect-changes MEDIUM, 3 processes) ✓
18. This WO holds the complete resumable checkpoint ✓
19. Branch clean and pushed — verified below ✓
20. Status = READY_FOR_GPT_PRIMARY_REVIEW (this checkpoint) ✓

**Claim release:** the lane claim (COLLAB row) is released at handoff — candidate stable at final HEAD, all contract tests green. Residual risk: none known in-lane; the 4 cp874 baseline failures remain on main until the portability PR merges (independent lane).

Next safe action: **GPT Primary independently review exact candidate HEAD, remote diff, trust boundaries, tests, PR/CI, and release.** Do not merge from this lane; do not mark this result as independent acceptance.
