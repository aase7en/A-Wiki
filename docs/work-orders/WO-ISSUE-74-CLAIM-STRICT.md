# WO-ISSUE-74-CLAIM-STRICT

Status: IMPLEMENTED / AWAITING_INTEGRATOR_REVIEW
Issue: aase7en/A-Wiki#74
Dependency: aase7en/A-Wiki-Conductor#734
Risk: R2, additive parser contract with tests
Branch: `feat/claim-strict-contract`
Base: `69874673` (live origin/main fetched before work)
Owner: `kilo-claim-strict`

## Scope And Entry

- `conductor/state.py`: opt-in strict parser, history, and canonical reader.
- `tests/test_claim_strict.py`: deterministic strict/legacy regression contracts.
- This work order and the lane's own `COLLAB.md` claim row only.
- Prior issue #58 is CLOSED and PR #67 MERGED at `4c817f2`; its leftover
  COLLAB row is historical, not concurrent work. Do not alter that row.
- No matching open branch/PR; no protected-root file edits, secrets, process
  operations, CLI migration, claim-authority redesign, or merge.

## Root Cause And Choice

Malformed rows are discarded before duplicate matching; history exceptions are
discarded before generation defaults to one. Both defects remain on live main.
Changing legacy functions would break compatibility. Chosen alternative:
opt-in strict APIs using existing `ClaimLookupError`, sharing canonical record
validation without changing legacy behavior. No new error framework/store.

## Acceptance And Test-First Plan

1. Reproduce legacy malformed conflicting row acceptance and history fallback.
2. Add failing strict tests for short/long rows anywhere in the claim region,
   ambiguity, Git log/diff/probe errors, shallow history, happy path, BOM/CRLF.
3. Implement strict APIs; leave all lenient public behavior unchanged.
4. Run focused and related tests, diff/privacy/security checks; record results.
5. Commit/push, open draft PR with Loop-Evidence; integrator reviews and merges.

Failure-model checks: do not skip malformed underscore/separator rows before
width validation; blank lines do not end claims; other tables/prose do. Git
availability must be proved for the shallow probe, log, and diff separately.
Rollback is removal of additive APIs/tests; no persisted schema migration.

## Checkpoint

- Entry preflight: branch check reports FAIL because it expects main, contrary
  to isolated-branch policy; other checks OK, optional Drive absent. No dashboard
  started because the mission forbids process operations.
- Durable claim registered through `python -m conductor claim`, RECONCILED.
- Claim bootstrap committed/pushed as `5b30158d` before production mutation.

## Verification Checkpoint

- RED: `python -m pytest tests/test_claim_strict.py -q`: 23 failed (strict
  APIs absent), 2 passed (legacy malformed-conflict and Git-fallback repros).
- GREEN, final: `python -m pytest tests/test_claim_strict.py -q`: 33 passed.
- Compatibility: `python -m pytest tests/test_conductor.py tests/test_agent_claims.py tests/test_check_agent_claim_hook.py -q`:
  first run 124 passed / 1 failed (unrelated FTS search JSON decode); direct
  search rerun succeeded, then identical full suite rerun: 125 passed.
- `python scripts/check-privacy.py`: PASS after replacing the scanner-flagged
  synthetic test email with `noreply`; no real personal data was involved.
- `python scripts/security/scan_repo.py --ci --baseline scripts/security/baseline.txt`:
  PASS, 51 baselined findings / 0 new (tracked-file scan rerun before delivery).
- `git diff --check`: PASS.
- Live-worktree strict reader smoke on this lane's exact task: PASS, generation
  1, owner and branch match. No machine-local path emitted.
- Review: canonical validation/output is shared, lenient parsing/generation and
  fallback ordering remain unchanged. Strict width validation precedes skips;
  all three Git-history calls must succeed. No downstream callers migrated.
- Prevention tier 1: executable regressions in `tests/test_claim_strict.py`.
- No native subagent/review dispatch tool is exposed in this executor; independent
  exact-head review and final merge remain the integrator's responsibility.

## API Handoff

Use `read_canonical_claim_strict(repo_root, task_id)` for AWC PR #734.
`parse_claims_strict(collab)` and `claim_generation_strict(repo_root, task_id)`
are also available. All failures use existing `ClaimLookupError` (ValueError):
`CLAIM_TABLE_MALFORMED`, `CLAIM_TABLE_UNAVAILABLE`, `GIT_UNAVAILABLE`,
`GIT_HISTORY_SHALLOW`, plus existing task/ambiguity/owner/branch/scope errors.
BOM/CRLF are explicitly accepted. Record schema stays `awiki-claim-reader/v1`.

Next safe action: integrator independently reviews the final PR head and CI,
then adopts the opt-in reader downstream. Do not merge from this lane. This
lane's durable claim is released in the implementation commit; historical
claims and protected-root dirty files are untouched.
