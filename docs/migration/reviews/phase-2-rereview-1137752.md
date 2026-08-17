# A-Wiki vNext — Phase 2 Re-review

> Review target: `1137752ee9b8ce98fae96a537ab9998d35b5cb44`
> Reviewer: ChatGPT / Architecture + QA
> Date: 2026-08-18 ICT
> Verdict: **CHANGES_REQUIRED (verification blocker only)**
> Phase 3 authorization: **NOT GRANTED**

## Clarification

The executor did **not** drift into A-Wiki graph work. The reported `GraphQL 503` was the GitHub GraphQL API used while trying to inspect/manage PR and Actions state.

The Phase-2 remediation itself is directionally correct and the prior code findings appear resolved. The remaining blocker is end-to-end CI verification on PR #11.

## V-P2-001 — PR #11 is currently not mergeable, so pull_request CI cannot prove the new gate

Current PR #11:

- base: `main`
- head: `refactor/awiki-kernel-vnext-clean`
- head SHA at review: `1137752ee9b8ce98fae96a537ab9998d35b5cb44`
- GitHub reports `mergeable: false`
- branch is 30 commits ahead and 1 commit behind `main`
- the one newer main commit is `569cd4d3 chore(swarm): auto-update model pool [skip ci]`, produced by the old main-side automation
- no pull_request workflow run exists for the current head

GitHub documents that `pull_request` workflows do not run while a pull request has a merge conflict. Therefore the absence of a run is not sufficient evidence that the new `pull_request` trigger is broken.

`workflow_dispatch` returning 404 for the new workflow is expected because manual dispatch requires that workflow file to exist on the default branch first.

## Required action

Do **not** rebase. DISC-001 established that rebase-style automatic synchronization is unsafe for this migration.

1. In the clean migration worktree, run `git fetch origin`.
2. Confirm the only commit behind is still the main-side bot model-pool commit (or document any newer commits before proceeding).
3. Merge `origin/main` into `refactor/awiki-kernel-vnext-clean` using an explicit merge, not rebase.
4. Resolve conflicts narrowly. If the expected conflict is the runtime `scripts/hermes/model-pool/model-pool.json` that Phase 1 intentionally removed from Git tracking, preserve the Phase-1 design: do **not** reintroduce runtime telemetry into Git merely to satisfy the merge.
5. Inspect the merge diff and ensure no unrelated main-side generated/runtime churn is accidentally restored.
6. Run targeted Phase-1/2 workflow/security/wiki-health tests plus the full canonical suite.
7. Push the merge resolution to the same branch. This should emit a `pull_request synchronize` event once PR #11 is mergeable.
8. Wait for GitHub to evaluate PR #11. Verify:
   - PR becomes mergeable
   - `A-Wiki Core CI` runs on the PR merge ref
   - core CI conclusion is success
   - domain workflow runs only if its path filters match; absence is acceptable when no quant path changed
9. If PR is mergeable but no core run appears after a fresh synchronize event, record that separately as a platform/trigger defect with evidence. Do not merge simply to test the workflow.
10. STOP. Do not begin Phase 3 and do not merge PR #11 until reviewer PASS.

## What is already accepted

Subject to final CI proof, the following remediation items are accepted in principle:

- R-P2-001: pull_request triggers added to core/domain workflows
- R-P2-002: security scan now reads the full file instead of only the first 256 KiB
- R-P2-003: security baseline identity is finding-specific/fingerprinted with multiplicity
- R-P2-004: wiki-health baseline identities are POSIX-normalized across operating systems
- R-P2-005: missing PyYAML is surfaced as an explicit skip rather than silent green
- canonical local suite reported green: `2595 passed, 17 skipped, 0 failed`

## Handoff

After the conflict is resolved and CI runs, report only:

```text
PHASE 2 FINAL VERIFICATION READY
Branch: refactor/awiki-kernel-vnext-clean
HEAD: <sha>
PR #11 mergeable: yes/no
Core CI: success/failure/no-run
Domain CI: success/failure/not-applicable
Full suite: <summary>
Conflict resolution: <one-line summary>
```

No Phase 3 work is authorized yet.
