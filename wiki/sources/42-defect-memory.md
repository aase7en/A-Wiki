---
type: source
title: "42 — DEFECT MEMORY / REGRESSION PREVENTION"
slug: 42-defect-memory
date_ingested: 2026-09-10
original_file: raw/Skill template/graph-engineering-project-template/42-DEFECT-MEMORY.md
tags: []
---

# 42 — DEFECT MEMORY / REGRESSION PREVENTION

## Activate when

A material defect, recurring failure, incident, or important debugging lesson is discovered.

---

# 1. Core question

For every meaningful defect ask:

> What should the system learn so this class of failure is harder to reintroduce?

Do not settle for:

> Remember not to do that again.

---

# 2. Prevention priority

Prefer, in order:

1. regression test,
2. deterministic/static checker,
3. type/schema constraint,
4. architectural invariant,
5. CI rule,
6. linter,
7. monitoring/alert,
8. durable documentation,
9. prose memory only when nothing stronger fits.

**Executable memory beats prose memory.**

---

# 3. Defect record

For material/recurring defects preserve:

- symptom,
- impact,
- trigger,
- root cause,
- missing invariant,
- fix,
- regression protection,
- affected area,
- evidence,
- future warning.

Do not preserve raw debugging noise as permanent knowledge.

---

# 4. Promote selectively

Working-state details belong in current work/handoff.

Durable defect knowledge belongs in defect records/architecture/testing rules only if it is reusable.

Do not pollute long-term memory with transient errors.

---

# 5. Close the loop

A bug is not fully learned from until the chosen prevention exists and is verified.

Examples:

`bug → regression test → test red before fix → repair → test green`

`unsafe pattern → static rule → scan catches pattern`

`operational failure → health signal/alert → verified detection`

Documentation alone is acceptable only when executable enforcement is not practical.
