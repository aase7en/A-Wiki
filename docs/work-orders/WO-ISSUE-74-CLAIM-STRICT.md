# WO-ISSUE-74-CLAIM-STRICT

Status: CLAIMED / TEST_FIRST
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
- Next: commit/push claim, then RED tests before production mutation.
