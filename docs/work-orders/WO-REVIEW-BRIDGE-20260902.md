# WO-REVIEW-BRIDGE-20260902 — Thin conductor Review Bridge (WRAP/EXTEND)

Status: READY_FOR_GPT_PRIMARY_REVIEW (target-repo seam)
Executor: GLM5.3-ZCode-MAX (follow-up deterministic implementation)
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

### 2026-09-03 GPT Primary exact-SHA review finding

- P1: trusted boolean evidence accepts non-bool strings; a false string is truthy in Python and can falsely satisfy retest/CI evidence. Repair must require actual bool values at the API boundary.
- P2: ReviewBusError from delegated operations can escape the adapter and bypass bounded ReviewBridgeError / JSON handling; reproduced with unknown finding resolve. Repair must translate engine contract failures without masking unexpected exceptions.
- RED-first repair is authorized only in review_bridge.py + focused tests; current main portability integration remains preserved.

### 2026-09-03 GPT repair checkpoint

- Current main portability baseline was integrated before repair; candidate remained isolated to the original five-file Review Bridge scope.
- RED: trusted retest/CI accepted non-bool false strings and produced READY; unknown finding resolve escaped as ReviewBusError. Focused run reproduced the three intended defects.
- GREEN: exact bool type checks now reject non-bool trusted evidence; resolve/verify translate ReviewBusError to ReviewBridgeError without masking unexpected exceptions.
- Verification after repair: focused 46/46 PASS; related ReviewBus/A-loop/conductor/kernel 112/112 PASS; broad conductor/review/graph/PR-loop matrix 176/176 PASS. A final CLI unknown-finding bounded-JSON regression was then added and focused suite is 47/47 PASS.
- py_compile on changed Python files PASS; git diff --check PASS; feature-vs-current-main scope remains COLLAB, conductor/cli.py, conductor/review_bridge.py, WO, and focused tests only.
- GPT repaired the reviewed candidate, so merge is intentionally blocked pending fresh independent rereview of the new exact SHA.

### 2026-09-03 GPT adversarial rereview — durable map identity repair

- P1 reproduced: replacing `task-a` durable map bytes with `task-b` map caused `status("task-a")` to report task-b cycle/state under task-a identity. P2 reproduced: truncated/invalid map JSON escaped as `JSONDecodeError`, and CLI emitted traceback/no bounded JSON.
- RED: 3 new task-map regressions failed exactly on corrupt JSON, cross-task map substitution, and CLI bounded-error behavior.
- Repair stays in the thin adapter: `_load_map()` now validates JSON/object shape, exact `task_id`, bounded cycle, Git SHA `head_sha`, and ingest-record shape; `status()` validates the map before `ALoopReview.task_gate()` and translates ReviewBus contract failures without masking unexpected exceptions. ReviewBus/ALoopReview authority remains untouched.
- GREEN exact repaired code: focused Review Bridge **50/50**, related ReviewBus/A-loop/conductor/kernel **112/112**, broad conductor/review/graph/PR-loop **180/180**.
- Gates: `git diff --check`, `py_compile`, privacy, stale-spec PASS; security **6327 tracked / 51 baseline / 0 new**; wiki-health **0 hard / 352 advisory**.
- Draft PR #50 remains intentionally Draft. Because GPT authored all trust-boundary repairs, a fresh independent exact-SHA rereview with P0/P1/P2=0 remains mandatory before ready/merge.

### 2026-09-03 GPT adversarial rereview — RB-A1..A7 closed

