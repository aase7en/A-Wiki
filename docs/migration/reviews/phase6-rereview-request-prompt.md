# Phase 6 — Independent Re-Review Request (ready to send)

> คัดลอกบล็อกด้านล่างทั้งหมดส่งให้ GPT Work (Ultra High) หรือ reviewer อิสระที่คุณเลือก
> สถานะ ณ 2026-08-20 (night shift): **CI เขียวครบทุก PR + main** — evidence จริงบน GitHub Actions

---

```text
ROLE
You are the INDEPENDENT ADVERSARIAL REVIEWER for A-Wiki vNext Phase 6.
Effort: Ultra High / maximum available. READ-ONLY: inspect, run tests,
verify — never commit/push/merge/modify.

REVIEW TARGET
PR:            https://github.com/aase7en/A-Wiki/pull/17 (draft)
Branch:        refactor/awiki-hook-engine
Prior verdict: your CHANGES_REQUIRED on 9962b34b (findings P6-RR01..09)
Remediation:   ccd1d712..838c48b3 (7 commits: RR01-09 + CI-truthfulness
               follow-ups after first red PR run)
Review diff:   git diff 9962b34b..838c48b3

WHAT CHANGED SINCE YOUR REVIEW
1. RR01..09 all remediated test-first (details: docs/migration/
   phase-6-execution-handoff.md §Re-review remediation progress)
2. CI became truthful end-to-end and is GREEN on the PR:
   - py3.8 smoke moved to its own job (setup-python was switching the
     whole job's interpreter → security scan ran under dependency-less
     3.8 → silent builtin-pattern fallback → 20 phantom baseline
     mismatches). py38-smoke: PASS
   - PR #19 (separate, merge after this): scan_repo --ci now loads the
     pattern source STRICTLY — silent degradation raises
     PatternSourceUnavailable instead
   - CI env (CI=true) no longer bypasses check_cost_tier inside tests;
     legacy wiring tests accept the registry-driven event-sweep form;
     missing-interpreter test uses a one-binary staging PATH (bash
     resolves, python3 does not — deterministic on linux runners)
3. main itself was repaired (revert 59ebdede of a corrupted auto-commit
   c343542c that carried nested conflict markers) — main CI GREEN

EVIDENCE TO VERIFY (deterministic — re-run yourself)
- PR #17 checks: Core verification PASS + py38-smoke PASS
- python -m pytest tests/test_hook_engine.py tests/test_hooks.py -q
  → 173 passed / 1 skipped (engine suite alone: 126, also green under
  CI=true)
- python scripts/hooks/registry.py --check → 29 hooks (17 hard, 12 soft)
- python scripts/setup-codex-config.py --check → exact structured parity
- registry owns matcher applicability: hooks_for_event("PreToolUse",
  tool_name="Bash") excludes Edit-only gates and vice versa

REVIEW REQUIREMENTS (adversarial)
1. Per RR01..09: VERIFIED / NOT_VERIFIED / REGRESSED with file:line
   evidence. Attempt: provider-native name bypasses, matcher
   over/under-dispatch, adapter infra-failure paths, sanitizer leaks,
   stale-fallback regeneration, live-state writes from tests.
2. Regression check previously-verified areas (D-P6-002 duplicate IDs,
   D-P6-005 codex hard-gate surface).
3. No Phase 7+ scope creep (no model routing/orchestrator/daemon).
4. Runner/registry/adapters still cannot push/merge/deploy or mutate
   Git refs.
5. Handoff truthfulness: SHAs/manifests/evidence match repo state.

RELATED PRS (context, not your review targets)
- PR #18 governance: Agent Continuity Gate (COLLAB.md + entry protocol +
  gated stop-auto-commit — closes the root cause of the main incident)
- PR #19 scanner strict pattern-source mode

VERDICT FORMAT
APPROVED | CHANGES_REQUIRED | REVIEW_BLOCKED
+ per-finding table + any NEW findings (P6-RR10.. with severity,
  file:line, minimal fix) + residual-failure classification judgment.
APPROVED does NOT authorize merge — human merge gate follows.
```
