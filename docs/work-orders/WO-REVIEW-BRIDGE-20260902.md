# WO-REVIEW-BRIDGE-20260902 — Thin conductor Review Bridge (WRAP/EXTEND)

Status: CLAIMED
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

(appended below per coherent chunk — same-file continuity only)
