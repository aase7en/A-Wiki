# WO-AGENT-FAST-PATH-20260913 — Risk-adaptive execution fast path

Date: 2026-09-13 (Asia/Bangkok)
Status: IN_PROGRESS
Owner: GPT-5.6 Sol integrator
Risk: R2 governance / execution-policy docs
Branch: `docs/agent-fast-path-20260913`
Base lineage: `origin/docs/agent-evidence-roadmap-20260910-gpt-antiloop@17029d6b`
Parent PR: #59 (stacked lineage; reuse preferred over duplicate PR ceremony)

## Goal

Reduce repeated bootstrap and serial review ceremony while preserving A-Wiki authority, mutation safety, ownership, deterministic verification, exact-SHA review, and durable continuity.

## Brain Gate

- Gain: faster accepted outcomes, bounded retries, less repeated context loading, and parallel review/CI.
- Shape: one on-demand protocol plus small router/governance edits; no new orchestrator or shadow SSoT.
- Weight: keep detailed flow out of always-loaded instructions; load only by risk/task routing.
- Safety: public docs only; isolated worktree; no raw/private/secret data.
- Verify: focused protocol checks, privacy/security gates, actual diff, PR CI, exact-SHA independent review when available.

## Authority / reuse boundary

- Reuse `BRAIN-ENTRY.md`, `PROJECT-GRAPH.yaml`, `COLLAB.md`, conductor claims, existing Work Orders, Review Bus/PR evidence, and defect-memory rules.
- Do not replace `a-flow` runtime state machine. The new protocol selects gate depth and anti-loop behavior around existing execution.
- Existing anti-loop rule from `17029d6b` remains authoritative for unchanged blocker fingerprints and is generalized here rather than duplicated.

## Scope

Expected edits:
- `BRAIN-ENTRY.md`, `AGENTS.md`, `README.md`
- `docs/graph/PROJECT-GRAPH.yaml`
- `docs/protocols/agent-continuity-gate.md`
- `docs/protocols/cross-agent-work-orders.md`
- new `docs/protocols/risk-adaptive-fast-path.md`
- this WO + conductor-managed `COLLAB.md`

Forbidden: production runtime, hooks, skill registry, memory implementation, CI workflow behavior, secrets, provider/auth configuration, or unrelated open work.

## Acceptance

1. Minimum recovery does not require rereading large/static material unless graph/task routing requires it.
2. LOW/NORMAL/HIGH risk paths are explicit; security/secrets/concurrency/durable-state/release remain strongest-gated.
3. Independent review and CI run concurrently on a frozen candidate when both are required.
4. Repeated unchanged failure/blocker cannot loop; same material failure twice without new evidence enters root-cause mode.
5. Worker count is demand-driven; mutable parallel lanes are explicitly owned and non-overlapping.
6. Full suites/checkpoints are boundary-driven rather than run after every micro-edit.
7. Existing repo SSoT/claim/Review Bus/defect memory remain authoritative; no duplicate system is introduced.
8. Explicitly delegated merge authority may complete the merge once all required gates pass; no redundant human click is invented.

## Verification plan

Focused first:
- `git diff --check`
- strict UTF-8/YAML parse for routed files
- existing tests that cover project graph, governance, PR loop, or continuity where present
- `python scripts/check-privacy.py`
- `python scripts/gen-index.py --check`
- `python scripts/security/scan_repo.py --ci --baseline scripts/security/baseline.txt`

Candidate boundary:
- freeze one coherent SHA;
- push/update the existing PR lineage instead of opening an unnecessary parallel PR if remote state permits;
- run hosted CI and independent exact-SHA review in parallel;
- batch confirmed findings into one repair pass, then focused rereview.

## Checkpoint

- Recovery: live `main` = `origin/main@566637ac`; shared main worktree protected because it contains unrelated untracked files.
- Overlap: PR #59 is the only open A-Wiki PR; anti-loop child commit `17029d6b` was recovered and used as this branch base.
- Worker readiness: SunDay Workers 1–5 are occupied on other active projects/lanes; none is safe to rebind.
- Preflight: clean isolated branch; guardrails/hooks valid. `agent-preflight.py` reports only its known main-branch assumption plus optional Drive warning.
- Claim: `FASTPATH-20260913` acquired and pushed at `70aac6d9` before real scope mutation.
- Next safe action: implement protocol/router changes as one coherent docs batch, then targeted verification.
