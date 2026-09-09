---
type: source
title: "21 — SHAPING / WAYFINDING / RESEARCH / PROTOTYPE"
slug: 21-shaping-research
date_ingested: 2026-09-10
original_file: raw/Skill template/graph-engineering-project-template/21-SHAPING-RESEARCH.md
tags: []
---

# 21 — SHAPING / WAYFINDING / RESEARCH / PROTOTYPE

## Activate when

- requirements are unclear,
- architecture is foggy,
- effort is too large for one session,
- external facts block a decision,
- talking cannot resolve a design question,
- brainstorming is explicitly useful.

Shaping is optional. It exists to reduce uncertainty before the main build flow.

---

# 1. Brainstorming

Brainstorm alternatives before committing when there is meaningful design space.

Useful outputs:

- plausible approaches,
- trade-offs,
- risks,
- reversibility,
- constraints,
- unknowns,
- recommendation.

Do not confuse brainstorming with an approved decision.

If subagents are supported, use them only for bounded independent exploration.

Parent/lead owns synthesis.

---

# 2. Wayfinder

Use for efforts too large for one agent session where the destination is known but the route is unclear.

Wayfinder maps **decision work**, not implementation work.

Decision-ticket types may include:

- grilling/HITL decision,
- prototype/HITL experiential question,
- research/AFK factual question,
- task/manual prerequisite.

Resolved decision areas feed into the normal main flow.

Do not let wayfinding silently become implementation.

---

# 3. Research

Use research when a decision is blocked by external facts.

Prefer:

1. source code,
2. official specification,
3. first-party API docs,
4. official vendor docs,
5. authoritative standards,
6. primary research,
7. high-quality secondary sources when necessary.

Label outputs distinctly:

- `FACT`
- `INFERENCE`
- `RECOMMENDATION`
- `DECISION`

External research informs project decisions; it does not replace project authority.

Preserve durable evidence when the result matters beyond the current turn.

---

# 4. Bounded research delegation

One research worker should have:

- one bounded question,
- allowed/preferred sources,
- expected output,
- stopping condition,
- no uncontrolled nested delegation,
- no duplicate parallel assignment.

Avoid recursive trees:

`Agent → research agent → research agent → research agent`

Prefer:

```text
Lead
├─ Research A
├─ Research B
└─ Research C
    ↓
Lead synthesizes
```

---

# 5. Prototype

Use a prototype to answer a concrete unresolved design question.

Typical forms:

- logic prototype,
- UI/interaction prototype.

Prototype code is exploratory.

Unless explicitly promoted through the normal flow:

- do not treat it as production,
- do not harden it unnecessarily,
- do not quietly merge it,
- do not let prototype architecture become accidental policy.

Durable prototype output should emphasize:

- question,
- experiment,
- evidence,
- conclusion,
- design consequence.

---

# 6. Shaping exit gate

Shaping ends when the current decision frontier is sufficiently resolved to enter the main flow.

Exit with:

- settled facts,
- explicit decisions,
- remaining assumptions,
- constraints,
- recommended next stage.

If major uncertainty remains, continue shaping rather than hiding it inside implementation.