- RED proved all original blocker classes on the integrated candidate: stale reviewer result after Git HEAD advance; stale READY after HEAD advance; dirty-worktree READY; repeated `open` authority replacement; crash/replay duplicate finding + non-atomic map write; whole-file CLI ingest before size bound; pinned reviewer identity bypass.
- Additional REDs proved task-map cycle substitution, map↔ReviewBus head drift, and retest head desynchronization.
- Repair remains WRAP-only: ReviewBus and ALoopReview are untouched. Bridge map writes are atomic; staged ingest is replay-safe against partial ReviewBus mutation; map cycle is bound to `executor=bridge:<task>` and ReviewBus head; trusted retest/CI require current clean Git HEAD.
- Reviewer pinning is stored separately from verdict reviewer identity; conflicting/missing model identity fails closed when pinned.
- CLI rejects oversized result files from metadata before whole-file read. CLI tests now use a clean throwaway git repo so full-suite artifacts cannot weaken or spuriously trip the production clean-HEAD gate.
- Verification: focused `pytest tests/test_conductor_review_bridge.py -q` = **62/62 PASS**; related ReviewBus/A-loop/conductor/kernel = **112/112 PASS**; broad conductor/review/graph/PR-loop = **192/192 PASS**.
- Gates: `git diff --check` PASS; `py_compile` PASS; privacy PASS; security `6327 tracked / 51 baseline / 0 new`.
- GPT authored these repairs; independent exact-SHA rereview with P0/P1/P2=0 remains mandatory before Ready/Merge.

### 2026-09-03 post-main follow-up — external target-repo seam

- Accepted Review Bridge: PR #50 head `b04761d580ddcdc7eb682e3a6036078b3b346953`; independent rereview PASS P0/P1/P2=0; merge `588a907200e0d4998ec4fbb7fb2178b89d9700b2`; post-main Core CI `33704270521` SUCCESS.
- Root cause from A-Conductor WO147 realistic-E2E shaping: `conductor.cli.REPO_ROOT` is hard-bound to A-Wiki and `ReviewBridge(REPO_ROOT)` validates A-Wiki Git HEAD only; an A-Conductor mailbox `base_head` therefore cannot be truthfully ingested cross-repo yet.
- Reuse decision: EXTEND the accepted bridge; no second ReviewBus/mailbox/scheduler/provider registry and no direct A-Conductor access to A-Wiki `.tmp`/`scripts.lib`.
- Target contract: A-Wiki remains authority/library/state owner; optional absolute clean `target_repo_root` supplies Git HEAD/dirty truth. Omitted target preserves existing behavior. External-target state remains under A-Wiki ignored local state and is namespaced per target worktree.
- Routing evidence checked 2026-09-03 from official ZCode docs: GLM-5.3/ZCode Agent targets long-horizon multi-file repeated-verification work; `/goal` continues rounds until a checkable goal is met. GLM gets bounded RED→GREEN/regression burn-down; GPT retains architecture/trust-boundary/exact-SHA authority.
- Branch/worktree: `feat/wo-review-target-repo-20260903` / `<WORKTREE>/A-Wiki-review-target-repo-20260903` from accepted main `588a9072...`; primary checkout remains protected.
- Scope remains `conductor/review_bridge.py`, `conductor/cli.py`, `tests/test_conductor_review_bridge.py`, this WO, bounded `COLLAB.md` claim transfer. ReviewBus/ALoopReview/schema/core forbidden.
- Next: commit/push claim; GPT adds RED external-target contract tests; GLM Goal Mode burns RED→GREEN and regressions on this same lane.


### 2026-09-03 target-repo RED contract — GPT architecture lane

- GPT added external-target contract tests only; production remains unchanged at this checkpoint.
- RED focused result: `python -m pytest -q tests/test_conductor_review_bridge.py` = **9 failed / 62 passed**.
- All 9 failures are the intended seam: missing `target_repo_root` API support (7 parametrized/behavior cases) and missing CLI `--target-repo` support (2 cases).
- Contract proves: target HEAD is review HEAD; target dirty state fails closed; review bookkeeping never mutates target; A-Wiki-owned state is isolated per target worktree; target HEAD drift revokes READY; invalid relative/missing/non-git targets fail bounded; CLI open→ingest→retest→CI→READY operates against the external target.
- During RED, an older test oracle was found flaky: it formed a wrong SHA by forcing the last nibble to `0`, which is unchanged when the real SHA already ends in `0`. GPT repaired the oracle to always choose a different nibble; the pre-existing suite then returned to **62 passing** outside the 9 intended REDs.
- Python 3.8 compatibility is preserved in the RED helpers (no `Path.is_relative_to`).
- GLM must now implement only the declared bridge/CLI scope and burn this exact RED set to GREEN; no test deletion/weakening and no ReviewBus/ALoopReview/schema changes.

