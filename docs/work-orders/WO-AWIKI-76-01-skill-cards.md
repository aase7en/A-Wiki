# WO-AWIKI-76-01 — Compact Skill Cards (Issue #76)

Status: CLAIMED / IMPLEMENTATION_PENDING
Authority: A-Wiki existing skills-registry.json v3 and routing.py; Issue https://github.com/aase7en/A-Wiki/issues/76
Task: READ-ONLY additive skill-discovery utility (R1); no skill execution, no new router, no auto-hook.
Claim: bf72429aeb23 | Agent: ChatGPT A-Conductor
Branch: feat/76-compact-skill-cards
Base: origin/main@79f793788bc807e66d8e31f2e390c7d6475c8784
Worktree: A:/GitHub/_worktrees/A-Wiki-issue76-skill-cards

## Goal

Offer a small, plain-language agent-visible summary of existing canonical skills,
optionally ranked by the already accepted `routing.route` function,
before loading any complete `SKILL.md` body.

## Allowed scope

- NEW `scripts/skills_registry/skill_cards.py` — pure projection over accepted registry.
- NEW `scripts/skill-cards.py` — read-only CLI entry point.
- NEW `tests/test_skill_cards.py` — deterministic isolated tests.
- THIS Work Order and the one automatic claim row in `COLLAB.md` only.

Forbidden: editing `skills-registry.json`, generated skill surfaces, global settings,
hooks, router, other owners' worktrees or active execution, installing externals.

## Acceptance / test plan

1. Canonical-only; no deprecated skills; max 1–3 ranked cards in query mode.
2. Use `routing.route` rather than implementing another matcher; output useful description,
   positive triggers, `do_not_use` guardrail, invocation hint and source pointer.
3. Safe no-match output, explicit uncertainty, valid JSON, bounded long descriptions.
4. A catalog view may show a small core list without eager-loading all skill bodies.
5. CLI/tool never performs skill, subprocess actions or mutation except reading registry.
6. RED-first tests, focused + related checks, privacy/secret checks, independent review and CI.
7. Compare actual source/body bytes before claiming token improvements. No invented savings.

## Continuity

Do not reinitialize existing `AGENTS.md` or `/init`. Claim and work order are committed
and pushed before source mutation. After verification, freeze exact candidate SHA and
request review/CI. Update Issue #76 with truthful evidence. No merge without gates.
