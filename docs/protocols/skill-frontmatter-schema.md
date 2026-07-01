# SKILL.md Frontmatter Schema

> **Status:** Active (Chunk 3 of the Universal Skill Architecture)
> **Enforced by:** `scripts/hooks/check_skill_registry.py` (warnings, not blocks, for legacy)
> **Registry:** `skills-registry.json` is the single source of truth

Every `SKILL.md` file in A-Wiki starts with a YAML frontmatter block delimited by
`---`. This document defines the schema. The registry scanner
(`scripts/skills_registry/scan.py`) parses this without PyYAML (manual regex), so
keep the frontmatter simple: scalars and inline lists only.

---

## Required fields

| Field | Type | Example | Notes |
|-------|------|---------|-------|
| `name` | string | `debug-mantra` | Must match the skill directory name. Unique across the whole registry. |
| `description` | string | `Four-mantra debugging discipline.` | What the skill does + when to use it. Agents use this to auto-invoke. |

## Registry fields (recommended; enforced via `check_skill_registry.py` warning)

| Field | Type | Example | Notes |
|-------|------|---------|-------|
| `domain` | list | `[code, debug]` | One or more from VALID_DOMAINS. Multi-domain is fine. See taxonomy below. |
| `lifecycle_phase` | string | `build` | One of: define, plan, build, verify, review, ship, meta, none. Non-lifecycle skills use `none`. |
| `aliases` | list | `[root-cause-first]` | Other names/paths that resolve to this skill. |
| `status` | string | `canonical` | One of: `canonical`, `alias`, `deprecated`. Default is `canonical`. |
| `canonical` | string | `debug-mantra` | Required if `status: alias` — names the canonical skill this re-routes to. |
| `migrated_to` | string | `debug-mantra` | Required if `status: deprecated` — names the successor. |

## Optional fields

| Field | Type | Example |
|-------|------|---------|
| `category` | string | `engineering` |
| `version` | string | `1.0.0` |
| `license` | string | `MIT` |
| `tools` | list | `[Read, Bash]` |
| `origin` | string | `ECC` |

---

## Domain taxonomy (22 domains)

```
code | debug | design | ux-ui | trader | medical | business | data | engineering |
security | ai-ops | productivity | wiki | iot | env | pharmacy | thai |
logistics | network | media | document | sre
```

These live in `scripts/skills_registry/__init__.py` (`VALID_DOMAINS`). Adding a
new domain = add it there + re-run `regen-skill-surfaces.py`.

## Lifecycle phases

| Phase | When |
|-------|------|
| `define` | Requirements, acceptance criteria before code |
| `plan` | Decompose into verifiable tasks |
| `build` | Implementation, TDD, context engineering |
| `verify` | Testing, debugging, runtime verification |
| `review` | Code review, security, performance, simplification |
| `ship` | Git, CI/CD, docs, ADRs, observability, launch |
| `meta` | Routers, gates, orchestration (awiki-lifecycle-router) |
| `none` | Domain skills outside the engineering lifecycle (default) |

---

## Minimal example

```markdown
---
name: my-skill
description: Does X for purpose Y. Use when Z.
domain: [code]
lifecycle_phase: build
---

# My Skill

Body content...
```

## Alias example

```markdown
---
name: hipaa-compliance
description: Healthcare PHI compliance. See healthcare-phi-compliance.
status: alias
canonical: healthcare-phi-compliance
domain: [medical, security]
lifecycle_phase: review
---

This skill is a thin entrypoint. Start with `healthcare-phi-compliance`.
```

## Deprecated example

```markdown
---
name: root-cause-first
description: Superseded by debug-mantra.
status: deprecated
migrated_to: debug-mantra
domain: [code, debug]
lifecycle_phase: build
---

Use `debug-mantra` instead.
```

---

## How the hook enforces this

`scripts/hooks/check_skill_registry.py` runs on every Edit/Write/MultiEdit to a
`SKILL.md` file:

1. **Block (exit 2)** if the skill name is not in `skills-registry.json` — register first.
2. **Warn** if `domain` or `lifecycle_phase` is missing from frontmatter (grandfathered — legacy skills pass).
3. **Warn** if the skill is `status: deprecated` (suggest the successor).

Override (emergency): `HOOK_SKIP=check_skill_registry`.

---

## Creating a new skill (ordered checklist — CLICK-PATH-001)

**Order matters.** The hook blocks a Write/Edit to `SKILL.md` whose name is not
yet in the registry, so you MUST register BEFORE authoring the file:

1. **Add a registry entry** to `skills-registry.json` with the new skill's
   `name`, `domain`, `lifecycle_phase`, `category`, `source` (`repo`),
   `path`, `agents` (`["all"]`), and `status` (`canonical`). (Running
   `python scripts/regen-skill-surfaces.py --bootstrap --out draft.json`
   can scaffold a draft entry to copy in.)
2. **Regenerate surfaces** so the generated tables/paths include the new skill:
   `python scripts/regen-skill-surfaces.py`
3. **NOW author the `SKILL.md`** at the declared `path`. The hook will pass
   because the name is already registered.
4. **Verify** `python scripts/regen-skill-surfaces.py --check` is green (it
   should be — step 2 already synced surfaces), then commit.

If you author `SKILL.md` first (before step 1), the hook blocks the Write with
exit 2 and the registry-first order. To unblock: do step 1, then re-attempt.

---

## After editing an existing skill

Editing an already-registered `SKILL.md` (e.g. fixing a typo, adding a section)
needs no special order — the hook passes because the name is already in the
registry. Just remember to re-run `python scripts/regen-skill-surfaces.py` if
the edit changes the skill's `domain`/`lifecycle_phase`/`name` (frontmatter
changes flow into generated surfaces), then commit.
