# A-Wiki vNext Migration — Discoveries Log

> Non-blocking problems found during migration work (Master Plan §"Repository Improvement Discoveries").
> Exception rule: security leak / data loss / repository corruption → stop and report immediately (DISC-001 invoked this rule; reported at Phase 0 gate).

## DISC-001

- **Severity:** HIGH (data-loss class; actual damage low — regenerable)
- **Area:** repo automation / git safety
- **Date:** 2026-08-17 15:29 +0700 (detected 15:40 during Phase 0)
- **Evidence:**
  - `git reflog`: `pull --rebase origin main (finish): returning to refs/heads/refactor/awiki-kernel-vnext` at `2026-08-17 15:29:49 +0700` — not initiated by the migration executor (pytest suite was running at that moment).
  - Branch base rewritten `156a104e` → `443fd51a` (24 local commits replayed onto origin/main `e532d2f0`).
  - Working tree before: 15 rabies-WIP paths (session-start git status). After: 12 paths remain (staged flags flattened to unstaged — consistent with autostash pop), **3 paths' modifications gone**: `scripts/skills_registry/generated/gemini.skills.json`, `scripts/skills_registry/generated/zcode.skills.manifest.json`, `scripts/skills_registry/generated/skills-index.md`.
  - All 5 stash entries predate 2026-08-17 (2026-07-19 → 2026-08-07) — the lost diffs are in none of them.
  - `git diff 156a104e HEAD -- <3 files>` = empty → the edits are in no commit either.
  - `.git/hooks`: only `pre-commit` + `post-merge` (relink shims) — pull did NOT come from git hooks. Source unidentified; prime suspect = another concurrent agent session's SessionStart auto-pull (documented incident class of 2026-07-27, Iron Law #11 corollary).
- **Impact:**
  - Lost working-tree edits to 3 **generated** surfaces — recoverable via `python scripts/regen-skill-surfaces.py` because the modified `skills-registry.json` (source of truth) survived in the working tree.
  - Migration branch base moved to latest origin/main without review (net effect desirable: 0 behind origin, but ungated).
  - Demonstrates in production the exact P0 the Master Plan targets (§4.1 ungated automation mutating repo state; §4.3 CI/automation not authoritative).
- **Suggested action:**
  1. Phase 1 must include: disable/neutralize SessionStart auto-pull (or gate it: never rebase with dirty tree without explicit approval; prefer `pull --ff-only` + warn).
  2. Owner of the rabies WIP session: commit your WIP on main (Iron Law #11 corollary "commit early"), regenerate the 3 surfaces if needed.
  3. Consider `rebase.autoStash = false` + branch protection posture on shared machines.
- **Recommended phase:** Phase 1 (Stabilize Automation)

## DISC-002

- **Severity:** MEDIUM (security-relevant)
- **Area:** security scanning
- **Evidence:** baseline test run — `tests/test_hook_python_resolver.py::test_scanner_actually_flags_a_planted_secret` FAILS: the Python resolver scanner does not flag a planted secret.
- **Impact:** Layer-1 defense gap; privacy/secret guard over-reliant on later layers.
- **Suggested action:** fold into Phase 2 security-scan refactor (`scripts/security/scan_repo.py`, Master Plan §9) with the failing test as the regression case.
- **Recommended phase:** Phase 2

## DISC-003

- **Severity:** LOW
- **Area:** CI truthfulness
- **Evidence:** `daily-maintenance.yml:20` — `python3 scripts/gen-index.py --check 2>/dev/null || echo "OK"` (fail-open); workflow reports success while the same check FAILS Cross-Platform Smoke (`wiki-capability-map.md` stale).
- **Impact:** false-green health signal (Master Plan §6).
- **Suggested action:** retire `daily-maintenance.yml` (Phase 1); real checks move to rewritten `wiki-health` (Phase 2).
- **Recommended phase:** Phase 1–2
