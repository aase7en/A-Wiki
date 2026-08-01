---
title: Open Design
category: ai-tools
type: entity
created: 2026-08-01
related:
  - "[[claude-code]]"
  - "[[cointh-glm]]"
  - "[[frontend-design]]"
  - "[[theme-factory]]"
tags: [design, electron, byok, agent-orchestrator, ai-tools]
confidence: "[verified 2026-08-01]"
---

# Open Design

> Open-source Claude Design alternative — local-first desktop app (Electron v0.15.1) that spawns external coding-agent CLIs (Claude Code, Codex, OpenCode, Gemini, Aider, ...) as design engines to generate prototypes, landing pages, dashboards, slides, images, and videos.

- **Repo**: https://github.com/nexu-io/open-design
- **License**: Apache-2.0
- **Install path (Win)**: `C:\Users\<user>\AppData\Local\Programs\Open Design\`
- **Config path (Win)**: `C:\Users\<user>\AppData\Roaming\Open Design\namespaces\release-stable-win\data\app-config.json`

## Architecture (2 execution modes)

| Mode | Picker value | Flow |
|------|-------------|------|
| **Local CLI** (default) | "Local CLI" / agentId (claude, codex, ...) | Frontend → daemon `/api/runs` → `spawn(<agent>)` → file/tool SSE → project files → preview |
| **BYOK API** (fallback) | "Anthropic API" / "OpenAI API" / etc. | Frontend → daemon `/api/proxy/{provider}/stream` → SSE → `<artifact>` parser → preview |

Local CLI mode has **file tools** (full project); BYOK API mode returns a single `<artifact>` HTML block (no file tools).

## Config schema (app-config.json)

Verified against upstream `apps/daemon/src/app-config.ts`:

| Field | Purpose | Notes |
|-------|---------|-------|
| `agentId` | Default agent | `claude` / `codex` / `amr` / `hermes` / ... |
| `agentModels.<agent>.model` | Pin model per agent | e.g. `glm-5.2` |
| `agentCliEnv.<agent>` | Env vars injected when spawning the CLI | **Strict allowlist** (see below). Keys outside allowlist silently dropped by `validateAgentCliEnv`. |
| `agentCliEnvIntent.<agent>.apiKeyOverride` | Marker so auth keys survive normalization | Without this OR a baseUrl entry, legacy auth keys get dropped by `normalizeAgentCliEnvPrefs`. **Set both** for belt-and-braces. |

### Claude agent env allowlist (`AGENT_CLI_ENV_KEYS['claude']`)

```
CLAUDE_CONFIG_DIR, CLAUDE_BIN,
ANTHROPIC_BASE_URL, ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN,
MMD_MODEL_ROUTES_FILE
```

Auth/baseUrl split (`AGENT_CLI_AUTH_ENV_KEYS['claude']`):
- `auth`: `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`
- `baseUrl`: `ANTHROPIC_BASE_URL`

→ A block with a `baseUrl` entry OR `apiKeyOverride: true` survives normalization.

## Skill system

- **Bundled skills**: `resources/open-design/skills/` (read-only, ~162 in v0.15.1)
- **User skills (writable)**: `%APPDATA%\Open Design\namespaces\release-stable-win\data\skills\<slug>\SKILL.md`
- **Shadowing**: user root scanned first → user skill with same `name` replaces bundled
- **Rescan**: lazy (no restart needed) — open Settings → Skills to trigger
- **Install methods**: (A) drop folder manually, (B) `/api/skills/import` (minimal frontmatter only), (C) `/api/skills/install` from GitHub/local folder

### Skill frontmatter schema (OD-specific)

```yaml
---
name: <slug>              # must match folder name, [a-z0-9-]
description: |
  <one line>
triggers:
  - "<phrase>"
od:
  mode: prototype|deck|template|image|video|audio|design-system
  category: <slug for Settings filter>
  surface: web|image|video|audio
  scenario: design|marketing|engineering|product|general
  design_system:
    requires: false
  capabilities_required:
    - file_write
---
```

Import form (B) only writes `name`/`description`/`triggers` — for full `od.*` use method A or C.

### 5 concepts distinguished

| Concept | What | Folder |
|---------|------|--------|
| **skills** | Functional capabilities invoked mid-task | `skills/` + user `data/skills/` |
| **design-templates** | Renderable shapes with baked `example.html` | `design-templates/` |
| **design-systems** | DESIGN.md palette/type/voice tokens layer | `design-systems/` + user `data/design-systems/` |
| **plugins** | Marketplace bundles (460 indexed) | `plugins/registry/` |
| **library** | User asset clipboard (Figma, images, clips) | DB rows in `app.sqlite` |

## GLM 5.2 setup on Open Design (DONE 2026-08-01)

- **Goal**: route Cointh GLM 5.2 (Anthropic `/v1/messages` format) through the Claude Code CLI that Open Design spawns.
- **Config applied** (in `app-config.json`): `agentId=claude`, `agentModels.claude.model=glm-5.2`, `agentCliEnv.claude={CLAUDE_CONFIG_DIR, ANTHROPIC_BASE_URL, ANTHROPIC_AUTH_TOKEN, ANTHROPIC_API_KEY}`, `agentCliEnvIntent.claude.apiKeyOverride=true`.
- **Root cause of original "ConnectionRefused"**: `~/.claude/settings.json` had `apiKeyHelper` (pointed at uninstalled claude-code-router) + `env.ANTHROPIC_BASE_URL=http://127.0.0.1:3456` (CCR proxy not running) → overrode our env. Fix: isolated clean profile `~/.claude-opendesign/` (no apiKeyHelper) + set `CLAUDE_CONFIG_DIR` in `agentCliEnv`.
- **Resilience script**: `%APPDATA%\Open Design\glm-apply.py` (idempotent re-apply + `--check`/`--dry-run`/`--rollback`, auto-creates profile, warns on apiKeyHelper conflict). Backup at `drive/scripts/opendesign-glm-apply.py` (gitignored).
- **End-to-end verify**: passed via daemon API (`POST /api/proxy/anthropic/stream` → "I'm GLM, a large language model trained by Z.ai.")

## A-Wiki skill porting (DONE 2026-08-01)

Script: `scripts/opendesign-port-skills.py` (idempotent, re-runnable).

**Tier 1 ported (8 skills)**:
- `frontend-design` (prototype/ui-design) — distinctive UI generation
- `theme-factory` (design-system/design-systems) — 10 themes + `themes/` asset
- `make-interfaces-feel-better` (prototype/ui-design) — polish checklist
- `design-system` (design-system/design-systems) — audit + consistency
- `frontend-slides` (deck/presentations) — HTML slides + `scripts/`
- `web-artifacts-builder` (prototype/ui-design) — React/Tailwind/shadcn + `scripts/`
- `a-think` (template/reasoning) — 7-step reasoning loop
- `spec-driven-development` (template/reasoning) — turn vague prompt into spec

**Tier 2 candidates (not yet ported)**: algorithmic-art, motion-foundations, motion-patterns, canvas-design, marketing-campaign.

**Re-port after A-Wiki updates**: `python scripts/opendesign-port-skills.py` (or `--tier 2` to add Tier 2).

## Open questions

- KKU/OKMD API (https://gen.ai.kku.ac.th/okmd/api/v1): has 23 models from 9 providers, but `POST /chat/completions` returns 401 on all models while `GET /models` returns 200 → key is list-only, needs TK Park account activation. See session-memory `[2026-07-31→08-01] opendesign-glm-and-kku-council`.
