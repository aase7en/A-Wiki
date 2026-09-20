# WO-A-SECURITY-CLOUDFLARE-20260921 — A-Security upstream integration

Status: CLAIMED / IMPLEMENTING
Owner: GPT-5.6 Sol
Branch: `feat/a-security-cloudflare-upstream`
Base: `origin/main@25102e44950ccd28c2d22eafc6e6f1d2119f18ad`

## Goal

Adopt Cloudflare's `security-audit-skill` as an A-Wiki-owned, on-demand skill named
`a-security`, while preserving upstream provenance, MIT attribution, updateability,
and A-Wiki's existing authority, privacy, claim, verification, and second-brain rules.

## Brain Gate

- Gain: evidence-led multi-phase security audit with coverage ledger, machine-readable findings, and independent verification.
- Shape: reusable skill package under `skills/awiki/a-security/`.
- Weight: on-demand; no new always-on instruction layer.
- Safety: pinned public upstream only; no secrets/private data; security findings remain external/private by default.
- Verify: upstream validator tests + A-Wiki registry/surface/privacy/security checks + exact-SHA independent review + CI.

## Existing-surface delta

Existing `security-scan` is Claude-config/AgentShield focused; `security-and-hardening`
is a preventive checklist; `security-auditor` is a generic reviewer persona.
A-Security adds deterministic coverage planning, verdict schemas, bounded execution
safety, and finder/verifier separation. It does not replace those narrower surfaces.

## GLM_OFFLOAD_ASSESSMENT

No GLM mutation lane for initial integration. This is a HIGH-risk brain/security
change whose import, hashing, registry update, and tests are deterministic. Independent
review will be assigned to a separate read-only Worker after the candidate SHA freezes.

## Upstream pin

- Repository: `https://github.com/cloudflare/security-audit-skill`
- Source path: `skills/security-audit/`
- Pinned commit: `c1c8a8c1471069fb0e188eeaff69b8e8db6564a8`
- License: MIT, Copyright (c) 2025-2026 Cloudflare, Inc.

## Allowed scope

- `COLLAB.md`
- this work order
- `skills-registry.json`
- `skills/awiki/a-security/**`
- `scripts/refresh-cloudflare-security-audit.sh`
- `skills/_upstream/cloudflare-security-audit/**`
- generated skill surfaces produced by `python scripts/regen-skill-surfaces.py`

Forbidden: unrelated skills, AGENTS hand-edits, hooks, runtime code, private data,
secrets, and user/other-agent dirty worktrees.

## Acceptance

1. `/A-Security` resolves through the canonical skill registry and all generated surfaces.
2. Cloudflare source is pinned, attributable, and refreshable without hiding local adaptations.
3. Full-audit execution remains defensive/source-first and never probes live/shared targets.
4. Target-controlled execution fails closed unless the upstream OS-sandbox contract is provable.
5. Audit artifacts/findings default outside tracked public Git; no silent wiki/memory promotion.
6. Upstream validators/tests and A-Wiki registry/privacy/security checks pass.
7. Candidate gets independent exact-SHA review plus hosted CI before merge.

## Verify

```bash
node skills/awiki/a-security/validate-findings.test.cjs
node skills/awiki/a-security/validate-coverage-ledger.test.cjs
python scripts/regen-skill-surfaces.py --check
python scripts/verify-skill-surfaces.py
python scripts/check-privacy.py
python scripts/security/scan_repo.py --ci --baseline scripts/security/baseline.txt
python scripts/audit_a_suite.py
git diff --check
```

## Checkpoint — 2026-09-21 claim/start

- Isolated clean worktree: `<WORKTREE>/A-Wiki-a-security`.
- Shared primary checkout is intentionally untouched because it contains unrelated dirty work.
- Claim committed and pushed as `e073b9b1d452fdbc874915ad2982c3ebeaadf8e5`.
- No competing A-Security branch/PR/claim found after local + GitHub reconciliation.
- Upstream repository and latest pin verified from Cloudflare's official GitHub repository.
- Existing A-Wiki security surfaces inspected; this skill fills a distinct audit-orchestration gap.

**Next safe action:** inspect the complete pinned upstream package for instruction/conflict risk, then import only the compatible package into the claimed scope.
