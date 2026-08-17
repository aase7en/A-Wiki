# A-Wiki vNext — Phase 2 Architecture Review

> Review target: `dff83ebb8cc8f9f9fe83d0e82bf723592e96a0de`
> Reviewer: ChatGPT / Architecture + QA
> Date: 2026-08-17
> Verdict: **CHANGES_REQUIRED**
> Phase 3 authorization: **NOT GRANTED**
> Scope: Phase 2 — CI & Health Refactor

## Summary

Phase 2 is directionally strong. The monolithic CI was split, the canonical planted-secret regression was fixed, security orchestration moved to Python, wiki-health gained real checks, MCP/hook smokes were added, and the canonical local full suite is now green.

However the Phase-2 objective is not yet satisfied because the new "authoritative" CI/security/health layer still contains four correctness gaps. Two are hard security/CI blind spots and one is a cross-platform baseline bug that is likely to make Ubuntu CI disagree with the Windows-local green result.

Do not start Phase 3 until these findings are resolved and re-reviewed.

---

## R-P2-001 — BLOCKER — Core/domain CI do not run on pull requests

**Area:** CI authority / promotion gates

### Evidence

`.github/workflows/ci-core.yml` currently triggers on:

```yaml
on:
  push:
    branches: [main]
  workflow_dispatch:
```

There is no `pull_request` trigger.

`domain-tests.yml` likewise runs on push-to-main/path, schedule, and dispatch, but not on PRs.

Phase 1 deliberately moved automated mutations to `promotion/...` branches + pull requests and describes CI as part of the promotion gate. Without PR-triggered CI, those promotion PRs can be reviewed/merged before the new core CI or relevant domain regression runs. The branch review target itself also has no GitHub check/status evidence because the workflow cannot trigger on this PR-style branch flow.

### Required action

1. Add `pull_request` targeting `main` to `ci-core.yml`.
2. Add `pull_request` targeting `main` with the same quant/domain path filters to `domain-tests.yml`.
3. Preserve `push: main` as post-merge defense-in-depth and `workflow_dispatch` for manual use.
4. Add tests that pin the PR trigger contract so it cannot silently regress.
5. Ensure promotion PR wording that says "CI required" now corresponds to an actually triggered CI workflow.

### Acceptance

- every PR to `main` receives core CI
- a PR touching quant/MC paths receives domain regression before merge
- push-to-main still runs core CI
- workflow tests assert these triggers

---

## R-P2-002 — BLOCKER — Security scanner scans only the first 256 KiB of each file

**Area:** repository secret scanning

### Evidence

`scripts/security/scan_repo.py` defines:

```python
CHUNK_BYTES = 262_144
```

but `scan_file()` performs only one read:

```python
head = path.open("rb").read(CHUNK_BYTES)
...
text = head.decode("utf-8")
return scan_text(text, ...)
```

Despite comments describing chunked/full coverage, there is no loop/reopen that scans bytes after the first chunk. A secret placed after byte 262,144 is invisible to the hard gate.

This recreates the exact class of silent coverage cap Phase 2 was intended to remove.

### Required action

Implement complete-file scanning without imposing a silent byte cap. Prefer streaming/line iteration so large text files do not require unbounded memory.

Requirements:

- every byte/line of a tracked UTF-8 text file is covered
- correct line numbers are retained
- binary files may still be skipped according to an explicit policy
- a secret after `CHUNK_BYTES` must be detected
- add a regression test with a planted secret beyond 256 KiB
- include a boundary case so a long line/token near the former chunk boundary cannot escape detection

### Acceptance

A tracked text file larger than the old cap fails `--ci` when a planted secret appears after the old 256 KiB boundary.

---

## R-P2-003 — BLOCKER — Security baseline key is too coarse and suppresses new findings

**Area:** security baseline ratchet

### Evidence

`Finding.baseline_key()` is currently:

```python
return f"{self.path}::{self.pattern}"
```

and baseline keys are loaded into a `set`.

This means once a file+pattern pair is baselined, **any later finding using the same pattern in that same file is also treated as legacy debt**, even if it is a newly introduced secret/path. Duplicate baseline lines do not help because converting them to a set discards multiplicity.

Example failure mode:

```text
legacy.py has one baselined gh-token finding
→ developer adds a second different gh-token to legacy.py
→ both produce legacy.py::gh token
→ new token is suppressed as baseline
```

That contradicts the stated contract "any NEW finding fails".

### Required action

Make the ratchet finding-specific without storing raw secrets in the baseline.

A safe design may use a cryptographic fingerprint of the matched value/context plus path+pattern, and must preserve occurrence multiplicity (for example a Counter/multiset rather than a set) so adding another identical occurrence can still be detected.

Do not put raw token/secret values into `baseline.txt`.

Add regression tests proving:

1. the original known finding is baselined
2. adding a **different** same-pattern finding in the same file fails
3. adding an additional identical occurrence beyond the baselined count also fails
4. baseline data contains no raw secret

### Acceptance

A baseline can suppress exactly the known legacy findings and no more.

---

