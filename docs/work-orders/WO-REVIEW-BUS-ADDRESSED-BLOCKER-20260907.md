# WO-REVIEW-BUS-ADDRESSED-BLOCKER-20260907 — Issue #54

Status: CLAIMED / READY_FOR_GLM1_RED
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
