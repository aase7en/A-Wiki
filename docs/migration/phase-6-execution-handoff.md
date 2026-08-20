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

The exact Phase 6 remediation commit `9962b34bfc2604217359b4b56b54d9f902e7f1c3` was independently re-reviewed by GPT Work on 2026-08-20 and received **CHANGES_REQUIRED** with findings `P6-RR01` through `P6-RR09`.

The current task is to remediate those nine findings in severity order using test-first micro-steps, create a new attributable commit, push that exact SHA, and request another independent re-review. Phase 6 is not approved or merged. Phase 7 remains unauthorized.

## Verified repository/worktree state

- repository: `aase7en/A-Wiki`
- local project/worktree identity: `A-Wiki-vnext-clean`
- branch: `refactor/awiki-hook-engine`
- committed HEAD: `9962b34bfc2604217359b4b56b54d9f902e7f1c3`
- upstream: `origin/refactor/awiki-hook-engine` at the same SHA
- reviewed base commit: `fcef705cdf8e0814927d498bdd467c8987fcc59e`
- reviewed remediation commit: `9962b34bfc2604217359b4b56b54d9f902e7f1c3`
- latest independent re-review verdict: **CHANGES_REQUIRED**
- remote implementation state: Phase 6 remediation commit exists at the reviewed SHA
- local implementation state: **REMEDIATION_REQUIRED**, beginning `P6-RR01` test-first from the reviewed SHA
- live claims: zero across all discovered worktree claim stores
- open Phase 6 implementation PR at audit time: none
- docs-only continuity branch: `docs/awiki-continuity-recovery-20260820`
- durable checkpoint transport: draft PR #16 targeting the Phase 6 branch; the PR's current head is the immutable documentation target

The separate local `main` worktree is 24 commits ahead and 104 behind `origin/main` with unrelated dirty work. Historical tool worktrees also contain type-change noise. They are protected other work for this task: do not reset, clean, merge, rebase, switch, or otherwise normalize them.

## Dirty-state classification

At the start of the `P6-RR01..RR09` remediation pass, `git diff --name-only` was empty on the reviewed commit. `git status --short` still showed known semantic-empty generated wiki/graph stat/EOL noise plus untracked `.serena/` tooling state. These are not part of the remediation and must not be staged or normalized.

The reviewed Phase 6 commit contains exactly these 21 project files:

```text
.claude/settings.json
.codex/hooks.json
.gemini/settings.json
docs/migration/phase-6-execution-handoff.md
scripts/cline-hooks/adapter.sh
scripts/hooks/check_bash_destructive_git.py
scripts/hooks/memory_capture.py
scripts/hooks/providers.py
scripts/hooks/registry.py
scripts/hooks/self_audit.py
scripts/hooks_runner.py
scripts/lib/a_flow_state.py
scripts/live-dashboard/event_logger.py
scripts/setup-codex-config.py
tests/test_a_focus_hook.py
tests/test_a_route_hook.py
tests/test_compaction_suggest.py
tests/test_hook_engine.py
tests/test_hook_stdout_encoding.py
tests/test_hooks.py
tests/test_self_audit_visibility.py
```

Future remediation may expand this manifest only when a `P6-RRxx` finding explicitly requires another file. `.serena/` and semantic-empty generated wiki/graph noise remain excluded.

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

## Open findings — independent re-review of `9962b34bfc2604217359b4b56b54d9f902e7f1c3`

- **P6-RR01 CRITICAL — `providers.py`, `check_raw_immutable.py`:** Gemini/Cline native tool names can bypass hard gates. Normalize provider action/arguments into canonical tool schema before policy dispatch.
- **P6-RR02 CRITICAL — `hooks_runner.py`, `README.md`:** runner uses annotations incompatible with supported Python 3.8/3.9. Restore supported-version compatibility and verify against the documented support contract.
- **P6-RR03 HIGH — `providers.py`, `hooks_runner.py`, `memory_ledger.py`:** exceptions can still produce exit 1/traceback and redaction is incomplete. Add a safe outer boundary and unified sanitizer.
- **P6-RR04 HIGH — `scripts/cline-hooks/adapter.sh`, `.gemini/settings.json`, `hooks_runner.py`:** missing interpreter/log/timeout paths can fail open. Hard lifecycle failures must fail closed and total timeout must be bounded.
- **P6-RR05 HIGH — `registry.py`, `.codex/hooks.json`, `log_subagent_result.py`:** registry does not own matcher applicability, allowing over/under-dispatch. Add matcher policy/schema validation.
- **P6-RR06 HIGH — `agent-preflight.py`, `verify-awiki-ready.py`, compatibility tests/docs:** stale named-hook verification remains. Convert verification to event-sweep + registry authority.
- **P6-RR07 HIGH — `setup-codex-config.py`, `setup-codex-hooks.sh`, CI workflows:** fallback/CI rewrite paths can make parity false-green. Converge on one source of truth and check before write.
- **P6-RR08 MEDIUM — `tests/test_hook_engine.py`, `agent_claims.py`, `check_cost_tier.py`:** focused tests can still write live claims/cost state under some conditions. Redirect every mutable state seam.
- **P6-RR09 MEDIUM — `phase-6-execution-handoff.md`:** handoff was public-safe but stale on SHA/state/manifest/next steps. This checkpoint begins the reconciliation; final closure requires another truthfulness/privacy scan before review request.

