# Phase 6 Independent Review — Local Snapshot Based on fcef705c

> **Status:** CHANGES_REQUIRED
> **Task ID:** `P6-REMEDIATE-REVIEW-001`
> **Authoritative work order:** `docs/migration/phase-6-hook-engine-work-order.md`
> **Review target:** uncommitted local semantic delta based on `fcef705cdf8e0814927d498bdd467c8987fcc59e`
> **Approval scope:** none — an uncommitted snapshot is not an immutable PASS target
> **LOCAL_WORKTREE_VERIFICATION:** COMPLETE through GPT Work shell on 2026-08-20
> **LOCAL_SERENA_VERIFICATION:** NOT_REQUIRED by explicit user direction

## Identity and state evidence

GitHub was verified during continuity recovery:

- repository: `aase7en/A-Wiki`
- `main`: `51258fac665add6e65e6f4a239fda5d597670f0e`
- Phase 6 branch: `refactor/awiki-hook-engine`
- remote Phase 6 HEAD: `fcef705cdf8e0814927d498bdd467c8987fcc59e`
- merge-base with main: `51258fac665add6e65e6f4a239fda5d597670f0e`
- remote delta: one Phase 6 work-order commit; no implementation commit
- open Phase 6 PR at audit time: none

GPT Work shell access mechanically verified the local state after Serena became unavailable:

- project/worktree: `A-Wiki-vnext-clean`
- repository identity: `aase7en/A-Wiki`
- branch: `refactor/awiki-hook-engine`
- HEAD and upstream: both `fcef705cdf8e0814927d498bdd467c8987fcc59e`
- `origin/main` and merge-base: `51258fac665add6e65e6f4a239fda5d597670f0e`
- distance from `origin/main`: 0 behind / 1 ahead
- dirty state: 14 semantic Phase 6 files, 16 tracked diff-empty Windows stat/EOL entries, and pre-existing untracked `.serena/` tooling state
- live claims: zero across every discovered worktree claim store
- other worktrees: the separate local `main` worktree is 24 commits ahead and 104 behind `origin/main` with unrelated dirty work; historical tool worktrees contain type-change noise. None owns Phase 6 and none may be normalized during this task.

Classification:

- GitHub implementation state: **NOT_STARTED** (work order only)
- last reviewed local implementation state: **PARTIAL**
- review state: **CHANGES_REQUIRED**
- current live local state: **PARTIAL**, mechanically verified; implementation exists but is uncommitted and not review-ready

## Scope reviewed

The semantic delta covered:

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

Status-only Windows EOL/stat noise was not treated as semantic change. No file was modified during the independent review.

## Locked-decision verdicts

| Decision | Verdict | Summary |
|---|---|---|
| D-P6-001 malformed payload | **FAIL overall** | Core runner preserves a malformed sentinel, but supported adapter paths still bypass or collapse the distinction. |
| D-P6-002 duplicate hook IDs | **PASS** | Ordered specs are validated for duplicates before lookup-map construction. |
| D-P6-003 canonical provider wiring | **FAIL** | Deployed paths can bypass registry-owned event membership/order; provider normalization is not authoritative. |
| D-P6-004 diagnostic sanitizer failure | **FAIL** | Startup and sanitizer-adjacent errors can emit raw paths/tracebacks and violate the required 0/2 exit surface. |
| D-P6-005 Codex generated hard-gate surface | **PASS narrowly** | Required tracked hard gates are present, but generated/tracked parity and the checker contract fail. |
| D-P6-006 named/legacy compatibility | **FAIL overall** | Named invocation works in isolation, while active bare-invocation Gemini/Cline compatibility regresses. |

## Findings

### P6-R01 — Supported Gemini and Cline hook paths are broken

- **Severity:** CRITICAL
- **Files:** `.gemini/settings.json`, `scripts/cline-hooks/adapter.sh`, `scripts/hooks_runner.py`
- **Requirement violated:** D-P6-001, D-P6-006, provider parity, malformed payload distinction, hard-hook fail-closed behavior without breaking supported runtimes
- **Evidence:** `.gemini/settings.json:42` and `scripts/cline-hooks/adapter.sh:102` invoke the runner without a hook ID or event. The reviewed runner rejects bare invocation with exit 2. Read-only reproduction `echo {} | python -B scripts/hooks_runner.py` returned 2. The Cline adapter also maps jq/malformed failures to `{}` around lines 62–91, erasing malformed-vs-empty semantics; it converts runner exit 2 into cancellation.
- **Why it matters:** supported Gemini and Cline tool hooks can block/cancel normal work, while malformed data takes a different policy path from the contract.
- **Minimum remediation:** map Gemini and Cline lifecycle events and payloads into the canonical runner, preserve an explicit malformed sentinel, and define the compatibility surface without reintroducing run-all ambiguity.
- **Required verification:** provider-path end-to-end tests for valid, empty, malformed, hard-failure, and soft-failure cases on Gemini and Cline.

