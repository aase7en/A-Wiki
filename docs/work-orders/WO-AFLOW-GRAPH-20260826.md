# WO-AFLOW-GRAPH-20260826: A-Flow Graph Engineering Upgrade
Status: claimed(SunDay-Worker-4)
Lane/files: `skills/awiki/a-flow/**`, `scripts/lib/a_flow_state.py`, `scripts/hooks/check_a_flow_discipline.py`, `tests/test_check_a_flow_discipline.py`, `tests/test_a_flow_graph.py`, `skills-registry.json`
Branch: `feat/a-flow-graph-engineering`
Model tier: primary-only

## Goal + Acceptance criteria
- Evolve the existing native `a-flow` instead of creating a parallel mega-prompt/pipeline.
- Preserve the 7-phase A-Suite compatibility spine for existing callers while adding a finer SSoT-first graph workflow.
- Represent the current engineering main flow semantically as `grill-with-docs -> spec -> tickets -> implement -> code-review`, with conditional shaping before it and production-assurance/release nodes after it.
- Make pre-implementation graph nodes hard-block significant repository mutation when A-Flow graph state is active.
- Add durable graph/runtime documentation using progressive disclosure; do not require all workflow docs to load every session.
- Reduce runtime duplication by composing canonical leaf skills directly instead of stacking A-Flow -> A-Plan -> grill/spec/plan again.
- Audit overlapping/deprecated engineering skills; only remove/deprecate when actual references/usage evidence makes it safe. Do not delete merely because names overlap.
- Preserve SSoT/claim/work-order/continuity rules and dirty-main safety.

## Reference pattern
- Existing router/state: `skills/awiki/a-flow/SKILL.md`, `scripts/lib/a_flow_state.py`, `scripts/hooks/check_a_flow_discipline.py`.
- A-Wiki governance: `AGENTS.md`, `docs/protocols/brain-improvement-gate.md`, `skills/awiki/a-claim/SKILL.md`.
- Current upstream flow (verified 2026-08-26): AIHero / mattpocock main flow = `grill-with-docs -> to-spec -> to-tickets -> implement -> code-review`; A-Wiki maps semantic stages to its canonical local skills rather than blindly installing duplicates.

## Steps
1. Inventory current A-Wiki flow/review/debug/release/continuity capabilities and overlap.
2. Define backward-compatible graph nodes + phase mapping and failure-loop edges.
3. Add failing tests for graph-state mutation gate and valid transitions.
4. Implement graph-state support without breaking the 7-phase compatibility APIs.
5. Rewrite `a-flow` as the native graph router with progressive-disclosure references.
6. Update registry metadata/version only after skill changes exist.
7. Audit redundant/deprecated workflow skills and make only evidence-backed cleanup changes.
8. Run targeted tests, registry/skill checks, privacy check, preflight and diff review.
9. Commit, push, open PR, inspect remote diff/CI; re-audit before merge if tooling/permissions allow.

## Forbidden
- Do not edit the dirty original `A-Wiki` main worktree; use the isolated claimed worktree for this WO.
- Do not change the public 7-phase `A_PHASE_CHAIN` semantics in this slice; existing category packs/MCP tests depend on it.
- Do not create another top-level workflow framework or duplicate `a-flow` under a new name.
- Do not physically delete canonical skills without usage/reference evidence and a migration path.
- Do not modify `AGENTS.md`, `COLLAB.md`, raw/private/drive data, or unrelated generated wiki files.
- Do not weaken tests/checks to make the change green.

## Verify commands
- `python -m pytest tests/test_check_a_flow_discipline.py tests/test_a_flow_graph.py -q`
- `python -m pytest tests/test_a_focus_mcp.py tests/test_skills_registry.py -q`
- `python scripts/regen-skill-surfaces.py --check`
- `python scripts/verify-skill-surfaces.py`
- `python scripts/skill-quality-report.py --fail-on-warn`
- `python scripts/check-privacy.py`
- `python scripts/agent-preflight.py`
- `git diff --check`

## Checkpoint log (append-only)
- [2026-08-26] SunDay-Worker-4: identity/preflight complete. Original main is dirty and was behind origin; created an isolated worktree from `origin/main` at `60ddd5ca`, branch `feat/a-flow-graph-engineering`. Local claim acquired. Current gap: A-Flow has 7 broad stages but lacks explicit SSoT/repo-gate/spec-ticket/deep-assurance/release/post-merge graph nodes. Upstream main flow verified current before design.