### 2026-09-03 target-repo seam GREEN — GLM implementation checkpoint

- Identity at start: branch `feat/wo-review-target-repo-20260903`, HEAD `de390f7516563e120aca1e3e3a3ca9c782a989b2` (= expected RED contract head; clean tree; origin/main `588a9072` ancestor). RED confirmed before mutation: **9 failed / 62 passed** exactly as the GPT contract recorded.
- Implementation (minimal, WRAP-only):
  - `conductor/review_bridge.py`: new `_validate_target_repo()` (absolute + existing dir + real Git checkout/worktree incl. linked `.git` gitfile, verified via bounded `git rev-parse --git-dir`; malformed/missing/relative/non-Git ⇒ bounded `ReviewBridgeError`) and `_target_state_namespace()` (sha256 fingerprint of the resolved target — never the raw machine path — under `<authority>/.tmp/review-bridge-targets/`). `ReviewBridge(..., target_repo_root=None)`: omitted ⇒ behavior byte-identical to before (authority is the target, default state dir unchanged); provided ⇒ `self._root` becomes the validated TARGET (all existing HEAD/dirty/stale/READY/retest truth therefore keys to the target), ReviewBus/ALoopReview still import from the AUTHORITY's `scripts/lib`, durable state stays under the authority's ignored `.tmp`, and `gate.git_dir` binds the TARGET `.git`.
  - `conductor/cli.py`: every review subcommand gains the trusted `--target-repo <absolute path>` (plus shared bounded `--json`); bridge construction moved inside the bounded-error `try` so invalid targets emit bounded JSON rc=1 with no traceback. Reviewer JSON can never select the target — it is operator-supplied only.
