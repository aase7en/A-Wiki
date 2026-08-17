# A-Wiki vNext — Phase 1 Architecture Review

> Review target: `0a4ffa0d8b584d58729b8c18f98aacf5de5cab48`
> Reviewer: ChatGPT / Architecture + QA
> Date: 2026-08-17
> Verdict: **CHANGES_REQUIRED**
> Scope: Phase 1 — Stabilize Automation

## Summary

Phase 1 is directionally strong and P1.1–P1.4 substantially improve repository safety. The clean branch remains isolated from unrelated WIP, `session_start.py` no longer rebases non-main branches, model-pool telemetry no longer churns Git history, and the obsolete/fail-open workflows were removed.

However Phase 1 cannot close yet because two implementation defects and one verification gap remain. The most important finding is that `subagent-eval.yml` still has direct-main mutation paths, so the Phase 1 exit claim that no scheduled/ungated automation can mutate `main` is not yet true.

---

## R-P1-001 — BLOCKER — `subagent-eval.yml` still mutates checked-out main directly

**Area:** automation safety / promotion gate

### Evidence

Current `subagent-eval.yml` still has:

- weekly `schedule` trigger
- workflow-level `permissions: contents: write`
- `Commit new results file` → `git commit` + bare `git push`
- `Snapshot race results (history)` → `git commit` + bare `git push`
- manual `Auto-apply recommendations` path → modifies routing and performs direct commit/push instead of a promotion branch + PR

These paths remain outside the promotion-gate pattern introduced for `agent-model-scan.yml`.

### Impact

The Phase 1 exit statement — "no scheduled automation can mutate main ungated" — is false while this workflow remains unchanged. Pushes made with the workflow `GITHUB_TOKEN` may also avoid normal push-triggered CI chaining, which is exactly the safety class Phase 1 is meant to eliminate.

### Required action

Do **not** perform the full Phase 8 redesign yet. Apply only a Phase-1 safety patch:

1. Scheduled eval/race results must be report/artifact-only; no commit/push to the checked-out default branch.
2. Remove bare `git push` mutation paths.
3. Manual adaptive-routing/model-policy changes must either:
   - become preview/recommendation-only until Phase 8, **or**
   - write only to a named `promotion/...` branch and open a PR.
4. If any other direct-write step exists later in `subagent-eval.yml` (including cost optimization), apply the same rule.
5. Prefer least privilege: scheduled/report execution should not hold `contents: write` when it does not need it.
6. Add regression tests that prove scheduled execution is report-only and no policy mutation can directly push the checked-out `main` branch.

### Acceptance

- no scheduled path in `subagent-eval.yml` can commit/push repository changes
- no manual policy-apply path directly pushes `main`
- promotion mutation, if retained, targets a named promotion branch + PR
- workflow tests cover these invariants

---

## R-P1-002 — MAJOR — Telegram report truncates after 4,000 characters

**Area:** `provider-balance.yml` / reporting correctness

### Evidence

The new sender computes chunks with logic equivalent to:

```python
limit, chunk = 4000, 3600
parts = [text[i:i + chunk] for i in range(0, min(len(text), limit), chunk)]
```

For any report longer than 4,000 characters, everything after character 4,000 is silently discarded. The comment says the implementation chunks a Telegram report, but it currently truncates the report instead.

### Required action

Chunk the **entire** report, not only the first 4,000 characters. Each emitted message must remain below Telegram's message-size limit including header/suffix.

Add a deterministic test using a synthetic report larger than two chunks (for example >8,000 chars) and verify:

- all source content is represented exactly once and in order
- multiple messages are produced
- each message stays within the configured safe limit
- no silent truncation occurs

Prefer extracting the chunking logic into a small testable Python helper rather than testing YAML text only if that can be done without unnecessary Phase-1 scope expansion.

---

## R-P1-003 — MAJOR EVIDENCE GAP — `0 new failures` is not yet an apples-to-apples baseline comparison

**Area:** regression evidence

### Evidence

Phase 0's original full-suite capture reported:

```text
2,867 collected
2,856 passed
9 failed
2 skipped
```

That run occurred on the pre-remediation history that contained additional carried commits/tests. The clean migration branch was later rebuilt directly from `origin/main`.

Phase 1 reports:

```text
2,538 passed
3 failed
17 skipped
```

That totals a substantially different test population. Therefore the statement `0 new failures` cannot be proven by directly comparing the Phase 1 run with the original Phase 0 suite count.

### Required action

Establish a clean base-vs-head comparison using the same environment and exact test command:

1. clean worktree at base SHA `e532d2f0aeb116d06fe854d47c3cf386e95be955`
2. run the same full test command
3. run the same command at the Phase-1 fixed HEAD
4. compare failing test IDs and collection/skip counts

If the exact base run is expensive, it only needs to be done once and recorded as the canonical clean baseline for future phases.

Update migration evidence to distinguish:

- historical Phase-0 contaminated/pre-remediation baseline
- canonical clean-base baseline
- Phase-1 head result

### Acceptance

The claim `0 new failures` must be supported by an exact base-vs-head comparison, not by file-touch inference alone.

---

## R-P1-004 — MINOR — promotion PR creation is fail-open

**Area:** `agent-model-scan.yml`

The promotion step currently uses a pattern equivalent to:

```bash
gh pr create ... || echo "PR create failed ..."
```

This can leave a pushed promotion branch while the workflow still appears successful even though the required PR gate was not created.

### Required action

Do not silently treat a failed promotion-PR creation as success. Either:

- let `gh pr create` fail the promotion step, or
- explicitly detect an already-open PR and verify it exists before reporting success.

This finding is not a direct-main safety blocker, but fixing it in this remediation keeps the promotion gate truthful.

---

## Positive findings

### P1.1 — PASS

`session_start.py::git_pull` now enforces main-only + clean tracked tree + `--ff-only`. The change directly addresses DISC-001 and is backed by focused tests.

### P1.2 — PASS WITH NOTE

Scheduled model scan is dry-run by default and mutation is moved to a named promotion branch + PR. Resolve R-P1-004 so the PR gate is fail-closed/truthful.

### P1.3 — PASS

Model-pool runtime telemetry no longer auto-commits every six hours; workflow is report/artifact-only and the runtime cache is ignored by Git.

### P1.4 — PASS

The fail-open daily-maintenance workflow and duplicate Pages deployment workflow are removed after dependency/reference inspection.

### P1.5 — CHANGES REQUIRED

Minimal permissions and removal of the unpinned Telegram action are good changes, but report chunking must be corrected per R-P1-002.

---

## Required remediation order

1. **R-P1-001** — neutralize every direct-main mutation path in `subagent-eval.yml`.
2. **R-P1-002** — fix full Telegram report chunking + deterministic test.
3. **R-P1-003** — establish canonical clean-base regression comparison.
4. **R-P1-004** — make model-scan PR creation fail-closed/truthful.
5. Run targeted tests for each finding.
6. Run the agreed Phase-1 regression command at the fixed HEAD.
7. Update `docs/migration/awiki-vnext-plan.md` with the remediation evidence.
8. Push to `refactor/awiki-kernel-vnext-clean` and STOP for re-review.

Do not begin Phase 2.

## Re-review handoff

GLM should report only:

```text
PHASE 1 REMEDIATION READY
Branch: refactor/awiki-kernel-vnext-clean
HEAD: <sha>
Resolved: R-P1-001, R-P1-002, R-P1-003, R-P1-004
Canonical base test summary: ...
Fixed-head test summary: ...
```

The reviewer can read all diffs/evidence from GitHub; no long copy/paste report is required.
