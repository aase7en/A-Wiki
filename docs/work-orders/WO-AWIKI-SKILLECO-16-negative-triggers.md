# WO-AWIKI-SKILLECO-16 — negative_triggers routing veto (canonical registry)

- Date: 2026-11-17
- Agent: GLM (Kilo)
- Branch: `feat/negative-triggers`
- Status: OPEN
- Parent issue: #76 follow-up: "negative-condition metadata via canonical registry
  after #60 ownership reconciliation" (#60 verified closed → lane open).

## Problem

The auto-pick router scores positive triggers only. Issue #76 explicitly demands
the opposite direction too: "no automatic deprecated picks", "Required security
evidence is never compacted away", "no automatic grill for simple prompts". Today
those guardrails live only in prose (skill bodies / AGENTS.md), not in routing data —
the router cannot express "NOT for this input".

## Design

New OPTIONAL registry field `negative_triggers: list[str]` (max 4, same
normalize/boundary matching rules as `triggers`):

- Semantics: if ANY negative trigger matches the objective text, the skill is
  VETOED for that routing call regardless of positive score (score → dropped).
  Deterministic, explainable, cheaper than weighted penalties.
- Backward compatible: absent field = no veto. Non-canonical entries ignored as today.
- Validation (registry schema): list of non-empty strings, ≤4 entries, unique,
  rejected on deprecated entries; enforced wherever triggers are validated.
- Seed data (misuse-risk anchors named by #76):
  - `caveman`: "security evidence", "secret", "ci log", "diff"
  - `token-optimization`: "security evidence", "secret", "ci log", "diff"
  (Both skills' bodies already promise never to compact these; the router now
  enforces the same promise structurally.)

## Non-goals

- No A-ROUTER.md surface change (routing-internal metadata; revisit if #76 asks).
- No per-harness wiring changes (separate follow-up lane).
- No weighted-penalty scoring (veto only — simpler contract, easier to test).

## Changes

1. `scripts/skills_registry/routing.py` — veto in `route()`.
2. `skills-registry.json` — schema + 2 seed entries.
3. Validation wherever triggers are validated (`scripts/skills_registry/__init__.py`
   / hooks) — located during implementation.
4. `tests/test_skill_route_fallback.py` (or new focused test class) — RED-first:
   veto beats positive hit; absent field unchanged; validation rejects bad shapes.
5. COLLAB claim row (this WO). TOKNIT-15 DONE marker rides the NEXT slice's docs
   commit (this WO's docs commit carries only its own claim row to keep the branch
   rebased on main `ea7cd3f1` which already landed SKILLECO-14's marker).

## Tests

- RED: veto test fails on current routing (no veto → skill routed despite negative).
- GREEN: routing tests + `tests/test_skill_tiers.py` + `verify-skill-surfaces.py`
  + `check-privacy.py`.

## Review

GLM subagent independent review, anchored `VERDICT` line.

## Evidence

- Filled at close.