### P6-R02 — Registry selection and ordering are not authoritative on deployed Claude/Codex paths

- **Severity:** HIGH
- **Files:** `.claude/settings.json`, `.codex/hooks.json`, `scripts/hooks_runner.py`, `scripts/hooks/providers.py`, `tests/test_hook_engine.py`
- **Requirement violated:** D-P6-003; canonical dispatch, no registered-provider bypass, deterministic ordering
- **Evidence:** reviewed config entries invoke one named hook without `--event` at Claude lines 137/156/332 and Codex lines 9/218. Runner event validation occurs only when an event is supplied and then delegates named execution. Thus config membership/order can bypass registry event selection. The provider normalization seam is unused. The parity test loops over a provider label but executes the same runner command for both iterations.
- **Why it matters:** a registered hook may be omitted, reordered, or attached to the wrong event without the canonical registry detecting the bypass.
- **Minimum remediation:** make every registered provider event enter one canonical normalize → registry select/order → classify → execute path; direct named compatibility must still validate registry membership and event semantics.
- **Required verification:** distinct Claude and Codex provider-path tests that prove registry-owned membership, exact order, hard/soft classification, output behavior, and rejection of wrong-event wiring.

### P6-R03 — A missing soft executable globally blocks the runner

- **Severity:** HIGH
- **Files:** `scripts/hooks/registry.py`, `scripts/hooks_runner.py`, `tests/test_hook_engine.py`
- **Requirement violated:** soft hooks cannot block; stable missing-executable semantics
- **Evidence:** registry validation records every missing executable as a global registry error; runner exits 2 before classification. The intended soft-missing nonblocking branch is therefore unreachable during normal startup. Tests cover a missing hard hook but not a missing soft hook.
- **Why it matters:** removing or mispackaging an advisory hook can block all lifecycle work, contradicting the fundamental hard/soft contract.
- **Minimum remediation:** keep structural registry invalidity fail-closed, but defer executable availability handling until after classification so a missing soft hook is observable and nonblocking.
- **Required verification:** isolated missing-hard and missing-soft tests, including mixed events and deterministic diagnostics/exit codes.

### P6-R04 — Startup diagnostics can leak private paths and escape the 0/2 exit contract

- **Severity:** HIGH
- **Files:** `scripts/hooks_runner.py`, `scripts/hooks/registry.py`, `tests/test_hook_engine.py`
- **Requirement violated:** D-P6-004, privacy, deterministic sanitizer fallback, exit codes restricted to 0/2
- **Evidence:** `HOOK_TIMEOUT` is parsed without a guard; a nonnumeric value produced exit 1 plus a traceback and an absolute repository path. Registry-load errors embed raw exception text and are printed before canonical diagnostic sanitization; a synthetic private path was emitted unchanged.
- **Why it matters:** malformed environment or registry data can leak usernames/private paths and bypass the hard-failure surface.
- **Minimum remediation:** route all startup/config/registry failures through a total sanitizer with constant safe fallback text and normalize all terminal failures to 0 or 2.
- **Required verification:** tests for invalid timeout, registry exceptions containing private paths/secrets, sanitizer failure, non-UTF-8 text, and an assertion that every runner path exits only 0 or 2.

### P6-R05 — Codex generator and tracked runtime config drift, and parity checking can be bypassed

- **Severity:** HIGH
- **Files:** `scripts/setup-codex-config.py`, `.codex/hooks.json`, `scripts/hooks/registry.py`, `tests/test_hook_engine.py`
- **Requirement violated:** D-P6-005 definition of done; generated/tracked equivalence; no registered direct bypass
- **Evidence:** tracked Codex config contains canonical `auto-council-trigger`, `memory-capture`, and a session router that the generator source omits and would overwrite. The hard-gate test checks only generated-hard minus tracked-hard, so it cannot detect deletion of tracked compatibility hooks. The checker substring-scans matcher blocks; a config with IDs under a wrong matcher and noncanonical commands can pass.
- **Why it matters:** routine setup can silently delete memory/observer behavior, and `--check` can approve hooks under the wrong lifecycle event or command.
- **Minimum remediation:** define one structured generated model for the full tracked surface and validate exact event/matcher/command/output semantics against the registry.
- **Required verification:** no-write round-trip equivalence, bidirectional hook-set comparison, negative wrong-matcher/wrong-command tests, and explicit Stop/UserPromptSubmit output assertions.