### Remediation progress — 2026-08-20

The evidence below documents the prior `P6-R01..P6-R07` remediation that produced reviewed SHA `9962b34b...`. It is retained as history, but the latest independent re-review supersedes any earlier green interpretation.

### Re-review remediation progress

- **P6-RR01 provider-native canonicalization — FOCUSED GREEN:** TEST-FIRST reproduced `4 failed` for Gemini `write_file`, Cline `write_to_file`/`replace_in_file`, and native raw-write bypass. `providers.py` now centralizes native action mapping (`write_file/write_to_file → Write`, `replace/replace_in_file → Edit`, `run_shell_command/execute_command → Bash`) and Cline `path → file_path`. Provider normalization suite: `16 passed`. Actual Gemini/Cline native E2E: `2 passed`, including malformed handling, hard secret block, missing-hard behavior, and soft Cline behavior. Independent re-review is still required after all RR findings are remediated.
- **P6-RR02 Python 3.8+ compatibility — LOCAL GREEN / CI EVIDENCE PENDING RR07:** README still declares Python 3.8+. TEST-FIRST found three runtime-evaluated `str | None` annotations in `hooks_runner.py`; they were replaced with `typing.Optional[str]`. Python-3.8 grammar/annotation guard now passes and current-runtime import smoke passes. No 3.8/3.9 interpreter is installed locally; dedicated real-runtime CI smoke is deferred to `P6-RR07` when CI workflows are already in scope.
- **P6-RR03 safe outer boundary + unified redaction — FOCUSED GREEN:** TEST-FIRST reproduced three failures: unexpected provider exception escape, dispatch exception escape, and incomplete generic credential redaction. `hooks_runner.main()` is now a safe wrapper around `_main_impl()` that normalizes unexpected exceptions to generic exit 2 without exception detail. `memory_ledger._redact()` now redacts credential assignments regardless of value length/punctuation and suppresses all original text if redaction itself fails. Focused tests: `3 passed`; runner/synthetic/memory-ledger compatibility: `56 passed`.
- **P6-RR04 hard lifecycle infrastructure failure + total timeout — FOCUSED GREEN (2026-08-20):** TEST-FIRST reproduced `4 failed`: Cline missing interpreter incorrectly returned `cancel:false`; unusable Cline log path exited 1 before policy; Gemini missing `python3` exited 127 instead of canonical block; event sweep had no bounded total lifecycle timeout. All four contracts now GREEN: `scripts/cline-hooks/adapter.sh` fails closed (`cancel:true`, generic reason, no interpreter-path leak) on any non-{0,2} runner outcome and makes logging non-fatal (`_log`/`_prepare_log` guards); `.gemini/settings.json` BeforeTool command is a fail-closed bash wrapper (only rc=0 passes; missing interpreter → exit 2, no traceback); `hooks_runner.py` bounds the event sweep by `HOOK_TOTAL_TIMEOUT` with hard-remaining→block on exhaustion. RR04 + full engine suite: `118 passed / 0 failed` (2026-08-20, includes RR05/RR06 below).
- **P6-RR05 registry owns matcher applicability — FOCUSED GREEN (2026-08-20):** every registry entry now declares `matchers` (tool applicability: `"Edit|Write|MultiEdit"`, `"Bash"`, `"Agent"`, `"*"`); `validate_registry` enforces non-empty matchers; `hooks_for_event(event, tool_name=...)` filters dispatch (Bash payloads can no longer run Edit-only gates and vice versa); the runner event sweep passes the payload's `tool_name`; a Codex-config consistency test proves every runner-invoking block is an event sweep and each non-wildcard PreToolUse matcher tool still dispatches a non-empty set. 7/7 focused tests. Note: legacy structural contract preserved — registry validation stays STRUCTURAL (executable availability remains a runtime concern per approved P6-R03).
- **P6-RR06 preflight/readiness registry authority — FOCUSED GREEN (2026-08-20):** `scripts/agent-preflight.py` stale `REQUIRED_HOOKS`/`REQUIRED_GUARDRAIL_NAMES` lists deleted. `check_hooks(hooks_dir=None)` validates via the registry authority and checks registered-executable presence itself (fails on empty hooks dir — proven by test); `check_guardrail_coverage()` derives coverage from the registry's hard PreToolUse gates (named invocation OR structural event-sweep both satisfy; catches gates the stale list missed: agent_claim/machine_path/apikey/delegation_gate). 3/3 focused tests; consolidated engine suite `118 passed / 0 failed`.
- **P6-RR07 one Codex source of truth + truthful CI parity — FOCUSED GREEN (2026-08-20):** `scripts/setup-codex-hooks.sh` embedded fallback `hooks.json` heredoc DELETED (it predated parity/sweep and could regenerate a stale false-green config); with the generator missing the wrapper now FAILS LOUDLY (exit 1, writes nothing — proven by sandbox test). `ci-core.yml` gained `python scripts/setup-codex-config.py --check` (check-before-write parity truth against the tracked `.codex/hooks.json`) and a REAL Python 3.8 runtime smoke (setup-python 3.8 → import hooks_runner/registry/providers + `registry.py --check` + benign `--event PostCompact` sweep) — the RR02-deferred evidence. Local equivalents verified on current runtime: registry check `29 hooks (17 hard, 12 soft)`, sweep exit 0. 5/5 focused tests.
- **P6-RR08 mutable-state isolation for every focused test seam — FOCUSED GREEN (2026-08-20):** `run_runner(..., isolate=<dir>)` now redirects ALL mutable seams (AWIKI_MEMORY_LEDGER_PATH / AWIKI_COST_GATE_TMP_DIR / CLINE_HOOK_LOG_FILE / AWIKI_LIVE_LOG_PATH) before caller overrides; hash-snapshot tests prove the LIVE `memory-ledger.jsonl` is byte-identical after memory_capture runs and after a full PostToolUse sweep, with the capture landing in the isolated ledger; the PreToolUse sweep outcome is proven to depend only on the isolated cost declaration. All mutating call sites (`memory_capture` non-blocking, git-refs sweep, matcher sweeps, `test_hooks.py` event sweep) now isolate. 3/3 new tests; combined engine+hooks suites `173 passed / 1 skipped`.
- **P6-RR09 handoff truthfulness closure + acceptance gates (2026-08-20):** All nine RR findings now FOCUSED GREEN. Acceptance evidence at the remediation tree: registry `29 hooks (17 hard, 12 soft)` ✓ · `setup-codex-config.py --check` exact structured parity ✓ · privacy ✓ · security `6180 tracked / 49 baseline / 0 new` ✓ · wiki-health `0 hard / 48 baselined / 355 advisory` (semantic diff unchanged) ✓ · agent-preflight converted checks `core hooks OK via registry authority` + `17 hard PreToolUse gate(s) wired` (its two remaining FAILs are pre-existing ENVIRONMENTAL checks — non-main branch by design, Drive not mounted on this workstation — not Phase 6 scope) ✓ · engine+hooks suites `173 passed / 1 skipped` ✓. Historical full-suite platform failures (cp874 parent-reader family + MSYS symlink-copy) remain classified outside Phase 6 scope from the prior pass — not repaired here, not hidden. This handoff records the exact remediation commit/push SHA below after commit.
- **Status: REMEDIATION COMPLETE — awaiting independent adversarial re-review of the pushed SHA. Merge NOT authorized. Phase 7 NOT started.**

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
- **Current implementation boundary:** `P6-RR04` only. RR01–RR03 are focused GREEN as recorded above. RR04 is partially edited but not yet verified end-to-end; do not reset its WIP and do not start RR05 until the original four RR04 contracts are GREEN plus focused compatibility review passes.

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

