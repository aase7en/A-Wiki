# A-Wiki vNext — Phase 6 Execution Handoff

> **Task ID:** `P6-REMEDIATE-REVIEW-001`
> **Status:** **CHANGES_REQUIRED**
> **Current phase:** Phase 6 — Hook Engine Consolidation
> **Authoritative work order:** `docs/migration/phase-6-hook-engine-work-order.md`
> **Independent review:** `docs/migration/reviews/phase-6-review-local-fcef705c.md`
> **LOCAL_WORKTREE_VERIFICATION:** COMPLETE through GPT Work shell on 2026-08-20
> **LOCAL_SERENA_VERIFICATION:** NOT_REQUIRED by explicit user direction

This is the current durable execution checkpoint. It replaces the earlier local untracked draft that said `REVIEW_REQUESTED`, treated all locked decisions as green, and embedded machine-specific paths. On conflict, the work order defines the Phase 6 contract and the independent review defines the current verdict/findings.

## Current objective and exact task

Remediate P6-R01..P6-R07 without redesigning the Phase 6 architecture, weakening tests, or starting a later phase.

Phase 6 is not complete. Implementation exists only as uncommitted local work and independent review found material defects. No approval applies until a committed exact SHA passes a new review and CI.

## Verified repository/worktree state

- repository: `aase7en/A-Wiki`
- local project/worktree identity: `A-Wiki-vnext-clean`
- branch: `refactor/awiki-hook-engine`
- committed HEAD: `fcef705cdf8e0814927d498bdd467c8987fcc59e`
- upstream: `origin/refactor/awiki-hook-engine` at the same SHA
- `origin/main`: `51258fac665add6e65e6f4a239fda5d597670f0e`
- merge-base: `51258fac665add6e65e6f4a239fda5d597670f0e`
- distance from origin/main: 0 behind / 1 ahead
- remote implementation state: work order only; no Phase 6 implementation commit
- local implementation state: **PARTIAL**, uncommitted, independently reviewed
- live claims: zero across all discovered worktree claim stores
- open Phase 6 implementation PR at audit time: none
- docs-only continuity branch: `docs/awiki-continuity-recovery-20260820`
- durable checkpoint transport: draft PR #16 targeting the Phase 6 branch; the PR's current head is the immutable documentation target

The separate local `main` worktree is 24 commits ahead and 104 behind `origin/main` with unrelated dirty work. Historical tool worktrees also contain type-change noise. They are protected other work for this task: do not reset, clean, merge, rebase, switch, or otherwise normalize them.

## Dirty-state classification

The local status contains:

- 14 semantic Phase 6 files listed below
- 16 tracked entries whose Git diff is empty (Windows stat/EOL noise)
- pre-existing untracked `.serena/` tooling state, which is not Phase 6 product work and must not be modified or committed

Do not use status alone to expand Phase 6 scope. Use semantic diff evidence.

## Phase 6 semantic files

```text
.claude/settings.json
.codex/hooks.json
scripts/hooks_runner.py
scripts/setup-codex-config.py
scripts/hooks/providers.py
scripts/hooks/registry.py
tests/test_hook_engine.py
tests/test_hooks.py
tests/test_a_focus_hook.py
tests/test_a_route_hook.py
tests/test_compaction_suggest.py
tests/test_hook_stdout_encoding.py
tests/test_self_audit_visibility.py
docs/migration/phase-6-execution-handoff.md
```

## Completed work and evidence

The executor implemented a registry/runner/provider consolidation attempt plus test/config changes and reported:

- focused Phase 6 suite: 123 passed / 1 skipped / 3 warnings / 0 failures
- registry: 29 hooks / 17 hard / 12 soft
- privacy gate: pass
- security scan: pass
- CI secret-hook smoke: pass
- `git diff --check`: pass
- historical full suite: 2,827 passed / 41 failed / 17 skipped / 8 warnings

