# WO-A-SECURITY-CLOUDFLARE-20260921 — A-Security upstream integration

Status: CANDIDATE / REVIEW
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
- `scripts/refresh-cloudflare-security-audit.py`
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

## Checkpoint — 2026-09-21 implementation freeze

- Implementation commit: `a6ae2df83f8b67804aa4768df95b8497e675c7c4`.
- Official upstream pin: `cloudflare/security-audit-skill@c1c8a8c1471069fb0e188eeaff69b8e8db6564a8`.
- All 20 files under upstream `skills/security-audit/` match the official GitHub blob SHAs exactly; MIT notice is preserved separately.
- Local adaptation delta is intentionally limited to `skills/awiki/a-security/SKILL.md`: A-Wiki frontmatter/name plus stricter authority/privacy/sandbox integration rules. All companion docs, schemas, validators, and validator tests remain byte-identical to the upstream snapshot.
- Upstream refresh path was exercised successfully; it retained the same current pin and refuses to replace an existing remote with a different URL.
- Native-Windows findings CLI tests fail closed where `O_NOFOLLOW` / `O_NONBLOCK` protection is unavailable; this is the expected platform safety boundary documented by A-Security, not a weakened validator. The coverage-ledger suite passed its Windows-applicable tests.
- POSIX verification on macOS at the exact implementation commit passed `34/34` findings tests and `31/31` coverage-ledger tests.
- A-Wiki checks passed: registry regeneration check, cross-agent skill-surface verification, privacy scan, security baseline scan with `0` new findings, A-Suite audit (with UTF-8 console mode), and `git diff --check`.
- Primary dirty checkout remained untouched; all implementation work stayed in the claimed isolated worktree.

**Next safe action:** commit this checkpoint to freeze the review candidate, then open a draft PR and run hosted CI plus independent exact-SHA review in parallel.
