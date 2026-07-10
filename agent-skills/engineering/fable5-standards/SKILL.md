---
name: fable5-standards
description: Deeper reasoning standards for architecture decisions, debugging, data migrations, and other non-trivial technical work — problem decomposition, trade-off comparison, root-cause debugging, and playbooks for planning vs implementing vs analyzing vs writing. Use whenever a task involves multi-step planning, schema or data migration, security-sensitive design, or choosing between competing approaches. Skip for simple one-step lookups or edits.
domain: engineering
lifecycle_phase: ship
---

# Fable5 reasoning standards

Companion to the always-on rules in CLAUDE.md (epistemic honesty, communication style). This carries the procedural, situational half: how to work through non-trivial technical tasks. Loads only when invoked or when this description matches — keep it that way, don't duplicate this into CLAUDE.md.

## Reasoning loop

Run this before answering non-trivial requests; write it out for genuinely complex ones.

1. **Restate the real problem.** What's actually being asked, and is the premise sound? Fix a wrong question before answering it.
2. **Constraints & success criteria.** Budget, time, skill level, environment, what "done" looks like.
3. **Decompose** into sub-problems small enough to verify individually.
4. **Generate ≥2 approaches**, compare trade-offs (complexity, cost, failure modes, reversibility). Flag one-way doors (hard to reverse) vs two-way doors.
5. **Root cause, not symptom.** Gather facts → align with stakeholders → fix at the source.
6. **Pre-mortem.** "If this answer is wrong, why?" Check edge cases and the strongest counter-argument.
7. **Right-size the answer.** Simple question → short answer.

## Technical work

**Planning** — any multi-step technical task: propose a plan, wait for approval, then execute. Never silently run destructive or costly operations (DROP/DELETE, deploys, paid API calls).

**Code** — state assumptions as comments. Prefer boring, verifiable solutions over clever ones. Run or test what can be run; never call untested code "working" — say "untested; expected to work because X."

**Debugging** — read the actual error → reproduce → isolate → rank hypotheses → test the cheapest one first → fix the root cause → verify → explain in one paragraph.

**Data & migration**
- Idempotent migrations where possible, always paired with rollback notes and post-migration validation (row counts, checksums, spot checks).
- Two-phase imports: staging table → validate → promote. Never load straight into production tables.
- Thai health/government data: dates are frequently พ.ศ. (Buddhist Era = CE + 543). Never assume CE. Route conversions through a documented helper (e.g. `core.thai_be_to_date()`).

**Security & privacy**
- Patient-identifiable data never reaches external AI providers — a hard architecture boundary, not a preference, whenever health data is involved.
- Z.ai/GLM cloud APIs (ZCode) are subject to Chinese data-governance law — never route hospital/patient-adjacent work through them, even indirectly.
- Never echo or print credentials. An exposed secret is P0: flag immediately, rotate it.

## Match the task type

- **Architecture/design** — think longest here. Deliver an options table → recommendation → why → what would change the recommendation.
- **Implementation** — small, verified increments. After each: what was done, how it was verified, what's next.
- **Analysis/research** — sources with dates. Separate data from interpretation. State what's missing and how that limits the conclusion.
- **Writing/documents** — confirm audience + purpose → draft → self-critique against purpose → one revision → deliver.
