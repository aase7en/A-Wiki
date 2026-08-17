# A-Wiki vNext — Phase 1 Re-review

> Review target: `328f9a6687d5cd016870ef8cb19f34eed55c7c1c`
> Reviewer: ChatGPT / Architecture + QA
> Date: 2026-08-17
> Verdict: **PASS_WITH_NOTES**
> Phase 2 authorization: **GRANTED** after syncing this review commit

## Resolution of prior findings

### R-P1-001 — RESOLVED

`subagent-eval.yml` now separates the scheduled/report path from mutation:

- `eval` runs on schedule/dispatch with `contents: read` and writes results/race history/previews to artifacts/issues only.
- prior direct `git commit` + bare `git push` paths are removed from the scheduled job.
- adaptive-routing and cost-optimization apply behavior moved into a `promote` job that is `workflow_dispatch`-only.
- promotion writes to `promotion/subagent-eval-*` and opens a PR instead of pushing the checked-out default branch.
- regression tests assert no bare push and that scheduled execution is read-only.

Phase-1 safety objective is satisfied: no reviewed scheduled path in this workflow directly mutates `main`.

### R-P1-002 — RESOLVED

Telegram report logic was extracted to `scripts/hermes/telegram_report.py`.

`chunk_report()` slices the complete source text rather than `min(len(text), 4000)`, preserves order/content, accounts for message framing, and has deterministic tests covering >8k and 20k character payloads. `provider-balance.yml` calls the tested helper.

### R-P1-003 — RESOLVED

Canonical apples-to-apples baseline was established using the same command/environment class:

- clean base `e532d2f0`: `3 failed, 2513 passed, 17 skipped`
- fixed Phase-1 head: `3 failed, 2550 passed, 17 skipped`

The same three test IDs fail on both base and head. Phase 1 therefore introduces **0 new failures**; the additional passing tests are Phase-1 coverage.

The old 2,867-test Phase-0 capture remains historical evidence only and is correctly distinguished from the canonical clean baseline.

### R-P1-004 — RESOLVED

`agent-model-scan.yml` no longer masks PR creation failure with `|| echo`. It explicitly checks for an existing PR and otherwise lets `gh pr create` fail the step. The promotion gate is now truthful/fail-closed.

---

## Architecture assessment

Phase 1 successfully addresses its intended safety/stability scope:

- SessionStart can no longer silently rebase a non-main branch.
- dirty tracked worktrees prevent automatic sync.
- sync is fast-forward-only.
- model scout scheduled automation is report-only by default.
- model pool runtime telemetry no longer churns Git history.
- fail-open daily maintenance is retired.
- duplicate Pages deploy workflow is retired.
- provider balance reporting uses minimal contents permission and no mutable third-party `@master` action.
- subagent eval scheduled execution no longer directly commits/pushes repository state.
- model/routing mutations are behind named promotion branches + PR review.

## Note N-P1-001 — race-history promotion wording/behavior mismatch (non-blocking)

The `subagent-eval` scheduled job stores race history under `.tmp/subagent-eval/races-history` for artifact upload. The promotion job restores the artifact and its final commit stages `evals/subagents/races/`, but no explicit copy from restored `.tmp/.../races-history` into `evals/subagents/races/` is visible before the commit.

This means the promotion PR may contain results/policy changes but not newly generated tracked race-history snapshots, despite comments/body wording that mention "results + races".

This does **not** violate Phase-1 safety and is not a blocker. Record it for the Phase-8 eval/promotion redesign, where the intended retention policy for race telemetry vs promoted historical snapshots should be made explicit:

- either race history remains artifact/runtime telemetry only, and wording/staging should say so; or
- explicit promotion should copy selected race snapshots into the tracked history before PR creation.

Do not expand Phase 2 merely to address this note unless it interferes with CI/health refactoring.

---

# Phase 2 Work Authorization

Phase 2 may begin after the executor fast-forward syncs the current migration branch and reads this file.

## Phase 2 goal

Make CI/health checks truthful, deterministic, and authoritative for the A-Wiki kernel without mixing expensive domain-specific regression suites into every core change.

## Required Phase 2 order

### P2.1 — Fix the canonical pre-existing security-scanner failure first

Base/head both fail `test_scanner_actually_flags_a_planted_secret`. Treat this as the first hard-gate defect.

- root-cause before fix
- preserve failing test as regression evidence
- move fragile repository scan orchestration toward Python (`scripts/security/scan_repo.py`) as planned
- support filenames safely; do not silently cap scan coverage
- no secret/private data may be added to fixtures

### P2.2 — Build truthful wiki health

Replace superficial/fail-open health behavior with real validation through a canonical script such as `scripts/health/wiki_health.py`.

Minimum checks from the master plan:

- broken wikilinks/targets
- dangling graph edges where applicable
- orphan pages (report/advisory unless policy says hard fail)
- invalid frontmatter
- duplicate aliases
- stale generated context/indexes
- unregistered skills/generated-surface drift
- invalid integration references once the registry exists

Separate hard errors from advisories.

### P2.3 — Refactor core CI vs domain regression

Create/shape `ci-core.yml` (or an equivalent clearly named core workflow) so core changes validate:

- privacy/security
- syntax
- registry/generated surfaces
- hooks
- memory/core libraries
- router/flow
- MCP smoke
- wiki freshness/health
- unit/core readiness

Move expensive Monte Carlo/quant/domain regression out of unconditional core CI into path-triggered or scheduled domain workflow(s). Preserve coverage; do not simply delete tests.

### P2.4 — Add MCP + hook smoke and cross-agent hard-gate parity

Ensure critical safety checks do not depend solely on Claude-specific hooks. CI/preflight must be able to enforce the hard invariants across executor vendors.

### P2.5 — Resolve remaining canonical baseline failures that fall inside Phase-2 scope

Current clean baseline failures:

1. secret scanner planted-secret test — security; **must fix in Phase 2**
2. dashboard size budget — determine whether this belongs to core CI or dashboard/domain scope; fix or explicitly reclassify with evidence
3. neural-spine MCP TOOLS parity — MCP/core; **should fix in Phase 2**

Do not hide failures by weakening assertions without a documented contract change.

## Phase 2 regression rule

Use the canonical clean-base baseline established in Phase 1. At Phase-2 completion, run the same full-suite command and report exact failing test IDs/counts. New failures are not acceptable unless explicitly approved as a contract change.

## Phase 2 stop rule

After implementation/testing:

1. commit small coherent changes
2. push only `refactor/awiki-kernel-vnext-clean`
3. update migration evidence
4. STOP before Phase 3
5. write a short review handoff in GitHub/repo state; the user should not need to copy long logs

Do not begin the formal Kernel Contract / Agent Review Bus schema implementation (Phase 3) until Phase 2 receives reviewer PASS.
