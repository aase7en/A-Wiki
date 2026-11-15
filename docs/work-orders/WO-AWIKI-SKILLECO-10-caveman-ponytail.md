# WO-AWIKI-SKILLECO-10 — register caveman + ponytail; extend token-optimization triggers

Branch: feat/skill-eco-auto-on-demand · Agent: GLM (Kilo) · Opened: 2026-11-15
Base: 6b200b03 · Parent issue: #76 (SKILL-ECO AUTO_ON_DEMAND tier, slice 2
after WO-AWIKI-76-01) · Inventory comment: issuecomment-6892939374

## What

Implements the WRAP+EXTEND items from the #76 inventory shortlist:

1. skills/awiki/caveman/SKILL.md — ADAPTED output-style skill (original
   concept from community caveman skills; style guidance ONLY, no upstream
   proxy/runtime/telemetry imported — per #76's external-skill warnings)
2. skills/awiki/ponytail/SKILL.md — ADAPTED minimal-solution + scoped
   prior-context checkpointing discipline
3. token-optimization triggers +5 (compact logs / compress diff / shrink
   search output / lossless reference / reduce context) — registry field
   only, no file edit
4. commands/Caveman.md + commands/Ponytail.md
5. Tests: TestSkillEco10 (registration contract: canonical/auto/routable;
   token-optimization compact triggers present)

Tier policy: both non-user-specific → invocation auto (manual tier stays
user-specific-only). Trigger cap 8 enforced (ponytail trimmed from 10).
Hard exclusions preserved: caveman never touches code/security/test
evidence; ponytail never weakens safety gates.

## Checkpoints
- [x] Claim row WO-AWIKI-SKILLECO-10 (RECONCILED)
- [x] Local gates: 285 passed; regen --check no drift; privacy clean

## Review round 1 — GLM BLOCK → repairs (2026-11-15)

P1 verify-skill-surfaces 3c failed (first non-a-suite triggered canonical
skills — A-ROUTER generator couldn't render them → "unreachable" dead data)
→ gen_a_router gained _auto_on_demand + §3 section (deterministic, regen-
owned); verify now passes, triggers live for hookless agents. P3 YAGTI→
YAGNI registry typo fixed; test pinning completed (all 5 compact triggers
+ ≤8 cap assertion). P3/INFO acknowledged (claim wording caveat recorded
here: A-ROUTER/kilo-paths were no-ops by generator design pre-fix).

Evidence: 287 passed; verify no drift/orphans; A-ROUTER carries §3.