1. `P6-RR01` — **FOCUSED GREEN** — provider-native tool/action + argument normalization and hard-gate parity proved.
2. `P6-RR02` — **LOCAL GREEN / CI EVIDENCE PENDING RR07** — Python 3.8+ source/runtime-annotation compatibility restored; real 3.8/3.9 CI smoke remains to be added in RR07.
3. `P6-RR03` — **FOCUSED GREEN** — safe outer exception boundary + unified redaction implemented and compatibility-tested.
4. `P6-RR04` — **IN_PROGRESS / PARTIAL UNVERIFIED** — total lifecycle timeout contract is GREEN; Cline/Gemini infrastructure fail-closed edits exist but original 4-test RR04 set still needs rerun and minimal completion.
5. `P6-RR05` — move matcher applicability into registry authority and validate matcher schema/dispatch.
6. `P6-RR06` — convert preflight/readiness compatibility checks from stale named-hook expectations to event-sweep + registry authority.
7. `P6-RR07` — converge Codex setup/fallback/CI paths on one structured source of truth with check-before-write semantics.
8. `P6-RR08` — isolate remaining claims/cost mutable state seams and prove focused tests do not touch live state.
9. `P6-RR09` — finalize handoff SHA/state/manifest/next-step truthfulness and privacy after remediation.
10. Run bounded focused regressions, acceptance gates, and platform classifications.
11. Create and push a new attributable remediation SHA.
12. Request independent re-review of that exact SHA.
13. Advance only after APPROVED plus CI and explicit human merge authorization.

## Single next safe action

Continue `P6-RR04` only from the current WIP: first inspect the semantic diff in `hooks_runner.py`, `.gemini/settings.json`, and `scripts/cline-hooks/adapter.sh`; then rerun the original four RR04 contracts (missing Cline interpreter, unusable Cline log path, missing Gemini `python3`, bounded total event timeout). Treat any remaining RED as the next minimal fix. Do not reset existing WIP, do not start RR05, and checkpoint the handoff immediately after RR04 focused GREEN or any interruption.

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
