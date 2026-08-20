# A-Wiki vNext — Phase 6 Execution Handoff

> **Task ID:** `P6-REMEDIATE-REVIEW-001`
> **Status:** **REVIEW_REQUESTED**
> **Current phase:** Phase 6 — Hook Engine Consolidation
> **Authoritative work order:** `docs/migration/phase-6-hook-engine-work-order.md`
> **Independent review:** `docs/migration/reviews/phase-6-review-local-fcef705c.md`
> **LOCAL_WORKTREE_VERIFICATION:** COMPLETE through GPT Work shell on 2026-08-20
> **LOCAL_SERENA_VERIFICATION:** NOT_REQUIRED by explicit user direction

This is the current durable execution checkpoint. It replaces the earlier local untracked draft that said `REVIEW_REQUESTED`, treated all locked decisions as green, and embedded machine-specific paths. On conflict, the work order defines the Phase 6 contract and the independent review defines the current verdict/findings.

## Current objective and exact task

P6-R01..P6-R07 remediation is complete locally without redesigning the Phase 6 architecture, weakening tests, or starting a later phase. The exact next objective is to create the bounded attributable Phase 6 commit and submit that exact SHA for fresh independent review.

Phase 6 is not yet approved or merged. The remediation candidate is **COMPLETE_VERIFIED locally** against the focused/provider/isolation/acceptance evidence recorded below, but no approval applies until the committed exact SHA passes a new independent review and CI/human merge gates.

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
- local implementation state: **COMPLETE_VERIFIED locally**, uncommitted remediation candidate awaiting exact-SHA independent re-review
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

### Remediation progress — 2026-08-20

- **P6-R01 provider compatibility:** TEST-FIRST reproduced Gemini/Cline bare-runner and malformed-payload defects. Gemini/Cline now enter `--provider ... --event ...`; Cline preserves raw malformed input, no longer depends on `jq`, and supports an explicit Python interpreter. Core/provider tests: `6 passed`; compatibility review: `13 passed`; actual isolated Gemini+Cline E2E: `2 passed` covering valid, empty, malformed, hard-block, and Cline soft-failure paths.
- **P6-R02 deployed registry authority:** Claude/Codex registered hooks now enter provider event sweeps per existing matcher block; registry owns registered membership/order while legacy non-registry utilities remain explicit. Focused R02 result: `12 passed / 2 R05 tests intentionally deferred`, followed by exact-order provider-path tests `4 passed`.
- **P6-R03 executable availability:** registry validation is structural only; executable availability is handled after hard/soft classification. Missing hard blocks; missing soft is observable and nonblocking. Focused result: `5 passed`.
- **P6-R04 startup/privacy/exit surface:** invalid `HOOK_TIMEOUT` no longer crashes module import; startup/registry failures expose constant safe diagnostics and normalize terminal failure to exit `2`. Focused result: `6 passed`, including sanitizer fallback and 0/2 contract checks.
- **P6-R05 Codex full structured parity:** `HOOKS_CONFIG` is now the full tracked Codex model (event sweeps plus compatibility utilities). Checker uses recursive exact structure, so wrong matcher, wrong command, missing observer, order, or extra/missing blocks fail. Focused result: `5 passed`; `setup-codex-config.py --check` passes; tracked hooks SHA was unchanged by check mode.
- **P6-R06 isolation + provider E2E:** added explicit seams for A-Flow state, destructive-git repo root, live-dashboard log/session-id, memory ledger, self-audit blackboard, and Cline log/interpreter. Former live-state tests now use temporary state/repos/files, including in-process synthetic runner tests. Actual isolated Gemini+Cline E2E: `2 passed`. Final combined Phase 6 suite ran twice: `210 passed / 1 skipped / 3 warnings` on both rounds, with the same 9-path live-state SHA/missing snapshot unchanged after each round.
- **P6-R07 handoff/privacy:** local handoff is reconciled to `CHANGES_REQUIRED`, contains no machine-specific absolute worktree path, and explicit handoff scan reported zero Windows user/worktree paths, macOS/Linux home paths, secret-like tokens, or conflict markers. Tracked privacy gate also passed.
- **Acceptance gates completed before full regression:** registry `29 hooks (17 hard, 12 soft)`; Codex exact structured parity PASS; production Python compile / Claude-Codex-Gemini JSON parse / Cline shell syntax PASS; handoff path-secret-conflict scan zero; tracked privacy PASS; security `6176 tracked / 49 baseline / 0 new`; `git diff --check` PASS; wiki-health `0 hard / 48 baselined / 355 advisory` with semantic diff unchanged; CI secret smoke `safe=0 / planted-secret=2`.
- **Full-regression platform recovery checkpoint:** a Serena 502 occurred while running `tests/test_link_agent_configs.py`, but recovery found no live pytest process and a complete durable report at the isolated temp location. Result: `15 passed / 6 failed / 27 warnings in 298.24s`. Five failures are cp874 parent-reader/test-harness failures where `result.stdout` became `None`; one is the pre-existing MSYS/Git-Bash symlink-copy behavior test. These are classified outside the Phase 6 hook-engine implementation scope and must not be repaired on this branch merely to make the full suite green.
- **Remaining platform-family rechecks under Git Bash precedence:** `test_global_env_system.py = 17 passed`; `test_verify_model_routing.py = 2 passed`; `test_lean_session_start.py = 15 passed`; `test_model_router_policy.py = 10 passed`; `test_pre_commit_syntax_gate.py = 16 passed`. `test_link_my_skills.py` still has one cp874 parent-reader failure (`result.stdout is None`) and is likewise infrastructure debt outside Phase 6. `test_export_notebooklm.py` was intentionally not rerun because its regression test writes real `exports/notebooklm/*` artifacts in the repository and exposes no isolation seam; prior failure belongs to the same shell/path family and rerunning it would violate the no-generated-drift safety boundary.
- **Next implementation boundary:** verify final semantic diff/live-state/handoff privacy after these rechecks, prepare the exact bounded staging manifest, then create and push the attributable Phase 6 commit for independent re-review. No Phase 7 or later work is authorized.

