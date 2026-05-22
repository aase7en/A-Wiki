# Skill Quality Standard

> มาตรฐานสำหรับการเขียนและดูแล AI Agent Skills ใน A-Wiki

## Required Frontmatter

Every `SKILL.md` MUST have:

```yaml
---
name: <kebab-case-name>
description: <one-line description in English or Thai>
status: <stable | beta | draft>
---
```

Optional:
- `migrated_from`: source repo (e.g., `InW-Wiki`, `9arm-skills`)
- `triggers`: list of trigger phrases
- `tags`: list of keywords

## Structure Requirements

A well-written `SKILL.md` should include:

1. **Name + Description** (from frontmatter)
2. **When to invoke** — explicit trigger phrases
3. **When NOT to use** — guard rails
4. **Required inputs** — what must be present before the skill fires
5. **Workflow** — numbered steps, applied in order
6. **Output flow** — what the skill produces and how
7. **Rules** — operating constraints (must/must-not)
8. **Examples** (optional) — worked example demonstrating the skill

## Review Checklist

Before marking a skill `stable`, verify:

- [ ] Frontmatter has all required fields
- [ ] No hardcoded secrets, paths, or personal data
- [ ] All internal references point to valid paths
- [ ] Trigger phrases are explicit (not vague)
- [ ] Guard rails exist for when NOT to use
- [ ] Workflow steps are ordered and actionable
- [ ] Output format is specified
- [ ] Rules are concrete (not "be careful")

## Category Definitions

| Category | Purpose |
|----------|---------|
| `engineering/` | Daily code work — debugging, review, documentation |
| `productivity/` | Non-code workflow — management, spreadsheets |
| `wiki/` | Wiki management — ingest, lint, search, export |
| `automation/` | Repetitive task automation — hooks, optimization |
| `research/` | Information gathering — web, synthesis, planning |
| `domain/` | Domain-specific — pharmacy, IoT, etc. |
| `delegation/` | Cross-agent coordination |
| `deprecated/` | Skills no longer in use (keep for reference) |
| `in-progress/` | Drafts not yet ready to ship |