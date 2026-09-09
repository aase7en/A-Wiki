---
type: source
title: "80 — UPSTREAM REFERENCES / FRESHNESS POLICY"
slug: 80-upstream-references
date_ingested: 2026-09-10
original_file: raw/Skill template/graph-engineering-project-template/80-UPSTREAM-REFERENCES.md
tags: []
---

# 80 — UPSTREAM REFERENCES / FRESHNESS POLICY

## Reference status

This template incorporates methodology inspired by the AIHero / mattpocock engineering skills ecosystem, but the project's own SSoT and safety rules remain authoritative.

Last template review: **2026-08-26**

---

# 1. Current main flow verified at template creation

The current main build chain was verified as:

`grill-with-docs → to-spec → to-tickets → implement → code-review`

Primary references:

- https://www.aihero.dev/skills
- https://www.aihero.dev/skills-grill-with-docs
- https://github.com/mattpocock/skills
- https://github.com/mattpocock/skills/blob/main/docs/engineering/to-spec.md
- https://github.com/mattpocock/skills/blob/main/docs/engineering/to-tickets.md
- https://github.com/mattpocock/skills/blob/main/docs/engineering/implement.md
- https://github.com/mattpocock/skills/blob/main/docs/engineering/code-review.md

Shaping references:

- Wayfinder
- Research
- Prototype

Catalog:
- https://www.aihero.dev/skills-catalog
- https://www.aihero.dev/skills-wayfinder

---

# 2. Upstream freshness rule

External skills evolve.

Before depending on exact current behavior, installation commands, file formats, or orchestration details:

1. check current upstream docs/source,
2. compare with this template/local installed edition,
3. identify material change,
4. adopt/adapt/reject intentionally,
5. record important project deviation.

Do not rewrite project governance merely because upstream changed.

---

# 3. Stable conceptual ideas currently used

At creation time the template intentionally preserves these ideas:

- `grill-with-docs` aligns decisions/vocabulary before spec,
- `to-spec` synthesizes agreed understanding rather than re-interviewing,
- `to-tickets` prefers tracer-bullet vertical slices with blockers,
- wide refactors may use expand-contract,
- `implement` executes settled work at pre-agreed seams and uses test-driven verification,
- `code-review` keeps Standards and Spec as separate axes,
- Wayfinder maps large unresolved decision spaces,
- Research answers external factual blockers,
- Prototype answers design questions experimentally.

---

# 4. Project-specific strengthening

This template deliberately strengthens generic upstream workflows by requiring:

- no critical implementation decision to live only in chat,
- actual-state verification after important skill execution,
- bounded delegation,
- SSoT checkpoints,
- deep E2E and production assurance when risk warrants it,
- defect memory/regression prevention,
- PR remote-diff audit,
- CI failure classification,
- post-CI re-audit,
- post-merge verification,
- context/session rotation protocol.

These are project governance rules, not claims that upstream tools provide them automatically.
