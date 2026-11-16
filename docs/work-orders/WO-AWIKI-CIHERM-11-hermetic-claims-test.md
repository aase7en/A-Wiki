# WO-AWIKI-CIHERM-11 — Hermetic `conductor claims` CLI test

- Date: 2026-11-16
- Agent: GLM (Kilo)
- Branch: `fix/ci-hermetic-claims-test`
- Status: OPEN → (status updated at close)

## Context

Post-merge Core CI for PR #92 (`a11b8773`, run `43706413589`, 2026-11-15T10:55Z) failed at
`tests/test_conductor.py::TestBridgeCli::test_claims_cli_returns_exact_current_claim`:
CLI exit 1 with `BRANCH_HEAD_UNRESOLVED: fix/issue-58-claim-convergence` in stdout.

The test ran `python -m conductor claims --task-id "Issue #58 claim authority convergence"`
against the **live checkout** and asserted exit 0 + exact JSON. The CLI resolves repo root from
the package location (`conductor/cli.py` `REPO_ROOT = Path(__file__).resolve().parents[1]`) and
`_branch_head()` (`conductor/state.py:226`) resolves branch heads via
`show-ref --verify refs/remotes/origin/<branch>` → `refs/heads/<branch>`.

## Root cause

actions/checkout@v4 ref-fetch topology differs by event, even with `fetch-depth: 0`:

- **pull_request** checkouts fetch all heads → `refs/remotes/origin/fix/issue-58-claim-convergence`
  present → PR rerun `43705645499` passed (after the branch was restored at `c1bf7ea4`).
- **push** checkouts fetch only the pushed branch (`main`) → historical COLLAB row referencing
  another branch is genuinely unresolvable → CLI correctly reports `BRANCH_HEAD_UNRESOLVED`.

Evidence matrix:

| Environment | refs available | CLI result |
|---|---|---|
| PR-head CI (pull_request, depth 0) | all heads | exit 0 |
| main push CI (push, depth 0) | `origin/main` only | exit 1 `BRANCH_HEAD_UNRESOLVED` |
| local Mac (full refs) | all heads | exit 0 |
| fresh `git clone` @ `a11b8773` | all heads | exit 0 |

The CLI behavior is correct (UNRESOLVED on genuinely absent refs is the intended foreign-claim
contract). The defect is the **test's environment coupling** to runner ref topology.

## Options considered

- **A. Test-only:** copy the `conductor/` package into a tmp fixture repo so `REPO_ROOT`
  points at the fixture. No production change, but heavier fixture and never exercises the
  flag surface.
- **B. Production micro-change (chosen):** add optional `--repo-root` to the `claims`
  subcommand (precedent: review bridge already accepts `target_repo`), test passes
  `--repo-root <tmp fixture>`. Smaller fixture, tests the real CLI surface.

Decision: **B**. Jev/Terra consult unavailable this slice (jev-advisory MCP not configured in
this session; Terra weekly quota until 2026-11-20) — disclosed; decision is low-risk and
reversible, both options documented here.

## Changes

1. `conductor/cli.py`: `claims` subparser gains `--repo-root` (default: package REPO_ROOT).
2. `tests/test_conductor.py`: `test_claims_cli_returns_exact_current_claim` rewritten hermetic —
   tmp git repo + COLLAB row mirroring the prod Issue #58 row shape (slashy branch), branch
   created, CLI invoked with `--repo-root`, asserts exit 0 + exact JSON incl. deterministic
   `branch_head_sha`.

## Tests

- RED: new test with `--repo-root` fails before implementation (argparse exit 2).
- GREEN: `pytest tests/test_conductor.py -q` full file.

## Review

GLM subagent independent review (anchored `VERDICT APPROVE`) before merge; no merge on author
self-report.

## Evidence

- Failed main run: `43706413589` (RED at main).
- Passing PR rerun (all-heads topology): `43705645499`.
- Fresh-clone + local resolutions: session log 2026-11-16.
