# A-Wiki vNext Migration — Plan & Tracking Log

> Living document for the A-Wiki vNext migration. The current implementation branch is **`refactor/awiki-hook-engine`**; the current phase contract is `docs/migration/phase-6-hook-engine-work-order.md`.
> Source of authority: A-WIKI-MASTER-DEVELOPMENT-PLAN, `docs/architecture/A-WIKI-KERNEL.md`, this plan, the approved orchestrator/review-bus plans, and the current phase work order in that order.
> Current state: Phase 5 is **PASS + MERGED**. Phase 6 is **CHANGES_REQUIRED** after independent review of an uncommitted local snapshot based on `fcef705cdf8e0814927d498bdd467c8987fcc59e`; see `docs/migration/reviews/phase-6-review-local-fcef705c.md`.
> Operating model: select roles by capability. A high-reasoning agent acts as architect/reviewer; a cost-effective or local agent may execute; deterministic tools verify. Provider and model names are runtime candidates, never stable policy.
> Local state note: GPT Work shell access mechanically verified the Phase 6 worktree, branch, HEAD, upstream, semantic diff, all discovered worktrees, and local claim stores on 2026-08-20. **LOCAL_WORKTREE_VERIFICATION: COMPLETE**. Serena was explicitly not required by the user.
> Rule: one phase per review cycle. Security leak / data loss / repo corruption = immediate stop.

## Guardrails (binding for every phase)

