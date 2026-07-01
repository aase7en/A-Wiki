# Skill Consolidation Protocol

> **Status:** Active (Chunk 2 of the Universal Skill Architecture)
> **Applies to:** all A-Wiki agents editing skills or the registry
> **Enforced by:** `scripts/skills_registry/consolidate.py` + `validate_registry()`

This protocol defines how A-Wiki collapses duplicate/near-duplicate skills while
preserving all distinct functionality. It implements the **Moderate** dedup level
approved in the architecture plan: collapse true duplicates, alias near-duplicates,
never destroy distinct skills.

---

## Skill statuses (the 3 valid values)

| Status | Meaning | Required fields | When to use |
|--------|---------|-----------------|-------------|
| `canonical` | The primary implementation of a skill | `name`, `path` | The "keeper" — what agents should load |
| `alias` | A thin entrypoint that re-routes to a canonical | `name`, `canonical` | Same-purpose skill under a different name/path; keeps working via redirect |
| `deprecated` | Do not use; routes to a successor | `name`, `migrated_to` | Superseded skill; kept for reference but agents are warned |

---

## Consolidation actions (Chunk 2 applied)

### 1. TRUE DUPLICATE → `mirror_paths`
When a skill exists in multiple paths with identical or near-identical content, the
canonical copy keeps its `status: canonical` and gains a `mirror_paths: [...]` field
listing the duplicate locations. Mirrors are NOT deleted (Iron Law safety) — they
are recorded so a later cleanup can remove them after verifying no runtime breaks.

**Example:** `skill-creator` exists at `skills/anthropic-skills/` (canonical, 485
lines), `skills/claude-code/` (Manus fork, 236 lines), and `skills/delegation/`
(identical Manus fork). The registry keeps `skill-creator` canonical at
`skills/anthropic-skills/skill-creator` with `mirror_paths: [skills/claude-code/skill-creator, skills/delegation/skill-creator]`.

### 2. THIN STUB → `status: alias`
A skill that exists only to re-route to a richer canonical implementation. The stub
keeps its own `name` and `path` but gains `status: alias` + `canonical: <name>`.

**Examples:**
- `hipaa-compliance` → alias of `healthcare-phi-compliance`
- `token-budget-advisor` → alias of `context-budget`

### 3. DEPRECATED → `status: deprecated`
A skill superseded by another. Gains `status: deprecated` + `migrated_to: <name>`.
Agents invoking a deprecated skill are warned and routed to the successor.

**Example:** `root-cause-first` → deprecated, `migrated_to: debug-mantra`

### 4. NEAR-DUPLICATE → `status: alias` (keep content)
Skills with the same purpose and near-identical structure but different
frameworks/contexts. The canonical is chosen by breadth of use; others become
aliases that still point agents to the canonical workflow. **Content is preserved** —
these are distinct enough to keep, but aliasing prevents confusion about which to use.

**Example:** `laravel-verification`, `quarkus-verification`, `springboot-verification`
→ all alias to `django-verification` (the reference implementation of the 5-phase
verification workflow).

---

## What we explicitly do NOT consolidate

These were audited and confirmed **distinct** — they share a theme but serve
different functions. Leave them alone.

- **8 language-testing skills:** `python-testing`, `golang-testing`, `rust-testing`,
  `kotlin-testing`, `perl-testing`, `cpp-testing`, `csharp-testing`, `fsharp-testing`
  — each is language-idiomatic (pytest, GoogleTest, xUnit, etc.)
- **12 Thai skills:** each owns one domain (postal, date format, ID validation, etc.)
- **6 trading-security micro-skills:** each prevents a specific distinct bug
- **Framework patterns** (`django-patterns`, `laravel-patterns`, etc.): distinct stacks

---

## How to add a consolidation action

1. Confirm the duplicate via `scripts/skills_registry/dedup.py` (description similarity)
   or manual audit.
2. Add an entry to `CONSOLIDATION_ACTIONS` in `scripts/skills_registry/consolidate.py`.
3. Run `python scripts/skills_registry/consolidate.py skills-registry.json`.
4. Verify: `python scripts/regen-skill-surfaces.py --validate` and `--check`.
5. Commit with `chunk(dedup): <what> [next: ...]`.

The consolidation script is **idempotent** — safe to run multiple times.