## Decisions preserved

- Hooks remain police, not manager.
- Phase 7 owns the model/provider control plane and is **NOT_STARTED**.
- Phase 8 owns the eval-vs-routing split and first automated reviewer adapter foundations.
- Phase 9 owns A-Loop v2.
- Phases 10–11 remain optional-module/docs phases.
- Phases 12–16 remain solely defined by the multi-agent/orchestrator roadmap and are **NOT_STARTED**.
- A-Wiki is the durable brain/governance surface; Conductor is orchestration; Serena or equivalent local tooling is the execution hand. These are not one monolith.

## DECISION_REQUIRED

None for architecture or current remediation. The PR #16 continuity handoff has already been reconciled locally without overwriting the Phase 6 implementation WIP.

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

1. Continue the remaining platform/full-regression rechecks in small isolated batches; after any Serena transport loss, recover the original process/report before deciding whether a retry is safe.
2. Classify any residual failures as Phase 6 regressions vs pre-existing/out-of-scope platform infrastructure; do not repair unrelated subsystems on this branch.
3. Re-run only the final bounded Phase 6 gates needed after any additional Phase 6 changes; if no Phase 6 changes occur, reuse the already-recorded green acceptance evidence.
4. Inspect the final semantic diff and bounded staging manifest; explicitly exclude `.serena/` and semantic-empty generated wiki/status noise.
5. Commit and push an attributable Phase 6 SHA.
6. Request a fresh independent review of that exact SHA.
7. Advance only after PASS plus CI and the human merge gate.

## Single next safe action

Run the next small platform/full-regression recheck (`tests/test_link_my_skills.py`) with Git Bash precedence and isolated TEMP/TMP. If Serena transport drops, recover the original process/report before any retry.

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
