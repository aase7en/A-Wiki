# WO-REVIEW-BUS-ADDRESSED-BLOCKER-20260907 — Issue #54

Status: IMPLEMENTED / READY_FOR_GPT1_EXACT_SHA_ACCEPTANCE
Owner: GLM1 / GLM-A implementation; GPT1 independent exact-SHA review + merge authority
Issue: #54 — ReviewBus: addressed blockers must block READY until verified
Repository: A-Wiki
Base: `main@759384116edcc6785bdc9f5d660f166d4940359d`
Branch: `fix/issue-54-addressed-blocker-gate`
Worktree: `<WORKTREE>/A-Wiki-issue54-q25`
Claim: durable COLLAB row + local claim `33ae016c64a0`

## Goal
Keep blocker findings blocking while state is `open` OR `addressed`. Only `verified` releases PASS/READY. Preserve Issue #53 HEAD-rollover semantics and use the existing ReviewBus authority only.

## Read first
1. `AGENTS.md` + `COLLAB.md`
2. Issue #54 comments, especially 5552031076, 5552283324, 5559912777
3. PR #55 / Issue #53 merged behavior
4. `scripts/lib/review_bus.py`
5. focused ReviewBus/ReviewBridge tests

## Allowed scope
- `scripts/lib/review_bus.py`
- `tests/test_review_bus.py`
- `tests/test_review_bus_head_rollover.py`
- this WO + `COLLAB.md` for checkpoint/claim only

## Forbidden
- no `conductor/review_bridge.py` change unless RED evidence disproves its existing `state != verified` behavior
- no second review store/lifecycle/predicate authority
- no A-Conductor mutation, ZRA-2 work, secrets, root checkout mutation, destructive Git, direct main push, or self-merge

## RED-first contract
1. addressed blocker rejects PASS
2. addressed blocker keeps readiness false even with current-head retest + green CI
3. verified blocker permits PASS/READY when all other gates pass
4. open blocker behavior remains blocking
5. non-blocking/note behavior unchanged
6. restart/reload preserves addressed/verified state
7. Issue #53 H1→H2 rollover still clears verdict/CI while preserving findings/state

## Implementation constraint
Use ONE canonical blocker predicate/state set consumed by both `set_verdict()` and `readiness()`. Prefer the minimal ReviewBus-only repair already design-reviewed. Do not weaken `verify_finding()` ordering.

## Verification
- focused new REDs first, proving failure on base
- `python -m pytest -q tests/test_review_bus.py tests/test_review_bus_head_rollover.py tests/test_conductor_review_bridge.py`
- relevant broader ReviewBus regressions
- `python scripts/check-privacy.py`
- `git diff --check`
- remote diff audit + hosted PR CI on frozen exact SHA

## Stop condition
GLM1: freeze one clean pushed exact SHA and stop at `READY_FOR_GPT1_EXACT_SHA_ACCEPTANCE`. GPT1 then independently inspects source/tests/CI and alone decides acceptance/merge.

## Implementation checkpoint — 2026-09-07 (GLM-1)

- Claim verified ACTIVE in COLLAB.md (claimed 2026-09-07, this branch, exact scope; no overlap; no reacquire needed — actual state overrides the stale "expired" expectation). SAFE_TO_MUTATE=YES proven: isolated clean worktree at claim head `b59ed129`, base = `main@759384116edcc6785bdc9f5d660f166d4940359d`, upstream gate PR224/WO163 MERGED (2026-09-07T09:50:42Z).
- **RED-first:** 9 Issue #54 tests appended to `tests/test_review_bus.py`; 5 failed on the unmodified bus exactly on the addressed-blocker contract (PASS accepted, READY flipped true with fresh retest+CI, reload and rollover variants). The strengthened RED-2 proves the exact named hole end-to-end (set_verdict(PASS) SUCCEEDS + readiness READY on the unfixed bus).
- **Fix (minimal, ONE authority):** `_BLOCKING_STATES = ("open", "addressed")` + module-level `_blocking_blocker_ids(doc)` — the single canonical predicate consumed by BOTH `set_verdict()` and `readiness()`; only `verify_finding()` (ordering untouched) moves addressed → verified and releases the blocker. Reason/error messages updated to say "unresolved blockers (open/addressed)". No second predicate, no store/lifecycle change, `conductor/review_bridge.py` untouched (its `state != verified` semantics held under its own suite — no RED justified mutation).
- **Verification:** focused `tests/test_review_bus.py` + `tests/test_review_bus_head_rollover.py` + `tests/test_conductor_review_bridge.py` = **113/113 PASS** (all 9 new REDs GREEN; every pre-existing assertion unchanged). Broader: `test_a_loop_review.py` + `test_agent_claims.py` + `test_agent_preflight.py` = **48/48 PASS**. `python scripts/check-privacy.py` PASS; `git diff --check` PASS. Scope audit: exactly `scripts/lib/review_bus.py` + `tests/test_review_bus.py` changed (within allowed scope).
- Stop state: **READY_FOR_GPT1_EXACT_SHA_ACCEPTANCE** at the frozen pushed head (exact SHA + CI in the PR). GLM1 does not merge; GPT1 owns acceptance/merge.