These are useful evidence, not completion proof. The focused tests omit or weaken several required paths, and no final full suite exists at a committed Phase 6 SHA.

## Locked decisions after independent review

| Decision | Verdict |
|---|---|
| D-P6-001 malformed payload | **FAIL overall** |
| D-P6-002 duplicate hook IDs | **PASS** |
| D-P6-003 canonical provider wiring | **FAIL** |
| D-P6-004 diagnostic sanitizer failure | **FAIL** |
| D-P6-005 Codex generated hard-gate surface | **PASS narrowly; generated/tracked definition of done fails** |
| D-P6-006 named/legacy compatibility | **FAIL overall** |

The detailed contract, evidence, bypass/regression analysis, and required verification are in the independent review record.

## Open findings

- **P6-R01 CRITICAL:** supported Gemini/Cline bare-runner paths break; malformed input is collapsed in Cline
- **P6-R02 HIGH:** Claude/Codex deployed paths do not make registry selection/order authoritative
- **P6-R03 HIGH:** a missing soft executable invalidates the registry and blocks
- **P6-R04 HIGH:** startup/config failures can leak raw paths/tracebacks and exit 1
- **P6-R05 HIGH:** Codex generator/tracked config drift; checker can approve wrong matcher/command
- **P6-R06 MEDIUM:** focused tests mutate live repository state
- **P6-R07 MEDIUM:** earlier handoff used machine-specific paths

## Decisions preserved

- Hooks remain police, not manager.
- Phase 7 owns the model/provider control plane and is **NOT_STARTED**.
- Phase 8 owns the eval-vs-routing split and first automated reviewer adapter foundations.
- Phase 9 owns A-Loop v2.
- Phases 10–11 remain optional-module/docs phases.
- Phases 12–16 remain solely defined by the multi-agent/orchestrator roadmap and are **NOT_STARTED**.
- A-Wiki is the durable brain/governance surface; Conductor is orchestration; Serena or equivalent local tooling is the execution hand. These are not one monolith.

## DECISION_REQUIRED

None for architecture. The documentation recovery PR must be reconciled without overwriting the 14-file local WIP; this is a normal execution/review step.

## Do not do

- do not reset, clean, stash, rebase, delete, or overwrite local WIP
- do not touch the unrelated dirty/diverged `main` worktree
- do not modify or commit `.serena/`
- do not weaken tests or bypass hard gates
- do not regenerate config during continuity recovery
- do not edit `main` directly
- do not begin Phase 7 or Phases 12–16
- do not grant PASS to an uncommitted or different SHA

## Ordered TODO

1. Reconcile the draft continuity PR #16 into the Phase 6 branch without overwriting local WIP.
2. Remediate P6-R01 test-first.
3. Remediate P6-R02..P6-R07 in severity order.
4. Run isolated focused/provider-parity/generated-config/privacy/security/CI-secret/diff/full-regression gates.
5. Commit and push an attributable Phase 6 SHA.
6. Request a fresh independent review of that exact SHA.
7. Advance only after PASS plus CI and the human merge gate.

## Single next safe action

Reconcile the draft continuity PR #16 into the verified Phase 6 branch without overwriting the local semantic delta; then begin the P6-R01 test-first remediation slice.

## Resume checks

At each new session, repeat read-only identity/ownership checks through any available local tool surface:

```text
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git status --short
git remote get-url origin
git rev-parse '@{upstream}'
git rev-parse origin/main
git merge-base HEAD origin/main
git worktree list --porcelain
git diff --name-only
git diff --check
```

Also inspect every local claim store and all open A-Wiki pull requests. Stop if the branch, SHA, scope, ownership, or diff provenance changed.

## Resume success condition

A fresh worker may continue only when the identity/ownership gate matches this checkpoint and no conflicting live claim exists. The next implementation boundary is P6-R01 only.

<!-- durable-continuity: 2026-08-20; local-worktree-verification=complete -->
