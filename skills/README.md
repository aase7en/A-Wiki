# Skills Catalog

> Single source of truth for all AI agent skills. Every skill has a YAML frontmatter with `name`, `description`, and `status`.

> **Canonical sources & discovery**
> - The categorized dirs below (`engineering/`, `wiki/`, `delegation/`, …) are the **canonical** content locations.
> - `claude-code/` and `ecosystem/` are convenience mirrors/upstream — prefer the categorized copy when a skill exists in both.
> - `agent-skills/engineering/{debug-mantra,scrutinize,post-mortem}` are **Iron-Law-enforcing** variants of the same skills here (fuller preambles). Either is valid; the agent-skills variant adds Iron Law enforcement.
> - **Kilo Code** discovers these via `.kilo/kilo.jsonc` → `skills.paths` (relative, repo-portable). Claude/Codex link them via `scripts/link-skills.sh` / `scripts/ecosystem/link-my-skills.sh`.

## Categories

### engineering
| Skill | Description | Status |
|-------|-------------|--------|
| [debug-mantra](./engineering/debug-mantra/SKILL.md) | Four-mantra debugging discipline: reproduce → trace → falsify → cross-reference | stable |
| [post-mortem](./engineering/post-mortem/SKILL.md) | Write the canonical engineering record of a fixed bug | stable |
| [scrutinize](./engineering/scrutinize/SKILL.md) | Outsider-perspective end-to-end review of a plan, PR, or code change | stable |

### productivity
| Skill | Description | Status |
|-------|-------------|--------|
| [management-talk](./productivity/management-talk/SKILL.md) | Rewrite engineering content for leadership audiences | stable |

### domain
| Skill | Description | Status |
|-------|-------------|--------|
| [excel-generator](./domain/excel-generator/SKILL.md) | Professional Excel spreadsheet creation | beta |
| [pharmacy-order-lookup](./domain/pharmacy-order-lookup/SKILL.md) | Drug order lookup against sp_drugstore DB | beta |

### wiki
| Skill | Description | Status |
|-------|-------------|--------|
| [ingest-source](./wiki/ingest-source/SKILL.md) | Ingest sources into wiki — raw/, URL, or pasted text | beta |
| [lint-wiki](./wiki/lint-wiki/SKILL.md) | Wiki health checks — orphans, broken links, metadata | beta |
| [wiki-search-local](./wiki/wiki-search-local/SKILL.md) | Local FTS5/grep wiki search | beta |
| [export-notebooklm](./wiki/export-notebooklm/SKILL.md) | Bundle wiki for NotebookLM upload | beta |
| [obsidian](./wiki/obsidian/SKILL.md) | Obsidian integration — wikilinks, canvas, CLI | beta |

### automation
| Skill | Description | Status |
|-------|-------------|--------|
| [hook-suggest](./automation/hook-suggest/SKILL.md) | Analyze patterns and suggest automation hooks | beta |
| [token-optimization](./automation/token-optimization/SKILL.md) | Reduce token consumption mid-session | beta |
| [verify-before-done](./automation/verify-before-done/SKILL.md) | Verify completeness before declaring done | beta |

### research
| Skill | Description | Status |
|-------|-------------|--------|
| [web-research](./research/web-research/SKILL.md) | Web search for datasheets, prices, facts | beta |
| [ask-notebooklm](./research/ask-notebooklm/SKILL.md) | Cross-file synthesis via Gemini API | beta |
| [brainstorm-before-build](./research/brainstorm-before-build/SKILL.md) | Plan before implementing >3 file changes | beta |
| [internet-skill-finder](./research/internet-skill-finder/SKILL.md) | Discover agent skills from GitHub | beta |

### delegation
| Skill | Description | Status |
|-------|-------------|--------|
| [delegate-subagent](./delegation/delegate-subagent/SKILL.md) | Delegate read-heavy work to subagents | beta |
| [crew-dispatch](./delegation/crew-dispatch/SKILL.md) | Cross-agent dispatch (Claude ↔ Gemini) | beta |
| [skill-creator](./delegation/skill-creator/SKILL.md) | Create and update agent skills | beta |

### deprecated
- **root-cause-first** — Superseded by debug-mantra (which covers the same ground with a more complete 4-step framework)

---

## Quality Standard

See [docs/protocols/skill-quality-standard.md](../docs/protocols/skill-quality-standard.md) for:
- Required frontmatter fields
- Structure requirements
- Review checklist before marking stable