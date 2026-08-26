# Changelog

All notable A-Wiki changes are tracked here so every clone, device, and AI
agent can tell what capability level the repository is at.

Format: keep the newest release first. Use small, operational entries that
explain what changed and how to verify it.

## 1.4.0 - 2026-08-26

Migration complete + brain-enhancement round (≈1,100 commits since 1.3.0;
verify each via `python scripts/awiki-doctor.py --full`, full pytest suite,
and CI history).

### Added
- **vNext migration phases 5–11 complete**: memory layers L0–L5 · hook
  engine (registry authority, 30 hooks, 4 providers incl. ZCode+Gemini
  wiring) · model control plane · review-bus (findings/SHA-bound
  approval/halt) · A-Loop v2 completion gate · world-intel lazy bridge ·
  operator runbook.
- **Brain enhancement (6 slices)**: `awiki adopt <repo>` (brain gates in
  any repo, cross-repo E2E) · skill pipeline (propose → deterministic
  auto-eval → one-button approve + scout) · grill with live upstream docs
  (`docs:` frontmatter, honest cache-stale labels) · stale-spec CI gate +
  plan fold-back stop hook · loop budget/halt + persona memory + nightly
  synthesis cron · `awiki doctor`/`guide` + TH/EN getting-started.
- **Universal Loop Contract (CI-enforced)**: every PR carries
  `## Loop-Evidence` (WO/finding + tested); production-code PRs must pair
  with tests — `pr-loop-gate` workflow binds ALL agents equally.
- **`awiki` pip package** (`pip install git+…`): thin launcher CLI
  (status/search/adopt/skill/doctor/guide).
- **Repo Health 100%**: wiki-health 0 hard/0 baselined (root-cause fixes:
  link resolution for skills/files, code-span examples, truncation), CI
  green streak restored via deterministic generated context.

### Changed
- Skill tiers consolidated: 198 canonical (12 manual buttons) / 47
  deprecated-with-successors; routing now 3-tier (trigger → description →
  default spine `/A`).
- `/A <objective>` is THE single entry (question-guard, default spine).

## 1.3.0 - 2026-06-12

### Added

- Strategic A-Wiki capability lanes for Design/Web, high-end lightweight games, revenue engine, and premium auto trading.
- Capability upgrade roadmap with graph hygiene loop, MCP/plugin allowlist, and recurring update cadence.
- Four wiki hub pages that connect the new lanes to existing skills, protocols, game docs, Creator Layer, and trading safety rules.

### Changed

- `scripts/wiki/build-capability-map.py` now emits strategic lanes, an upgrade matrix, graph hygiene baseline, and MCP allowlist in the generated capability map.
- `scripts/check-privacy.py` skips vendored `skills/anthropic-skills/` license/example files so the privacy gate stays focused on repo-owned public-safe content.

### Verification

- `python3 -m pytest tests/test_build_capability_map.py -q`
- `python3 -m pytest tests/test_check_privacy.py -q`
- `python3 scripts/gen-index.py --check`
- `python3 scripts/verify-awiki-ready.py`
- `python3 scripts/check-privacy.py`

## 1.2.0 - 2026-05-30

### Added

- P0: GitHub Actions CI for fast repo verification on every push to `main`.
- P1: Cross-platform smoke workflow for Ubuntu, macOS, and Windows using fake external data.
- P2: Weekly/manual model roster scout that reports OpenRouter free-model changes without auto-committing.
- P3: Onboarding documentation for GitHub Actions, external data setup, and model roster review.
- P4: `VERSION`, this changelog, and upstream refresh runbook for capability tracking.
- P5: Weekly wiki health digest workflow that emits an audit artifact instead of mutating repo state.

### Changed

- `scripts/update-model-roster.sh` can now run in CI-safe degraded mode when `OPENROUTER_API_KEY` is missing.
- New-machine onboarding documents which GitHub Secrets are optional and how each workflow behaves without real private data.

### Verification

- Local privacy scan: `python3 scripts/check-privacy.py`
- Local tests: `python3 -m pytest -q`
- GitHub: `A-Wiki CI`, `A-Wiki Cross-Platform Smoke`, `A-Wiki Model Roster Refresh`

## 1.1.0 - 2026-05-30

### Added

- Universal `AGENTS.md` brain with Iron Laws, Cost Pyramid, Swarm protocol, and external data policy.
- External `drive/` data layer for heavy/raw/private files and secrets.
- Cross-platform setup scripts for local links, hooks, wiki index, and model router cache.
