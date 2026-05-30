# Changelog

All notable A-Wiki changes are tracked here so every clone, device, and AI
agent can tell what capability level the repository is at.

Format: keep the newest release first. Use small, operational entries that
explain what changed and how to verify it.

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