- GREEN: focused `python -m pytest -q tests/test_conductor_review_bridge.py` = **71 passed** (62 + all 9 RED).
- Adversarial self-review probes (9/9 PASS): full lifecycle leaves the target file tree byte-identical (no state in target, no `.tmp` in target); authority HEAD advance never substitutes target HEAD (open/ingest stay target-bound); same task id fully isolated across two target repos (separate state namespaces, cross-target result rejected); open-on-A + ingest-on-B fails closed; explicit target==authority works end-to-end (documented subtlety: requires the authority's ignored-state convention, e.g. `.tmp/` gitignored as in A-Wiki); linked git worktree full lifecycle + HEAD-advance READY revoke; dirty target after READY demotes `allow_complete`; relative/missing/plain-dir/file targets all bounded; reviewer payload `target_repo`/`state_dir` fields are ignored extras — state stays authority-owned and target-A-bound.
- Related suite: first run **1 failed / 111 passed** (`test_search_fts_returns_structured_hits`), passed in isolation and on rerun **112/112** — the same known environment-flake class already documented in the rereview result; not attributable to this diff (no `conductor/__main__.py`/search change). Broad matrix: **201/201** (192 baseline + 9 new).
- Cross-process CLI E2E: covered by the contract tests via subprocess against an external target (open→ingest→record-retest→record-ci→READY; target stays `git-clean`); invalid target path ⇒ bounded JSON rc=1 without traceback.
- Gates: `py_compile` (3.11 + managed 3.8) PASS · `git diff --check` PASS · strict UTF-8 no U+FFFD PASS · privacy PASS · security **6,327 tracked / 51 baseline / 0 new** · stale-spec PASS · wiki-health **0 hard / 352 advisory**. GitNexus: fresh `analyze --index-only` index for this worktree + impact/detect-changes recorded in the final checkpoint below.
- Findings: P0=0 P1=0 P2=0; P3 notes — (a) explicit target==authority namespaces state under `review-bridge-targets/` (beside the implicit default dir), documented as intentional; requires ignored-state convention when authority==target; (b) the known one-off conductor-search environment flake recurred once and did not reproduce (6+ consecutive green runs across rounds).
- Next: GitNexus evidence → commit/push → READY_FOR_GPT_PRIMARY_REVIEW.

### 2026-09-03 target-repo seam — final checkpoint (READY_FOR_GPT_PRIMARY_REVIEW)

- Final candidate HEAD `bd072204...` (implementation + this WO checkpoint; COLLAB claim release row included). Exact files vs RED base `de390f75`: `conductor/review_bridge.py`, `conductor/cli.py`, `docs/work-orders/WO-REVIEW-BRIDGE-20260902.md`, `tests/test_conductor_review_bridge.py` (RED contract, unchanged by GLM), `COLLAB.md` (claim rows only).
- RED baseline: **9 failed / 62 passed** (confirmed pre-mutation). Focused GREEN: **71 passed**. Related: **112 passed** (one first-run environment flake of the known conductor-search class, unreproduced in isolation + rerun). Broad: **201 passed**.
- Realistic cross-process CLI E2E: contract tests drive subprocess CLI against an external throwaway Git target end-to-end (open→ingest PASS→record-retest→record-ci→READY, target stays git-clean, invalid target bounded JSON). API-level probes additionally prove linked-worktree lifecycle + HEAD-advance revoke and full file-tree immutability of the target.
- GitNexus (fresh `analyze --index-only` for this worktree: 85,283 nodes / 125,148 edges / 700 flows; FTS extension unavailable on this Windows runtime = documented tool limitation): impact `ReviewBridge` LOW (2 impacted / 0 processes), impact `cli.main` LOW (2 / 0); `detect-changes --scope compare --base-ref de390f75` = 3 files / 9 symbols / 3 processes / **risk MEDIUM** (additive seam symbols; below HIGH/CRITICAL stop threshold).
- Gates: `git diff --check` PASS · py_compile 3.11 + managed 3.8 PASS · strict UTF-8 (no U+FFFD) PASS · privacy PASS · security 6,327 tracked / 51 baseline / **0 new** · stale-spec PASS · wiki-health **0 hard / 352 advisory**.
- Findings: **P0=0 P1=0 P2=0**. P3: (a) explicit target==authority uses the namespaced state dir beside the implicit default (intentional; authority must ignore its state path — A-Wiki does); (b) known one-off conductor-search environment flake (documented class, unreproduced).
- Residual risks: external-target trust is operator-supplied absolute path (by design — reviewer JSON cannot select it); namespace fingerprint is deterministic sha256 of the resolved target path (state-dir name only, gitignored, never tracked).
- Next safe action: **GPT-5.6 Sol Max independent exact-SHA review of `bd072204...` (trust boundaries, remote diff, tests), then PR/CI/merge/post-main under GPT authority.**

### 2026-09-03 GPT Primary repair claim - external-target trust boundary

- Primary exact-SHA review of `0ed89003655b07356c84f1d6311ed31b20ce942f` re-ran focused 71/71, related 112/112, broad 201/201, then found two uncovered trust-boundary defects.
- P1/P2 proof 1: supported API `ReviewBridge(authority, target_repo_root=target, state_dir=target / "review-state")` can open successfully and later creates `?? review-state/` inside the target. This violates the target-as-Git-truth-only / authority-owned-state contract.
- P1/P2 proof 2: `_target_state_namespace()` unconditionally `.casefold()`s the resolved target path; `/tmp/Repo` and `/tmp/repo` therefore map to the same namespace even though they can be distinct repositories on case-sensitive filesystems.
- Repair claim is limited to `conductor/review_bridge.py`, focused tests, this WO, and bounded COLLAB bookkeeping. No ReviewBus/ALoopReview/schema/core/A-Conductor mutation. Original `0ed89003...` stays frozen for independent review; repair occurs on `fix/wo-review-target-repo-primary-20260903`.
- RED-first target: reject explicit state-dir override in external-target mode; use platform-correct path normalization for durable target namespace and remove unnecessary digest truncation.

### 2026-09-03 GPT Primary repair final checkpoint — READY_FOR_INDEPENDENT_REREVIEW

- Repair branch: `fix/wo-review-target-repo-primary-20260903`; repaired production head before this checkpoint: `e9e569e5addcdf0e806d83a0945477dfacca3af5`.
- RED commit `d0afb924336ec64f9967a31106f15157c6da4607`: focused suite **2 failed / 71 passed** exactly on external `state_dir` authority escape and truncated/unconditional-casefold namespace semantics.
- GREEN repair changes only `conductor/review_bridge.py`: external-target mode rejects explicit `state_dir`; namespace canonicalization uses host `os.path.normcase` semantics and a full SHA-256 digest.
- Focused GREEN: **73/73 PASS**.
- Related first run: **111/112** with the known one-off `TestBridgeSearch.test_search_fts_returns_structured_hits` environment flake; isolated repeat **8/8 PASS** and related rerun **112/112 PASS**.
- Broad matrix: **203/203 PASS**.
- Gates: `py_compile` PASS; `git diff --check` PASS; strict UTF-8/U+FFFD PASS; privacy PASS; stale-spec PASS; added-line secret scan **0 hits**; wiki-health **0 hard / 352 advisory**.
- Scope remains exactly the accepted target-repo seam files plus bounded WO/COLLAB bookkeeping; ReviewBus/ALoopReview/schema/core remain untouched.
- GPT authored the trust-boundary repair, so independent exact-SHA rereview remains mandatory before PR/merge.

### 2026-09-03 post-merge TR-R3 case-safety repair ? READY_FOR_INDEPENDENT_REREVIEW

- Post-main audit of PR #51 merge `2191f2a1ff4bccc5ebb08b1d2bc87fdbe7ca0826` found a residual P1 trust-boundary defect: `os.path.normcase()` treated Windows OS family as filesystem case semantics even though Windows supports per-directory case-sensitive directories.
- RED commit `e9c4492e1e843cfc8c6d3b3382b3504fae250283`: exact regression `test_external_target_namespace_never_collapses_case_distinct_targets_by_os_family` failed because case-distinct target spellings mapped to one durable review namespace.
- GREEN production repair `e178d2ce2cc28d6117af25f2294262eed4b3fdaa`: namespace hashes the exact resolved target spelling with full SHA-256; no OS-wide `normcase` / casefold inference remains. False separation of aliases is accepted over cross-target state contamination.
- Focused `tests/test_conductor_review_bridge.py` = **74/74 PASS**. Related first run hit the known unrelated FTS environment flake; isolated repeat **8/8 PASS**, related rerun **112/112 PASS**. Broad bridge matrix = **204/204 PASS**.
- Gates: `git diff --check`, `py_compile`, strict UTF-8/U+FFFD, privacy, stale-spec PASS; security **6,327 tracked / 51 baseline / 0 new**; wiki-health **0 hard / 352 advisory**.
- GitNexus local index completed; FTS remained unavailable due the existing Windows runtime DLL limitation. `detect-changes` could not resolve the newly indexed worktree label despite listing it, so detect-changes is `UNVERIFIED ? tool resolver failure`; no system DLL was installed. Prior seam impact was LOW and the repair changes only `_target_state_namespace` plus focused regression tests.
- Defect Memory Tier-1 recorded in `.tmp/memory-ledger.jsonl`; `conductor recall` verified the entry. Mechanism: the RED regression above. Evidence binds RED `e9c4492e...` to GREEN `e178d2ce...`.
- GPT authored this forward-only repair, so a fresh independent exact-SHA rereview with P0/P1/P2=0 remains mandatory before PR/CI/merge.