1. Work only in the branch/worktree authorized by the current phase work order. For Phase 6 this is `refactor/awiki-hook-engine` — never `main`, and never an unrelated or forensic checkout.
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
| 1 | Stabilize automation (Priority #1: harden `session_start.py::git_pull`; stop ungated main mutation; retire duplicate/fail-open workflows; remove model telemetry Git churn; pin/fix Actions) | ✅ **PASS** — merged; review cycle closed before Phase 2 | `d4223d90` `77bb1f77` `a68e0c44` `8ff7d8fd` `cccb10a6` + doc commit |
| 2 | CI & health refactor (`ci-core.yml`, domain split, real `wiki_health.py`, Python security scan, MCP/hook smoke, integration-registry validation) | ✅ **PASS** — PR #11 merged | post-merge main `05140b153c8838ba93bfb005a35e1a607cd994a7` |
| 3 | Kernel contract (`A-WIKI-KERNEL.md`, `config/awiki.yaml`, `config/integrations.yaml`, intake/storage/project-memory protocols) + formalize `awiki-review/v1` protocol/schema design | ✅ **PASS** — PR #13 merged | reviewed head `dfd4946112a68d2933ece276462193f1583ed6e9`; merge `2e84759ca21e29bd007e4c2a0787f06a54658bf5` |
| 4 | Project adapter (`scripts/project/{attach,status,validate}.py`, schema, cross-platform tests) | ✅ **PASS** — PR #14 merged | reviewed head `6c75f936b5bc99f6ad8deb4964f3e6c1efc08a77`; merge `10507ceec1c286c53f62e331813692c9e2225e81` |
| 5 | Memory layers (L0–L5 separation, experiment memory, promotion pipeline, privacy gate) | ✅ **PASS** — PR #15 merged | reviewed head `5def54757ed7189f6408878a911f6bcd785d0adc`; merge `51258fac665add6e65e6f4a239fda5d597670f0e` |
| 6 | Hook engine consolidation (lifecycle runner, unit tests for every hard gate) | ⚠️ **CHANGES_REQUIRED** — local snapshot reviewed; implementation not pushed; local verification complete | work-order HEAD `fcef705cdf8e0814927d498bdd467c8987fcc59e`; `reviews/phase-6-review-local-fcef705c.md` |
| 7 | Model control plane (`scripts/lib/providers/`, `config/models/` policy-vs-runtime split) | ⬜ **NOT_STARTED** | — |
| 8 | Eval vs routing promotion split + first automated reviewer adapter/review-state foundations | ⬜ **NOT_STARTED** | — |
| 9 | A-Loop v2 + connect improvement-loop states to review verdict/state machine | ⬜ **NOT_STARTED** | — |
| 10 | Optional external modules (world-intel MCP — lazy, no vendoring) | ⬜ **NOT_STARTED** | — |
| 11 | Documentation slimming + review-bus operator docs | ⬜ **NOT_STARTED** | — |

Phases 12–16 are **NOT_STARTED** and are defined only in `docs/migration/awiki-multi-agent-orchestrator-roadmap.md`: Agent Registry & Availability, Assignment Engine, Orchestrator Service + MCP, Operator UI/integrations, and Autonomous Loop Hardening. This plan points to that sequence instead of duplicating it.

## Parallel Track — Agent Review Bus

Architecture plan: `docs/migration/awiki-agent-review-bus-plan.md`.

Purpose: remove the user as the copy/paste transport between executor and reviewer agents while preserving exact-SHA review, durable findings, and human control of high-risk decisions.

Current durable flow:

```text
capable executor
  -> implement/test/commit/push exact SHA
  -> independent capable reviewer
  -> durable PASS or stable CHANGES_REQUIRED findings
  -> executor fixes/retests/resubmits
  -> READY only after review + CI gates
```

The Phase 6 independent review targeted an uncommitted local snapshot. Its findings are durable, but it cannot grant approval to an immutable implementation SHA. Remediation must be committed/pushed and independently reviewed again at the exact new HEAD.

Do **not** pause or reorder the migration to build a large orchestrator. Phase 8 owns the first automated reviewer adapter foundations; Phases 12–16 own the wider orchestrator roadmap.

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

## Phase 1 Log (2026-08-17)

Executed in entry order P1.1 → P1.5 on the clean worktree; every item TDD (failing test first):

- **P1.1 `d4223d90`** — `session_start.py::git_pull` DISC-001 guards: G1 main-branch-only, G2 clean tracked tree (untracked OK), G3 `--ff-only` (no rebase/merge/autostash ever), G4 diverged-main warns without recovery. Z2 wiring dropped from this path (no rebase → no lost commits here). Tests: 11 new (7 red first), lean+encoding suites green (73).
- **P1.2 `77bb1f77`** — `agent-model-scan.yml` promotion gate: scheduled runs dry-run report + candidate issue; `--apply` only via dispatch `apply_swaps=true` → `promotion/agent-model-swap-*` branch + PR; `pull-requests: write` declared; no bare `git push`. Tests: 4 gate (red first) + 16 script tests green.
- **P1.3 `a68e0c44`** — model-pool telemetry out of git: workflow report-only (`contents: read`, artifact upload), `model-pool.json` `git rm --cached` + gitignored (runtime cache; consumers degrade gracefully via `load_pool` error path). Tests: 4 gate (red first) + model-intel suite green.
- **P1.4 `8ff7d8fd`** — retired `daily-maintenance.yml` (fail-open `|| echo OK` + auto-commit main path) and `deploy-awiki-live.yml` (duplicate Pages deploy; nothing pushes gh-pages; `pages-deploy.yml` already stages minimal `_site`). Reference inspection recorded in test docstring. Tests: 2 retire-assertions (red first) + health-digest suite green.
- **P1.5 `cccb10a6`** — `provider-balance.yml`: Telegram was receiving a literal `cat` string (`with:` never shell-expands) — replaced unpinned `telegram-action@master` with stdlib Bot-API POST (4096-char chunking), added `permissions: contents: read` + report artifact. Tests: 4 gate (red first), 14/14 green; embedded python compile-checked.
- **Regression set (full suite on clean branch, 2026-08-17)**: **3 failed / 2,538 passed / 17 skipped** (522.34s). All 3 failures are pre-existing on `origin/main` and already recorded in Phase 0 baseline §7 / DISC-002 — `test_scanner_actually_flags_a_planted_secret` (scanner crash unpacking PATTERNS), `test_file_under_60kb` (dashboard 82,986 B > 80 KB), `test_tools_dict_has_all_neural_spine_tools` (untracked `design_quality_gate`). Phase 1 diff touches none of their files → **0 new failures**. Deferred to Phase 2 as planned.

Phase 1 exit state: no scheduled automation can mutate `main` ungated — every remaining writer is either report-only (artifacts/issues) or behind an explicit dispatch gate + PR.

## Phase 1 Remediation Log (2026-08-17)

Review `docs/migration/reviews/phase-1-review-0a4ffa0d.md` → **CHANGES_REQUIRED** (R-P1-001..004). Fixed in order, each TDD:

- **R-P1-001 (BLOCKER) `9c577354`** — `subagent-eval.yml` split into 2 jobs: `eval` (schedule+dispatch, `contents: read`, results/races/previews are artifacts + issue only; removed "Commit new results file", race-history git snapshot, and both auto-apply direct commit/push paths) and `promote` (dispatch-only, `needs: eval`, restores artifacts, applies adaptive-routing + cost-optimizer, lands everything on `promotion/subagent-eval-*` + PR). 5 gate tests red-first.
- **R-P1-002 (MAJOR) `14cbbcf6`** — new `scripts/hermes/telegram_report.py` `chunk_report()` chunks the ENTIRE report (header + `(i/n)` framing, ≤4,096/message); the P1.5 inline sender had truncated at 4,000 chars. 6 deterministic tests (>8k synthetic: content exactly once, in order, all sizes); dry-run smoke: 9,000 chars → 3 messages, max 3,610. `provider-balance.yml` now calls the helper.
- **R-P1-003 (MAJOR)** — canonical clean-base comparison established (exact command `python -m pytest tests/ -q --tb=line`, detached worktree at base):

  | Baseline | Context | Result |
  |---|---|---|
  | Phase-0 contaminated | pre-remediation history w/ 24 carried commits | 2,856 passed / 9 failed / 2 skipped (2,867 collected) |
  | **Canonical clean-base** | `e532d2f0` (branch base) | **2,513 passed / 3 failed / 17 skipped** (466.83s) |
  | Phase-1 head (pre-remediation) | `0a4ffa0d` | 2,538 passed / 3 failed / 17 skipped (522.34s) |
  | Phase-1 fixed head | post R-P1-001..004 | **2,550 passed / 3 failed / 17 skipped** (457.64s) — failing IDs identical to base; +37 passed = Phase-1's new tests (11 git-pull + 20 workflow gates + 6 telegram) |

  **Apples-to-apples verdict: 0 new failures** — same 3 pre-existing failing test IDs at base `e532d2f0` and fixed head, same skip count; the only delta is Phase-1's own green tests.

  Failing test IDs are **identical** across base and head: `test_scanner_actually_flags_a_planted_secret` · `test_file_under_60kb` · `test_tools_dict_has_all_neural_spine_tools` — all pre-existing on `origin/main`, none touch Phase-1 files. Head's +25/+12 passed vs base = Phase-1's own new tests.
- **R-P1-004 (MINOR) `3b7989ee`** — `agent-model-scan.yml` PR creation fail-closed: removed the `|| echo` success-masking fallback; explicit `gh pr list --head` detection; a failed creation fails the step.

## Phase 2 Log (2026-08-17)

Executed in review-mandated order P2.1 → P2.5, each TDD (red-first):

- **P2.1** — root cause of `test_scanner_actually_flags_a_planted_secret`: builtin fallback patterns in `_scan_staged_diff.py` were 2-tuples while the loop unpacks 3 — any env without PyYAML crashed the scanner (= fail-open layer-2 hole). Fixed (builtin entries carry allowlist slot) + 2 regression tests. New `scripts/security/scan_repo.py` (Python orchestrator: `git ls-files -z` spaces/Unicode-safe, no `head -5000` cap, binary skip, same yaml pattern source, exclude globs, `--ci`, legacy-debt ratchet `--baseline`) replaces the fragile CI shell loop whose line-collapse bug had masked **49 real findings** — recorded in `scripts/security/baseline.txt`. 10 tests.
- **P2.2** — `scripts/health/wiki_health.py` truthful health: HARD = broken wikilinks (all 4 repo wikilink dialects: bare slug / wiki-relative / `wiki/`-prefixed / non-wiki paths), invalid frontmatter, stale generated context + skill-surface drift (subprocess reuse); ADVISORY = orphans, duplicate aliases, dangling graph edges (real `.wiki-graph.json` schema incl. `broken` flags); integrations check reports SKIPPED until Phase 3. Ratchet baseline: 48 legacy wikilink debt keys (`scripts/health/wiki-health-baseline.txt`). 12 tests. Naive first scan said 1,172 hard errors; correct dialect support + templates exclusion → 48 genuine debt.
- **P2.3** — `ci.yml` split: `ci-core.yml` (privacy/syntax, Python security scan, registry consistency, truthful wiki health, unit suite, readiness — all preserved) + `domain-tests.yml` (scipy/MC/notebook regression, path-triggered on quant paths + weekly + dispatch; coverage preserved verbatim, not deleted).
- **P2.4** — cross-agent parity smokes in ci-core: MCP server import + tool-surface assertion (30 tools incl. claim/memory/route families) and hook-runner smoke proving the vendor-neutral runner honors block codes (clean payload → exit 0; planted token → BLOCKED exit 2). Also added the missing `tests/fixtures/sample-input.json` AGENTS.md always referenced.
- **P2.5** — closed both remaining canonical baseline failures: neural-spine `design_quality_gate` tracked + behavioral test; dashboard budget 80→84 KB as a documented contract change with commit evidence (c30b9876 + ec77ddc4), following the test's own 4-raise convention.
- **Regression (same command as canonical base)**: **0 failed / 2,584 passed / 17 skipped** (461.16s). Canonical base was 3 failed / 2,513 passed / 17 skipped — all 3 baseline failures closed by P2.1/P2.5, **0 new failures**, +71 passed = Phase 1+2 new tests. Full suite green (exit 0) for the first time in the migration.

## Phase 3 Log (2026-08-18)

Kernel Contract only — no orchestrator, no attach/status, no Graft install (G0 contract-only). Base main: `ef0eef0944889c3a43a2aa4ea1373d1c0c7faf80`. Every artifact TDD (red-first):

- **`9a0d985e` — contract schemas + configs**: `schemas/awiki-task/v1` (capability-based assignment — vendor names only as runtime candidates, 7 execution modes, stop states, claims-as-leases extending `task_board`), `schemas/awiki-review/v1` (verdicts + finding lifecycle codified from the lived Review Bus practice: `R-*-NNN`, blocker→note, open→verified, SHA-attributable cycles), `schemas/awiki-handoff/v1` (extends the handoff.md chunk system with `decisions`, `reproduce_commands`, `context_queries`), `schemas/awiki-integrations/v1`, `config/awiki.yaml` (durable-vs-runtime + control-plane-vs-project-state boundaries, memory-promotion pipeline, capability vocabulary source, G0 code-context operations), `config/integrations.yaml` (9 entries; graft = MODULE+PATTERN default-off lazy cache-never-committed; deer-flow REJECT). Vendor-neutrality enforced by a test that scans the capability enum for vendor tokens.
- **`8f338174` — deterministic validator + wiring**: `scripts/health/validate_integrations.py` (pure, side-effect-free: schema key, classification enum, external default-off+lazy, cache `commit:false`, dangling reference paths). `wiki_health.check_integrations` (P2.2 forward hook) now validates for real on every health/CI run — the "registry arrives in Phase 3" skip retired; tmp-repos without a registry still skip visibly. 8 TDD tests.
- **`a58906c6` — `docs/architecture/A-WIKI-KERNEL.md`**: identity is/is-not, contract surface, roles/capabilities/availability/modes, state boundaries, memory promotion, ProjectCodeContextProvider vocabulary (`status/orient/find/file_api/trace/search/freshness`) + routing rule, integration gate, hard invariants, explicit not-this-phase hooks.
- Gates: privacy ✓ (one false-positive `sk-` inside "ta**sk**-review-handoff" reworded), scan_repo ✓ (49 known/0 new), wiki_health ✓ (0 hard/48 baselined; integrations check active), focused suites 91+16+15 passed. Canonical suite: see Review History row.

## Phase 2 Remediation Log (2026-08-17)

Review `reviews/phase-2-review-dff83ebb.md` → **CHANGES_REQUIRED** (R-P2-001..004 + note R-P2-005). Fixed in the review's mandated order, each TDD:

- **R-P2-002 (BLOCKER) `a127431a`** — `scan_file` streams EVERY line (`io.TextIOWrapper` line iteration, line numbers preserved); the single 256 KiB read had made secrets past that boundary invisible. NUL-sniff window (8 KiB) is binary detection only. Tests: >256 KiB planted secret detected (line 4001), >300 KiB single-line boundary case, `CHUNK_BYTES` must not reappear.
- **R-P2-003 (BLOCKER) `a127431a`** — baseline keys now `path::pattern::sha256(match)[:16]` + **Counter multiplicity** — coarse path::pattern keys had suppressed NEW same-pattern findings in baselined files. Tests: different same-pattern token fails; extra identical occurrence beyond count fails; baseline holds no raw secret (digest only). `baseline.txt` regenerated: 49 fingerprint keys, 0 raw values.
- **R-P2-004 (BLOCKER)** — every wiki-health identity rendered via `.as_posix()` + `_hard_key` backslash normalization → identical baseline keys on Windows/Linux/macOS; `wiki-health-baseline.txt` regenerated portable (48 keys, 0 backslashes). Tests: no `\` in any identity; separator variants collapse to one key.
- **R-P2-005 (NOTE)** — frontmatter check reports `SKIPPED — PyYAML unavailable` in `report.skipped` instead of silently passing.
- **R-P2-001 (BLOCKER)** — `pull_request: [main]` added to `ci-core.yml` and `domain-tests.yml` (domain PR trigger keeps quant path filters); push:main retained; promotion PRs from Phase 1 now have real CI behind their merge gate. 2 yaml-parsing trigger-contract tests.
- **Targeted sweep**: 278 passed across all remediation areas. **Canonical full suite after remediation: 0 failed / 2,595 passed / 17 skipped** (459.36s; +11 vs pre-remediation = remediation tests). **GitHub PR CI evidence (R-P2-001)**: PR [#11](https://github.com/aase7en/A-Wiki/pull/11) opened `refactor/awiki-kernel-vnext-clean` → `main`. A live ci-core run could NOT be produced pre-merge, for two observed reasons: (1) a GitHub API incident (repeated 503s — PR creation itself only succeeded via REST, and the close/reopen retrigger was rejected); (2) `ci-core.yml`/`domain-tests.yml` do not yet exist on the default branch, and workflow-dispatch + pull_request pickup both 404/no-op for branch-only workflow files in this state. The PR event will fire the new CI as soon as the workflows reach `main` (i.e., at #11's merge, after reviewer PASS). Local Ubuntu-equivalent risk was closed by R-P2-004 (portable keys verified: 0 backslashes) and every ci-core gate was executed green locally this session.

## Review History

| Phase | Verdict | Date | Notes |
|---|---|---|---|
| 0 | PROVISIONAL PASS WITH NOTES | 2026-08-17 | Report quality looked good, but commits were not yet visible remotely. |
| 0 | CHANGES REQUIRED | 2026-08-17 | Formal GitHub review found branch contamination: 24 unrelated commits / 63-file diff. |
| 0 | **PASS** | 2026-08-17 | Clean branch verified independently: 4 commits ahead, 0 behind, docs-only 3-file diff. Phase 1 authorized. |
| 1 | ⏳ awaiting | 2026-08-17 | P1.1–P1.5 complete, 5 TDD commits; full-suite regression evidence in handoff. |
| 1 | CHANGES REQUIRED | 2026-08-17 | R-P1-001 subagent-eval main mutation · R-P1-002 telegram truncation · R-P1-003 baseline gap · R-P1-004 PR fail-open (`reviews/phase-1-review-0a4ffa0d.md`) |
| 1 | ⏳ awaiting re-review | 2026-08-17 | All 4 findings fixed in order (Remediation Log above); base-vs-head comparison established. |
| 1 | **PASS_WITH_NOTES** | 2026-08-17 | R-P1-001..004 RESOLVED (`reviews/phase-1-rereview-328f9a66.md`); N-P1-001 race-history wording deferred to Phase 8. Phase 2 authorized. |
| 2 | ⏳ awaiting | 2026-08-17 | P2.1–P2.5 complete per mandated order; full-suite regression evidence in Phase 2 Log. |
| 2 | CHANGES REQUIRED | 2026-08-17 | R-P2-001 no PR CI · R-P2-002 256 KiB scan cap · R-P2-003 coarse baseline keys · R-P2-004 OS-dependent identities (`reviews/phase-2-review-dff83ebb.md`) |
| 2 | ⏳ awaiting re-review | 2026-08-17 | All 4 blockers + note fixed in review order (Remediation Log above); PR opened for real GitHub CI evidence. |
| 2 | CHANGES_REQUIRED (verification only) | 2026-08-18 | Code accepted in principle; blocker = PR #11 unmergeable (1-2 bot commits behind). Merge-only remediation ordered (`reviews/phase-2-rereview-1137752.md`). |
| 2 | **FINAL VERIFICATION COMPLETE** | 2026-08-18 | Merge `dc726ed3` (no rebase) → PR #11 mergeable. First real PR CI exposed 3 latent main-side defects (all hidden until now by `[skip ci]` bot commits): quickchart.io support email (whitelisted per deepseek/sov.ai precedent `a4d1d98d`), stale generated context (regen `029e04b9`), model-pool.json hardcoded in a test (P1.3 optional-cache contract `8a2f01d1`) + preflight main-only branch check rejected PR merge refs (accepted `0f4b3baa`). **Core CI: SUCCESS on PR #11** (run 32060806908, head `0f4b3baa`, pull_request event). Domain CI: success. Webhook-drop incidents during the cycle re-fired per review step 9. |

| 2 | **PASS** (merged) | 2026-08-18 | PR #11 merged by human gate; post-merge main `05140b15`; Core+Domain CI green on the PR; local canonical suite 0 failed / 2,599 passed / 17 skipped. |
| 3 | CHANGES_REQUIRED | 2026-08-18 | R-P3-001..007 (PR #13 review): review state machine, validator authority, lost task semantics, vocabulary gaps, handoff looseness, missing intake artifact, ineffective graft test. |
| 3 | ⏳ awaiting re-review | 2026-08-18 | All 7 findings fixed TDD (Phase 3 Remediation Log); canonical suite green; pushed for re-review on exact new HEAD. |
| 3 | CHANGES_REQUIRED (re-review) | 2026-08-18 | R-P3-001/003/005/006/007 VERIFIED; open: R-P3-002 trust not machine-required, R-P3-004 capability bypass via assigned.requires, R-P3-008 PR Core CI red (stale capability-map). |
| 3 | ⏳ awaiting re-review (2) | 2026-08-18 | Trust machine-required (+4 truthful module entries), single $defs.capability for both enum paths, capability-map regen (attributable diff). Canonical 0 failed / 2,659 passed / 17 skipped. |
| 3 | **PASS** (merged) | 2026-08-18 | PR #13 merged; post-merge main `2e84759c`. Kernel Contract closed. |
| 4 | ⏳ awaiting | 2026-08-18 | Project Adapter complete (Phase 4 Log). |
| 4 | CHANGES_REQUIRED | 2026-08-18 | R-P4-001..006 (PR #14 review): containment, attach symlink safety, required policy, safe yaml gen, registry cross-check, attachment surface. |
| 4 | ⏳ awaiting re-review | 2026-08-18 | All 6 fixed TDD (41 adapter tests); canonical 0 failed / 2,700 passed / 17 skipped. |
| 4 | CHANGES_REQUIRED (re-review) | 2026-08-18 | R-P4-007 read-path symlinks · R-P4-008 allowlist eligibility · R-P4-009 decode fail-closed. |
| 4 | ⏳ awaiting re-review (2) | 2026-08-18 | R-P4-007..009 fixed TDD (49 adapter tests); canonical 0 failed / 2,708 passed / 17 skipped. |
| 4 | CHANGES_REQUIRED (re-review 2) | 2026-08-18 | R-P4-007 checks ran after reading; R-P4-008 module+pattern (graft) wrongly ineligible. |
| 4 | ⏳ awaiting re-review (3) | 2026-08-18 | Symlink checks BEFORE any read (lstat-only) in validate+status; eligibility = membership. 55 adapter tests; canonical 0 failed / 2,714 passed / 17 skipped. |
| 5 | ⏳ awaiting | 2026-08-18 | Memory layers complete (Phase 5 Log). Canonical 0 failed / 2,746 passed / 17 skipped. |
| 5 | CHANGES_REQUIRED | 2026-08-18 | R-P5-001..006 (PR #15 review): L2-bound promotion, nested symlink escapes, adapter-authoritative L5, provenance privacy/safe YAML, read-only status, ledger seam. |
| 5 | ⏳ awaiting re-review | 2026-08-18 | All 6 fixed TDD (33 negative tests, 29 red-first); canonical 0 failed / 2,779 passed / 17 skipped. |
| 5 | CHANGES_REQUIRED (re-review) | 2026-08-18 | R-P5-002..005 VERIFIED; open: R-P5-001 content not bound to source entry, R-P5-006 extra seam redaction/collision. |
| 5 | ⏳ awaiting re-review (2) | 2026-08-18 | promote() consumes the stored L2 summary (no free-form text; source identity+digest persisted); extra namespaced + recursively redacted + reserved-key rejection. 10 red-first tests; canonical 0 failed / 2,789 passed / 17 skipped. |
| 5 | **PASS** (merged) | 2026-08-18 | PR #15 independently passed at reviewed head `5def54757ed7189f6408878a911f6bcd785d0adc`; human-gate merge produced main `51258fac665add6e65e6f4a239fda5d597670f0e`. |
| 6 | **CHANGES_REQUIRED** | 2026-08-20 | Independent review of an uncommitted local snapshot based on `fcef705cdf8e0814927d498bdd467c8987fcc59e` found P6-R01..P6-R07. Findings are durable in `reviews/phase-6-review-local-fcef705c.md`; fresh local identity/dirty-state verification remains pending. |

## Phase 3 Remediation Log (2026-08-18)

Review: PR #13 vs `8ae924d7`. Every fix TDD with negative instance tests:

- **R-P3-001** — `awiki-review/v1` now enforces its state machine via `allOf/if-then`: reviewed/approved states require `reviewer`+`verdict`; APPROVED/READY accept only `PASS`/`PASS_WITH_NOTES` and must carry findings+required_tests+next_action; **open blockers make READY/APPROVED invalid** (`not contains {severity:blocker, state:open}`). 5 negative/positive instance tests.
- **R-P3-002** — validator rebuilt as ONE authoritative path: `UniqueKeyLoader` (duplicate YAML mapping keys rejected — `safe_load` silently overwrote them), full JSON-Schema validation (`additionalProperties:false` now structurally rejects unknown/runtime fields), semantic checks (external default-off+lazy, module ⇒ storage+provides, cache commit:false, reject-doesn't-combine, dangling references). `jsonschema>=4` added to requirements.txt (CI authority). Registry truthfulness: `graft-freshness-pattern` `merged→planned` (wiki-health/scan-repo do NOT implement query-path freshness), `implemented_by` removed; world-intel + trello gained the now-required `storage` declarations the stronger validator exposed. 14 validator tests.
- **R-P3-003** — task semantics restored safely: durable = `task_state` + `work_order_contracts` (+ review/handoff state), control_plane holds `task_state` — contract test asserts task is in BOTH boundaries AND the wording never re-triggers the `sk-` scanner.
- **R-P3-004** — one canonical vocabulary: `tester` role added to `assigned`; capability enum += `project-code-context`, `symbol-search`, `call-graph`, `blast-radius`, `memory-read`, `memory-write`; `worktree` (repo-relative only — pattern rejects drive letters/`~`/leading `/`) + `evidence` fields; cross-contract tests prove handoff roles ⊆ kernel roles and registry-advertised context capabilities are task-requestable; KERNEL.md list reconciled.
- **R-P3-005** — handoff now requires `from`, `to_role`, `tests`, `changed_files`, `open_questions`, `known_risks` (6 negative instance tests + complete-positive).
- **R-P3-006** — `docs/protocols/integration-intake.md` created (13-question checklist, classification vocabulary, decision-record requirement, hard intake rules — reconciled with brain-improvement-gate scope split); normative-reference test resolves `awiki.yaml` classification-gate pointer + every registry `reference:`.
- **R-P3-007** — graft classification test rewritten with explicit scalar/list normalization + set comparison; negative cases (`reject`, `["module","reject"]`, `[]`, `None`) prove the check bites.
- Gates: privacy ✓ · scan_repo 49 known/0 new (one self-inflicted literal drive path in a test assembled at runtime instead) ✓ · wiki_health 0 hard/48 baselined with the overhauled integrations check active ✓ · canonical suite green (see Review History).

## Phase 4 Log (2026-08-18)

Thin, portable project adapter — base main `2e84759c`, TDD (18 tests red-first, temp fixture repos only):

- **`schemas/awiki-project/v1.schema.json`** — stable project policy ONLY: id, repository identity, domains, skills/integrations allowlists, memory scopes, privacy/trust, optional code_context policy (G0 vocabulary, `global_memory_promotion: false` const), project-relative resources. `additionalProperties:false` structurally rejects secrets/quota/telemetry-shaped fields.
- **`scripts/project/validate.py`** — deterministic/offline, fail-closed: duplicate-key-safe loader (reused from integrations validator — one loading contract), JSON Schema, semantic checks — absolute/private machine paths rejected (drive-letter regex with lookbehind so `https://` never false-positives), secret-shaped values rejected via the kernel's single security-pattern source, referenced local files must exist, context.md required.
- **`scripts/project/attach.py`** — idempotent + non-destructive: creates `.awiki/{project.yaml,context.md,state/}` only-if-absent (existing policy byte-preserved); AGENTS.md created if missing else ONE marked section appended (marker `awiki-project-adapter`), existing content preserved verbatim, never appended twice. No submodules/symlinks/A-Wiki copies; pathlib-only (cross-platform).
- **`scripts/project/status.py`** — read-only + deterministic; --json reports id, adapter_valid, domains, memory, integrations, privacy/trust, state-dir availability, context.md presence; exit 1 without a valid adapter.
- Gates: privacy ✓ · scan_repo 49 known/0 new ✓ · wiki-health 0 hard/48 baselined ✓ · gen-index fresh (no regen needed). Canonical suite: see Review History row.

## Phase 4 Remediation Log (2026-08-18)

Review: PR #14 vs `4248caa3`. All findings TDD (negative tests first, 21 red before fixes):

- **R-P4-001** — `_contains()` resolved-path containment helper (symlink escapes + nested `..` rejected by resolution, not string checks); path regex extended host-OS-independently (UNC `\server`, extended `\?\` device, `/etc` `/tmp` `/var` `/opt` `/root` `/private`, drive-letter lookbehind keeps `https://` clean). Fixed a real self-bug found by the tests: the joined candidate is always absolute — absoluteness must be checked on the REF.
- **R-P4-002** — attach refuses to run when ANY adapter path is a symlink (checked before any write); tests prove external targets' bytes and directories remain untouched, no partial attach.
- **R-P4-003** — schema structurally requires privacy (project_private), trust (private_context), memory (all four scope decisions); attach template generates the full trust policy; negatives for each omission.
- **R-P4-004** — project.yaml generated from a mapping via `yaml.safe_dump` (punctuation/Unicode domains round-trip verbatim — tested with commas/colons/brackets/Thai/Chinese); id pattern reconciled to min-1 (`_slug` alignment); attach self-validates the RESULT and exits 1 on invalid (tested via a real pre-existing invalid project.yaml that must stay byte-preserved).
- **R-P4-005** — `integrations.allowed` cross-checked offline against the canonical registry (fail-closed if the registry is unreadable); unknown-id negative + known-id positive.
- **R-P4-006** — canonical attachment surface enforced: AGENTS.md with the adapter marker + context.md + state/ all required; negatives for deleted AGENTS.md, markerless AGENTS.md, missing state/.
- Gates: privacy ✓ / scan_repo 49 known 0 new ✓ / wiki-health 0 hard ✓ · canonical **0 failed / 2,700 passed / 17 skipped**.

## Phase 4 Remediation Log 2 (2026-08-18)

Review: PR #14 vs `25f488a1`. TDD (8 negatives red-first):

- **R-P4-007** — the READ path now enforces the same no-symlink invariant as attach: `_check_canonical_surface` rejects any symlinked canonical path (AGENTS.md, .awiki, project.yaml, context.md, state) before metadata is consumed; status reports INVALID instead of reading an external surface. Negatives: symlinked .awiki / AGENTS.md / project.yaml + status-INVALID.
- **R-P4-008** — allowlist eligibility by registry SEMANTICS (`_eligible_integration_ids`: MODULE-classified only); REJECT (deer-flow) and pattern-only (autoresearch) entries are ineligible even though their ids exist; planned/optional MODULE pre-authorization preserved. Negatives + existing module positive.
- **R-P4-009** — decode/read errors converted to deterministic validation errors (fail closed, no silent byte replacement in policy metadata): validate catches OSError + UnicodeDecodeError on project.yaml; status guards both project.yaml and AGENTS.md reads. Negatives: invalid-UTF-8 project.yaml (validate + status).
- Gates: privacy ✓ / scan_repo 49 known 0 new ✓ / wiki-health 0 hard ✓ · canonical **0 failed / 2,708 passed / 17 skipped**.

## Phase 4 Remediation Log 3 (2026-08-18)

Review: PR #14 vs `f5995089`. TDD (4 negatives red-first: secret-canary external targets prove they are never read):

- **R-P4-007 (final)** — canonical-surface symlink checks now run BEFORE any `is_file`/`read_bytes`/YAML parse/AGENTS read (`is_symlink()` = lstat, never follows the link); on unsafe surface validate returns immediately with ONLY the symlink violation. `status()` performs the same safe-surface check first and never parses/reports fields (e.g. attacker-controlled `id`) from an unsafe surface. Canary tests: external project.yaml/.awiki/AGENTS.md targets containing a secret-shaped token yield symlink errors ONLY — no secret error proves the bytes were never consumed.
- **R-P4-008 (final)** — eligibility is membership-based (`"module" in classes and "reject" not in classes`): graft `[module, pattern]` eligible, gitnexus pure-module eligible; `autoresearch` (pattern-only) and `deer-flow` (reject) stay ineligible. Contract-only — no Graft runtime installed/enabled.
- Gates: privacy ✓ / scan_repo 49 known 0 new ✓ / wiki-health 0 hard ✓ · canonical **0 failed / 2,714 passed / 17 skipped**.

## Phase 5 Log (2026-08-18)

Memory plane per `docs/migration/phase-5-memory-layers-work-order.md` — base main `10507cee`, branch `refactor/awiki-memory-layers`, TDD (32 tests, work-order invariants 1–25), temp fixture repos/storage only:

- **`scripts/lib/memory_layers.py`** — normative L0–L5 policy (`LAYER_POLICY`: durability runtime/durable, `global_knowledge`, `auto_promote` all False, `writable_via_memory_api` L3/L4=False) + `transition_allowed()`: the ONLY legal transition is L2→L3 via "promotion"; everything else raises `LayerViolation`. Mirrored in **`config/memory-layers.yaml`** (`awiki-memory-layers/v1`); a lockstep consistency test keeps the two from drifting.
- **`scripts/lib/project_memory.py`** — `ProjectMemoryStore` on Phase-4 authority: adapter validated via `scripts/project/validate.py` (invalid → fail closed `AdapterInvalid`); `scopes.project` required for L2 ops (`ScopeDenied`); `scopes.global is not True` blocks promotion; storage `projects/<id>/memory/` under `AWIKI_DATA_DIR` → drive-root resolution (absolute REQUIRED; relative/traversal/symlink data roots rejected); per-entry project tag + isolation guard (Project A never sees B's entries); `write_layer` refuses L3/L4.
- **`scripts/lib/experiment_memory.py`** — `ExperimentStore`: `baseline.json` immutable after init (`BaselineImmutable`), `iterations.jsonl` append-only (`AppendOnly` always raised on overwrite), `winner.json` must reference a recorded iteration (`WinnerValidationError`), strict experiment-id regex (`MalformedRecord`), per-experiment `.project` marker (cross-project access → `ProjectIsolationError`).
- **`scripts/lib/promotion.py`** — five-gate pipeline in one place: distill (non-empty, ≤2000 chars) → privacy (reuses `_scan_staged_diff` PATTERNS/PLACEHOLDERS + adapter `ABSOLUTE_PATH_RE` — no new scanner) → generalize (project-specific detail detector) → provenance-evidence (whitelisted types: commit_sha/tests_passed/experiment_id/adr_path/wiki_ref/review_finding/task_ref/handoff_ref; SHA-validated; path-free values) → write. Dry-run default; `--apply` writes exactly ONE candidate file to `wiki/promotion-candidates/`; no Git machinery anywhere. `ScopeDenied` imported from `project_memory` (single contract — the duplicate-class bug was caught and removed).
- **`scripts/memory/status.py` + `scripts/memory/promote.py`** — thin CLIs: read-only `status --json` (exit 1 invalid adapter); `promote --text --evidence type=value [--apply] [--json]` dry-run-first.
- Existing substrates reused, not duplicated: MemoryLedger stays L1 (`memory_remember`/`memory_recall` caller contracts green), wiki/ stays L3, raw/ stays L4, `.tmp` stays L0. No hook-engine changes, no Graft, no search rearchitecture, no auto-promotion, no background jobs.
- Gates: privacy ✓ / scan_repo 49 known 0 new ✓ / wiki-health 0 hard / 48 baselined ✓ / canonical **0 failed / 2,746 passed / 17 skipped** (521.87s).

## Phase 5 Remediation Log (2026-08-18)

Review: PR #15 vs `715cc19e`. All 6 findings fixed TDD — 33 negative tests written FIRST (29 red), then implementation. Focused: 65/65 memory + 291 compat; canonical **0 failed / 2,779 passed / 17 skipped**.

- **R-P5-001 (L2-bound promotion)** — `promote()` gained gate 0 `l2-source`: mechanically verifies a `source_entry_ts` exists in THIS project's L2 store (`ProjectMemoryStore.get_entry`, foreign-project entries return None) and consults `transition_allowed(source_layer, "L3", via="promotion")` on the execution path. L0/L1/L4 sources or a missing/foreign ts can never reach candidate write (proven with `dry_run=False` + empty candidates dir). CLI requires `--source-ts`.
- **R-P5-002 (nested symlink escapes)** — new `safe_join_under_root()`: component-wise symlink + Windows reparse-point rejection (lstat-only, `drive_path.is_reparse_point`) AND resolved-realpath containment within the canonical data root, before ANY read/write, for every L2/L5 path (projects/, project-id/, memory/, experiments/, exp-id/, leaf files) — re-verified after mkdir. Tests: symlinked `projects/`, leaf `entries.jsonl` (victim byte-identical after), symlinked experiment dir + baseline leaf.
- **R-P5-003 (adapter-authoritative L5)** — `ExperimentStore(project_root, data_root)` now derives identity from the validated Phase-4 adapter; a caller-supplied `project_id` may only re-state the adapter's own id and any mismatch raises `ProjectIsolationError` BEFORE storage is touched; requires `scopes.project`. Beta-supplying-alpha fails with alpha's tree unwritten.
- **R-P5-004 (provenance privacy + safe YAML)** — every persisted provenance value now clears the SAME privacy scanner as the distilled text (secret patterns + absolute-path detector), plus strict per-type value shapes for all 8 evidence types and a newline/control-char rejection. Candidate front matter is produced by `yaml.safe_dump` — no string interpolation; injection/key-addition tests prove it parses back to exactly the intended mapping.
- **R-P5-005 (read-only status)** — `resolve_data_root_readonly()` mirrors `get_drive_root()`'s chain but raises `DataRootUnavailable` instead of creating `~/.a-wiki-data`; status constructs the store `read_only=True`, emits NO absolute/private paths (identity = adapter id), and converts adapter/storage/symlink failures into deterministic JSON (`storage_ok`/`storage_error`) with stable exit behavior. Snapshot tests prove the filesystem is byte-identical before/after.
- **R-P5-006 (ledger seam)** — L2 storage routes through `MemoryLedger` via a narrowly-justified extension (`extra` kwarg merges caller fields AFTER redaction; vanilla entry shape unchanged — pinned by test). `append_entry` returns the ledger ts; appends inherit secret redaction + `atomic_json` lock-protected writes; `read_entries` = ledger.search + project filter (foreign lines skipped). Concurrency test: 2 threads × 5 appends → 11 valid JSONL lines.

## Phase 5 Remediation Log 2 (2026-08-18)

Re-review vs `30538744` (Core CI run #20 SUCCESS at that HEAD): R-P5-002/003/004/005 VERIFIED. Remaining two fixed TDD (10 negative tests red-first):

- **R-P5-001 (final) — content bound to the verified L2 entry.** `promote()` no longer accepts a free-form `distilled` argument (TypeError by construction — pinned by test). The promoted candidate IS the verified L2 entry's STORED summary, fetched by `get_entry(source_entry_ts)` inside gate 0; the distill/privacy/generalize gates evaluate that stored text, so a valid L2 ts can never authorize unrelated text, and the redaction that happened at append time is the redaction the candidate carries (secret-in-source test: token absent from the written candidate). Front matter persists the source identity — `source: {layer: L2, entry_ts, summary_digest: sha256[:16]}` — verifiable offline. Negative test: valid ts for benign A + apply writes exactly A; a second ts whose stored text is unpromotable ("At project … prod-db-01") writes nothing. CLI dropped `--text` (candidate comes from `--source-ts`).
- **R-P5-006 (final) — collision-safe, recursively-redacted extra.** `extra` is now stored under ONE reserved namespaced key `entry["extra"]` — canonical fields (`ts/session_id/type/summary/files/tags/parent_ts/extra`) cannot be overwritten by construction AND are rejected inside `extra` with ValueError before any write (nothing persisted). New `_redact_deep()` recursively redacts every string in nested dict/list metadata with the same secret patterns (top-level + nested-list + deep-dict tokens all proven absent; non-secrets intact). ProjectMemoryStore reads the namespaced tag (`entry["extra"]["project"]`) for isolation/get_entry; vanilla `append()` entry shape pinned unchanged.
- Gates: privacy ✓ / scan_repo 49 known 0 new ✓ / wiki-health 0 hard / 48 baselined ✓ / canonical **0 failed / 2,789 passed / 17 skipped**. Focused: 75/75 across the three Phase-5 files; compat sweep 301 passed.

## Historical Phase 1 Entry Order (closed)

The former Phase 1 execution instruction is retained by the Phase 1 logs and review history above. It is **not current work** and must not be executed. Phases 1–5 are closed; Phase 6 is the only authorized implementation phase.

## Current Continuity Checkpoint (2026-08-20)

### Project / objective / task

- **Project:** A-Wiki vNext migration
- **Current objective:** remediate the independent Phase 6 review findings without expanding scope
- **Current phase:** Phase 6 — Hook Engine Consolidation
- **Task ID:** `P6-REMEDIATE-REVIEW-001`
- **Status:** **CHANGES_REQUIRED**
- **Local classification:** **PARTIAL** — implementation exists locally but has material review defects and is not committed
- **LOCAL_WORKTREE_VERIFICATION:** **COMPLETE** through GPT Work shell on 2026-08-20
- **LOCAL_SERENA_VERIFICATION:** **NOT_REQUIRED** by explicit user direction

### Completed and evidence

- Phase 5 passed at `5def54757ed7189f6408878a911f6bcd785d0adc` and merged through PR #15 as `51258fac665add6e65e6f4a239fda5d597670f0e`.
- GitHub branch `refactor/awiki-hook-engine` points to `fcef705cdf8e0814927d498bdd467c8987fcc59e`, directly ahead of Phase 5 main by the authoritative Phase 6 work order only.
- An independent read-only review examined the uncommitted Phase 6 semantic delta and returned **CHANGES_REQUIRED**. See `docs/migration/reviews/phase-6-review-local-fcef705c.md`.
- No Phase 7 or Phase 12–16 implementation is authorized or mechanically present in the reviewed delta.
- GitHub showed no open Phase 6 implementation PR. Draft docs-only continuity PR #16 now preserves this checkpoint against the Phase 6 branch.

### Repository / worktree state

- **GitHub main:** `51258fac665add6e65e6f4a239fda5d597670f0e`
- **GitHub Phase 6 branch:** `refactor/awiki-hook-engine`
- **GitHub Phase 6 HEAD:** `fcef705cdf8e0814927d498bdd467c8987fcc59e`
- **Recovery documentation branch / HEAD:** `docs/awiki-continuity-recovery-20260820` / `3944efadf4ec1bdc2721c78a1ce44707f252c2b1` at draft PR #16 (docs only; targets the Phase 6 branch)
- **Verified local project/worktree:** `A-Wiki-vnext-clean`; repository identity matches `aase7en/A-Wiki`
- **Verified branch / HEAD / upstream:** `refactor/awiki-hook-engine` / `fcef705cdf8e0814927d498bdd467c8987fcc59e` / `origin/refactor/awiki-hook-engine` at the same SHA
- **Verified merge-base / distance from origin/main:** `51258fac665add6e65e6f4a239fda5d597670f0e`; 0 behind / 1 ahead
- **Verified dirty state:** 14 semantic Phase 6 files, 16 tracked diff-empty Windows stat/EOL entries, and pre-existing untracked `.serena/` tooling state
- **Claims:** no live claim in any discovered worktree claim store
- **Other worktrees:** the separate local `main` worktree is 24 commits ahead and 104 behind `origin/main` with unrelated dirty work; historical tool worktrees also contain type-change noise. None owns Phase 6. Do not normalize or modify them.

### Files changed in the reviewed local snapshot

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

The recovery branch changes only this tracking plan, the review-bus plan, the project-context architecture deltas, a corrected durable Phase 6 execution handoff, and the new Phase 6 review record.

### Decisions made

- `D-P6-001` — **FAIL overall**: the core malformed sentinel works, but supported adapter paths still collapse or bypass it.
- `D-P6-002` — **PASS**: duplicate IDs are checked before lookup-map collapse.
- `D-P6-003` — **FAIL**: deployed provider paths can bypass canonical event selection/order.
- `D-P6-004` — **FAIL end-to-end**: startup/sanitizer failure paths can leak raw diagnostics and violate the 0/2 exit contract.
- `D-P6-005` — **PASS narrowly** for present tracked hard gates; generated/tracked config parity still fails.
- `D-P6-006` — **FAIL overall**: named runner compatibility passes in isolation, but active bare-invocation provider paths regress.
- A-Wiki, Conductor, and Serena remain separate surfaces; see `awiki-project-context-architecture-deltas.md#d-ctx-013--separate-brain-orchestration-and-local-execution-surfaces`.

### DECISION_REQUIRED

No new architecture decision is required. The docs-only recovery branch must be reconciled into the Phase 6 branch without overwriting local WIP; this is an execution step, not an architecture choice.

### Known problems / warnings

- Serena returned repeated gateway timeouts, but GPT Work shell access completed the same mechanical local identity/ownership audit; no local evidence remains pending.
- Phase 6 focused evidence recorded 123 passed / 1 skipped / 3 warnings / 0 failures, but several focused tests touch live repository state and therefore were not rerun during the read-only review.
- The historical full suite recorded 2,827 passed / 41 failed / 17 skipped / 8 warnings. Most failures were plausibly platform-related, but no final full-suite run exists at a committed Phase 6 SHA.
- Passing privacy/security/diff gates did not detect all reviewed diagnostic/path leaks and therefore is not approval evidence by itself.
- The long local untracked handoff still says `REVIEW_REQUESTED`, marks all locked decisions green, and contains machine-specific paths. The corrected durable handoff on the recovery branch supersedes that draft; do not commit the stale local version blindly.
- The unrelated dirty/diverged local `main` worktree is protected external WIP for this task.

### Do not do

- Do not reset, clean, stash, rebase, delete, or overwrite the uncommitted Phase 6 work.
- Do not edit `main` directly.
- Do not begin Phase 7 or Phases 12–16.
- Do not regenerate configuration during continuity recovery.
- Do not treat the local-snapshot review as approval of a future commit.

### Ordered TODO

1. Reconcile the draft continuity PR #16 into the Phase 6 branch without overwriting the 14-file local WIP or the protected other worktrees.
2. Replace the stale local handoff with the corrected durable handoff during that reconciliation.
3. Remediate P6-R01 first, test-first, then P6-R02..P6-R07 in severity order within the Phase 6 work order only.
4. Run isolated focused tests, registry counts, privacy/security/CI-secret smoke, generated-config parity, `git diff --check`, and the appropriate full regression suite.
5. Commit and push an attributable Phase 6 implementation SHA.
6. Request a fresh independent review of that exact SHA; only PASS plus CI may advance the phase.

### Single next safe action

Reconcile the draft continuity PR #16 into the verified Phase 6 branch without overwriting the 14-file local WIP; then begin the P6-R01 test-first remediation slice.

### Resume checks

At the start of the next session, repeat these read-only checks through any available local shell/tool surface before mutation:

```text
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git status --short
git remote get-url origin
git rev-parse origin/main
git rev-parse origin/refactor/awiki-hook-engine
git merge-base HEAD origin/main
git worktree list --porcelain
git diff --name-only
git diff --check
```

Also inspect every local claim store and all open A-Wiki pull requests through GitHub. At this checkpoint there were zero live claims; the only expected open PR is draft continuity PR #16.

<!-- final-verification: continuity recovery 2026-08-20; LOCAL_WORKTREE_VERIFICATION: COMPLETE -->