### P6-R06 — Focused tests mutate live repository state

- **Severity:** MEDIUM
- **Files:** `tests/test_hook_engine.py`
- **Requirement violated:** Phase 6 temporary-fixture/isolation contract; repeatable read-only-safe validation
- **Evidence:** reviewed tests overwrite a live `.tmp/a-flow.json`, create a repository-root dirty marker, and sweep live PostToolUse state. Restore-on-success does not protect concurrent agents or interruption.
- **Why it matters:** a verification run can corrupt another session's state or produce environment-dependent results.
- **Minimum remediation:** redirect every mutable state surface to isolated temporary directories/repositories via explicit environment/config seams.
- **Required verification:** run the focused suite twice with repository status and relevant state-tree hashes unchanged before/after; include interrupted/concurrent safety where practical.

### P6-R07 — The local handoff contains machine-specific paths

- **Severity:** MEDIUM
- **Files:** `docs/migration/phase-6-execution-handoff.md`
- **Requirement violated:** public-repository privacy rule; portable handoff contract
- **Evidence:** the reviewed untracked handoff embeds local machine/worktree paths rather than placeholders or repository-relative identities.
- **Why it matters:** committing it would publish private machine information and make the checkpoint nonportable.
- **Minimum remediation:** replace machine paths and usernames with repository-relative references or placeholders; record only public-safe branch/SHA evidence.
- **Required verification:** privacy scan plus an explicit absolute-path/username search over the staged handoff.

## Existing validation evidence

The implementation handoff recorded:

- focused Phase 6 suite: **123 passed / 1 skipped / 3 warnings / 0 failures**
- registry check: **29 hooks / 17 hard / 12 soft**
- privacy gate: exit 0
- security scan: exit 0
- CI secret-hook smoke: exit 0
- `git diff --check`: exit 0

These results do not close P6-R01..P6-R07 because the focused suite has provider-parity, soft-missing, startup-error, generator-equivalence, and test-isolation gaps.

Historical full-suite evidence recorded **2,827 passed / 41 failed / 17 skipped / 8 warnings**. Approximately 35 failures looked plausibly platform-related, but no final full-suite run exists for a committed Phase 6 SHA. This classification must be rechecked after remediation rather than inherited blindly.

The independent review did not rerun the focused suite because the identified tests write live repository state and the review was explicitly read-only.

## Decisions preserved for later phases

The durable long-term architecture remains unchanged:

- Phase 7: Model / Provider Control Plane
- Phase 8: eval-vs-routing split and first automated reviewer adapter foundations
- Phase 9: A-Loop v2
- Phase 10: optional external modules
- Phase 11: documentation slimming/operator docs
- Phases 12–16: Agent Registry, Assignment Engine, Orchestrator Service + MCP, Operator UI/integrations, Autonomous Loop Hardening

All are **NOT_STARTED**. No finding authorizes their implementation during Phase 6.

## Do not do

- do not reset, clean, stash, rebase, delete, or overwrite local WIP
- do not weaken tests or bypass hooks
- do not edit `main` directly
- do not regenerate configuration during continuity recovery
- do not start Phase 7 or Phases 12–16
- do not treat this review as PASS for any commit

## Ordered resume checklist

1. Recheck repository identity, branch, HEAD, dirty state, all worktrees, live claims, and open PRs through any available local/GitHub tool surface.
2. Stop on identity or ownership conflict.
3. Reconcile the docs-only continuity PR without overwriting the local Phase 6 delta or protected other worktrees.
4. Replace the stale local handoff with the corrected durable handoff.
5. Remediate P6-R01 first, then P6-R02..P6-R07, test-first and within the authoritative work order.
6. Run isolated focused, parity, privacy, security, CI-secret, diff, and full regression gates.
7. Commit/push an exact Phase 6 SHA and request a fresh independent review.

## Single next safe action

Reconcile the docs-only continuity PR into the verified Phase 6 branch without overwriting local WIP; then begin the P6-R01 test-first remediation slice.
