# Specialized Domain Subagents

> **Status:** Active (Chunks SA2–SA6 of the Specialized Domain Subagents plan)
> **Enforced by:** `skills-registry.json` (Iron Law #9) + `scripts/hooks/check_subagent_fanout.py`
> **Protocol:** `docs/protocols/subagent-model-routing.md`

This directory holds the **definition files** for A-Wiki's specialized domain
subagents — one `.md` per subagent, loaded by ZCode from `~/.zcode/agents/`
(via symlink into this repo) and surfaced to other agents through
`gen_agents_md.py`.

The legacy review personas (`agents/code-reviewer.md`, `agents/security-auditor.md`,
`agents/test-engineer.md`, `agents/web-performance-auditor.md`) live in the
parent `agents/` directory and are **not** subagents in the ZCode sense — they
are Hermes fan-out personas. This `subagents/` subdir is reserved for true
ZCode-loadable subagent definitions.

---

## Frontmatter schema

Every `<name>.md` here uses this frontmatter (a superset of the ZCode/Claude
Code subagent format):

```yaml
---
# --- ZCode subagent fields (the part ZCode reads) ---
name: <kebab-name>                       # must match filename without .md
description: "<English, concise — primary agent uses this to route>"
tools: <comma-separated allowlist>       # optional; omit to inherit all
model: <alias | custom:<provider>:<model>>  # see model routing table below
color: <token>                           # optional UI accent

# --- A-Wiki governance fields (Iron Law #9, registry metadata) ---
source: a-wiki-subagent
adapted_for: A-Wiki
---
```

### `model` values

Aliases: `sonnet`, `opus`, `haiku`, `inherit`.
Custom: `custom:<provider-id>:<model>` (provider-id from `~/.zcode/v2/config.json`).

**Diversity rule** (see `docs/protocols/subagent-model-routing.md`): parallel
subagents in one message must not all resolve to the same provider bucket. The
default `model` per domain cluster is chosen to spread load:

| Domain cluster | Default model | Bucket |
|---|---|---|
| Coding / Data / Engineering | `sonnet` or `custom:...:deepseek-v4-pro` | anthropic / deepseek |
| Health / Finance / Business | `custom:...:deepseek-v4-flash` | deepseek |
| Assistant / Tutor / Thought-partner | `custom:...:glm-5.2` or OpenRouter free | glm / openrouter-free |
| Explore-style (read-only, fan-out) | `custom:...:deepseek-v4-flash` (NOT gemini) | deepseek |

> Provider IDs are machine-specific and live in the private config; the repo
> files use aliases where possible and `custom:...:deepseek-v4-flash` notation
> that the linker resolves at install time.

---

## The 9 domains (28 subagents)

| # | Domain | Subagents | Registry domain |
|---|---|---|---|
| 1 | Health / Medical | medical-lit-reviewer, clinical-reasoner, medical-safety-checker | medical |
| 2 | Data / Finance / Trading | finance-data-fetcher, finance-analyst, finance-debater, data-profiler | trader, data |
| 3 | AI Management | cost-auditor, model-router-advisor, token-optimizer | ai-ops |
| 4 | Webapp / Mobile / UX / DB | frontend-architect, ui-ux-reviewer, db-schema-designer, mobile-pattern-advisor | code, design, ux-ui |
| 5 | Business / Marketing / Real-estate | marketing-strategist, realestate-tax-advisor, business-doc-drafter | business, thai |
| 6 | Coding Engineering | code-architect, debug-investigator, test-engineer-agent, code-explorer-repo | code, debug, engineering |
| 7 | Personal Assistant | inbox-triage, schedule-planner, draft-responder | productivity |
| 8 | Thought Partner | workflow-simplifier, copywriting-partner | productivity, business |
| 9 | Personal Tutor | language-tutor, skill-coach | productivity, thai |

---

## Registration contract (Iron Law #9)

Every `.md` here MUST have a matching entry in `skills-registry.json` with:

```json
{
  "name": "<kebab-name>",
  "category": "subagent",
  "domain": ["<domain>", ...],
  "lifecycle_phase": "none",
  "source": "repo",
  "path": "agents/subagents/<name>.md",
  "status": "canonical",
  "agents": ["zcode"],
  "model": "<model-string>"
}
```

After adding/editing entries: `python scripts/regen-skill-surfaces.py` then commit.
The `gen_zcode_agents.py` generator emits `zcode.agents.manifest.json` consumed
by `scripts/link-agent-configs.sh` to build the `~/.zcode/agents/` symlink farm.

---

## Design references

- FinRobot (Lead + pipeline + debate agents, Director Agent for model diversity):
  https://github.com/AI4Finance-Foundation/FinRobot
- langgraph-email-automation (Categorizer → Drafter → QA): https://github.com/kaymen99/langgraph-email-automation
- Aider (architect/editor split): https://github.com/Aider-AI/aider
- CAMEL (role-playing + critic): https://github.com/camel-ai/camel
- A-Wiki personas (template): `agents/code-reviewer.md`, `agents/security-auditor.md`