## R-P2-004 — BLOCKER — Wiki-health baseline identities are OS-dependent

**Area:** cross-platform CI / wiki-health ratchet

### Evidence

`check_wikilinks()` renders page identity with:

```python
f"{page.relative_to(wiki_root)}: ..."
```

and `_hard_key()` preserves that platform-native string.

The committed `scripts/health/wiki-health-baseline.txt` visibly contains Windows-style keys such as:

```text
[wikilinks] concepts\ai-tools\agent-framework-tradeoffs.md::CLAUDE.md
```

`ci-core.yml` runs on `ubuntu-latest`. On Linux the same `Path` string uses `/`, so the generated key becomes roughly:

```text
[wikilinks] concepts/ai-tools/agent-framework-tradeoffs.md::CLAUDE.md
```

and no longer matches the Windows-generated baseline.

Therefore the local Windows green result does not establish that Ubuntu GitHub CI will pass; legacy debt may be reclassified as new hard errors purely because of path separator differences.

### Required action

1. Normalize all stable wiki-health path identities to POSIX `/` before rendering/baselining/comparison (`Path.as_posix()` or equivalent).
2. Regenerate/normalize `wiki-health-baseline.txt` to the canonical portable representation.
3. Add a cross-platform identity regression test that proves `\` and `/` representations normalize to one baseline key.
4. Ensure JSON/human reports can remain readable, but machine identity must be platform-independent.

### Acceptance

The same repository state produces the same baseline keys on Windows, Linux, and macOS.

---

## R-P2-005 — NOTE — Frontmatter validation silently passes when PyYAML is unavailable

**Area:** truthful standalone health reporting

`_parse_frontmatter()` currently catches `ImportError` for `yaml` and returns `(None, None)`, which looks identical to "no frontmatter / no error". CI explicitly installs PyYAML, so this does not block the GitHub CI path, but the canonical `wiki_health.py` command can appear green on a local environment where frontmatter was never validated.

This is non-blocking for Phase 2 if the CI dependency contract is explicit. Preferred follow-up: report the check as skipped/dependency-missing or fail loudly rather than silently treating it as OK.

---

## Positive findings

### P2.1 — PARTIAL PASS

The original planted-secret crash was correctly root-caused: fallback patterns now use the same 3-tuple shape as YAML-loaded patterns. `git ls-files -z` also fixes filename word-splitting and removes the old 5,000-file list cap. Resolve R-P2-002 and R-P2-003 before calling the repository scan authoritative.

### P2.2 — PASS WITH REQUIRED CROSS-PLATFORM FIX

The new health script checks real wikilinks, frontmatter, aliases, graph edges, orphans, generated context and skill-surface drift, with hard/advisory separation. Resolve R-P2-004 so the ratchet is actually portable to Ubuntu CI.

### P2.3 — CHANGES REQUIRED

Core/domain split is structurally good and domain coverage was preserved, but PR triggers are mandatory for the promotion-PR model. Resolve R-P2-001.

### P2.4 — PASS

MCP import/tool-surface smoke and vendor-neutral `hooks_runner.py` hard-gate smoke materially improve cross-agent parity.

### P2.5 — PASS WITH NOTE

The neural-spine parity failure was a stale test contract and the dashboard size change is explicitly documented as a contract reclassification rather than silently deleting the assertion. Keep the dashboard budget visible and revisit if markup continues growing.

---

## Regression evidence assessment

The committed Phase-2 log reports the canonical command moving from:

```text
base: 3 failed / 2513 passed / 17 skipped
head: 0 failed / 2584 passed / 17 skipped
```

This is useful local evidence and no new pytest regression is apparent. It does **not** replace GitHub/Ubuntu CI evidence because R-P2-001 currently prevents PR CI from running and R-P2-004 can produce OS-specific behavior.

---

## Required remediation order

1. **R-P2-002** — remove the 256 KiB security-scan blind spot + tests.
2. **R-P2-003** — make security baseline finding-specific/multiplicity-aware + tests.
3. **R-P2-004** — normalize wiki-health baseline identities cross-platform + regenerate baseline + tests.
4. **R-P2-001** — add PR triggers to core/domain CI + trigger-contract tests.
5. Optionally address R-P2-005 if it remains small and does not expand scope.
6. Run targeted tests for each finding.
7. Run the canonical full suite again.
8. If possible, create/use a PR or equivalent review branch event and provide actual GitHub Actions evidence for `ci-core` (and domain workflow when path-relevant).
9. Update `docs/migration/awiki-vnext-plan.md` with remediation evidence.
10. Push only `refactor/awiki-kernel-vnext-clean` and STOP for re-review.

Do not begin Phase 3.

## Re-review handoff

GLM should only need to report:

```text
PHASE 2 REMEDIATION READY
Branch: refactor/awiki-kernel-vnext-clean
HEAD: <sha>
Resolved: R-P2-001, R-P2-002, R-P2-003, R-P2-004
Canonical full-suite summary: ...
GitHub CI evidence: ...
```

The reviewer will read the implementation and evidence directly from GitHub; no long copy/paste report is required.
