# A-Wiki Lifecycle Skills — agent-skills Adaptation Plan

**วันที่**: 2026-06-20
**ผู้จัดทำ**: Kilo AI (Plan Mode)
**สถานะ**: ✅ Finalized — ready to implement
**Source**: Adapted from [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT, v0.6.2, 63.5k+ stars)

---

## Overview

Adopt the standardized engineering lifecycle architecture from addyosmani/agent-skills into A-Wiki. This adds a structured DEFINE→PLAN→BUILD→VERIFY→REVIEW→SHIP pipeline with anti-rationalization gates, verification checklists, specialist personas, and progressive disclosure references — usable by **all agents** (Kilo, Claude Code, Codex, Gemini CLI, Cursor, Windsurf, Copilot, Aider) with **Hermes as first-class orchestrator**.

### Objectives

1. Fill gaps where A-Wiki has no engineering lifecycle skill (19 skills)
2. Keep A-Wiki's purpose-built skills that are stronger than agent-skills equivalents (4 kept: debug-mantra, scrutinize, grill-me, post-mortem)
3. Package skills as plain Markdown for cross-agent compatibility
4. Add 4 specialist personas (code-reviewer, test-engineer, security-auditor, web-performance-auditor) with parallel fan-out orchestration
5. Wire Hermes as the runtime orchestrator that consumes these skills

### Design Principles

- **Adapt, don't copy-paste** — Each imported skill gets A-Wiki conventions (confidence markers, Thai-friendly where needed, A-Wiki tool references)
- **Progressive disclosure** — SKILL.md under 500 lines, references loaded on demand
- **Anti-rationalization mandatory** — Every skill includes the excuses→rebuttals table
- **Verification non-negotiable** — Every skill ends with evidence checklist
- **Cross-agent** — Plain Markdown, no agent-specific format lock-in

---

## Gap Analysis

### Skills to Import (19) — filling real gaps

| # | Phase | Skill | Why A-Wiki needs it |
|---|-------|-------|---------------------|
| 1 | Define | `spec-driven-development` | No spec-before-code discipline. Agents jump to implementation. |
| 2 | Define | `idea-refine` | No structured divergent/convergent thinking before building. |
| 3 | Plan | `planning-and-task-breakdown` | No systematic task decomposition with acceptance criteria. |
| 4 | Build | `incremental-implementation` | No thin vertical slice discipline. Agents implement everything at once. |
| 5 | Build | `test-driven-development` | No Red-Green-Refactor workflow. Tests written after code. |
| 6 | Build | `doubt-driven-development` | No in-flight adversarial review. Critical for Hermes orchestrator. |
| 7 | Build | `source-driven-development` | No verification against official docs before implementing. |
| 8 | Build | `frontend-ui-engineering` | No UI engineering standards (component architecture, WCAG 2.1 AA). |
| 9 | Build | `api-and-interface-design` | No contract-first API design with Hyrum's Law. |
| 10 | Build | `context-engineering` | No systematic context management (when to load/unload). |
| 11 | Verify | `browser-testing-with-devtools` | No browser-based testing workflow (Chrome DevTools MCP). |
| 12 | Review | `code-simplification` | No Chesterton's Fence / Rule of 500 simplification discipline. |
| 13 | Review | `security-and-hardening` | No security review skill (OWASP Top 10, auth patterns). |
| 14 | Review | `performance-optimization` | No measure-first performance optimization workflow. |
| 15 | Ship | `git-workflow-and-versioning` | No trunk-based development / atomic commit discipline. |
| 16 | Ship | `ci-cd-and-automation` | No CI/CD pipeline design skill (Shift Left, feature flags). |
| 17 | Ship | `deprecation-and-migration` | No deprecation/migration skill (code-as-liability mindset). |
| 18 | Ship | `documentation-and-adrs` | No ADR (Architecture Decision Record) skill. |
| 19 | Ship | `observability-and-instrumentation` | No structured logging/tracing/metrics skill. |

### Skills Kept As-Is (4) — A-Wiki versions are stronger

| A-Wiki Skill | Agent-Skills Equivalent | Reason to Keep |
|-------------|------------------------|----------------|
| `debug-mantra` | `debugging-and-error-recovery` | More disciplined: 4-mantra block, mandatory recital, falsification before fix. agent-skills version is less opinionated. |
| `scrutinize` | `code-review-and-quality` | Outsider-perspective, simpler/more-elegant alternatives first, traces real code paths not just diff. |
| `grill-me` | `interview-me` | More relentless interview style, good for Thai-first context. |
| `post-mortem` | (none) | No equivalent in agent-skills. Canonical bug record format unique to A-Wiki. |

### Meta-Skill Adaptation

| Agent-Skills | A-Wiki Version | Changes |
|-------------|----------------|---------|
| `using-agent-skills` | `awiki-lifecycle-router` | Rename to avoid confusion. Add A-Wiki-specific intents (ingest-source, lint-wiki, pharmacy-order). Keep the lifecycle flow chart but add A-Wiki skill references. |

---

## Directory Structure

```
skills/engineering-lifecycle/          ← One source of truth (plain Markdown)
│
├── define/
│   ├── spec-driven-development/
│   │   └── SKILL.md                   ← Adapted: add [wiki] markers, A-Wiki tool refs
│   └── idea-refine/
│       └── SKILL.md
│
├── plan/
│   └── planning-and-task-breakdown/
│       └── SKILL.md
│
├── build/
│   ├── incremental-implementation/
│   │   └── SKILL.md
│   ├── test-driven-development/
│   │   └── SKILL.md
│   ├── doubt-driven-development/
│   │   └── SKILL.md
│   ├── source-driven-development/
│   │   └── SKILL.md
│   ├── frontend-ui-engineering/
│   │   └── SKILL.md
│   ├── api-and-interface-design/
│   │   └── SKILL.md
│   └── context-engineering/
│       └── SKILL.md
│
├── verify/
│   └── browser-testing-with-devtools/
│       └── SKILL.md
│
├── review/
│   ├── code-simplification/
│   │   └── SKILL.md
│   ├── security-and-hardening/
│   │   └── SKILL.md
│   └── performance-optimization/
│       └── SKILL.md
│
├── ship/
│   ├── git-workflow-and-versioning/
│   │   └── SKILL.md
│   ├── ci-cd-and-automation/
│   │   └── SKILL.md
│   ├── deprecation-and-migration/
│   │   └── SKILL.md
│   ├── documentation-and-adrs/
│   │   └── SKILL.md
│   ├── observability-and-instrumentation/
│   │   └── SKILL.md
│   └── shipping-and-launch/
│       └── SKILL.md
│
└── awiki-lifecycle-router/
    └── SKILL.md                       ← Adapted meta-skill

agents/                                ← Persona files (plain Markdown)
├── code-reviewer.md                   ← Staff Engineer, five-axis review
├── test-engineer.md                   ← QA Specialist, prove-it pattern
├── security-auditor.md                ← Security Engineer, OWASP assessment
└── web-performance-auditor.md         ← Web Perf Engineer, Core Web Vitals

references/                            ← Progressive disclosure checklists
├── testing-patterns.md                ← From agent-skills, adapted
├── security-checklist.md
├── performance-checklist.md
├── accessibility-checklist.md
├── observability-checklist.md
└── orchestration-patterns.md          ← Persona composition rules

hooks/                                 ← Session lifecycle
├── hooks.json                         ← SessionStart config
└── lifecycle-session-start.sh         ← Inject awiki-lifecycle-router

commands/                              ← Agent-agnostic slash commands
├── spec.md                            ← /spec → spec-driven-development
├── plan.md                            ← /plan → planning-and-task-breakdown
├── build.md                           ← /build → incremental-implementation + TDD
├── test.md                            ← /test → debug-mantra + TDD
├── review.md                          ← /review → scrutinize + code-simplification
├── code-simplify.md                   ← /code-simplify → code-simplification
└── ship.md                            ← /ship → parallel fan-out + shipping-and-launch

.kilo/skills/engineering-lifecycle/    ← Symlinks → skills/engineering-lifecycle/*
.claude/skills/engineering-lifecycle/  ← Symlinks → skills/engineering-lifecycle/*
```

---

## Skill Adaptation Guidelines

Each agent-skills skill imported into A-Wiki gets these adaptations:

### 1. Frontmatter
- Add `source: addyosmani/agent-skills@v0.6.2` field
- Add `adapted_for: A-Wiki` field
- Keep `name` and `description` from original

### 2. Content Adaptations
- Replace `npm test`/`npm run build` with project-appropriate commands from spec
- Add `[verified 2026-06-20]` confidence markers on ported content
- Replace external references (`skills/other-skill/SKILL.md`) with A-Wiki paths (`skills/engineering-lifecycle/phase/skill/SKILL.md`)
- Keep all anti-rationalization tables verbatim (these are the core value)
- Keep all verification checklists verbatim
- Add A-Wiki-specific trigger conditions (e.g., "Use when /lint fails" or "Use when ingesting a source")

### 3. Linking to Existing A-Wiki Skills
Each imported skill references A-Wiki equivalents where they exist:
- `debug-mantra` referenced from `test-driven-development` (Step 3: Debug)
- `scrutinize` referenced from `code-review-and-quality` doesn't exist (scrutinize replaces it)
- `grill-me` referenced from `spec-driven-development` (Phase 1: Clarify)
- `post-mortem` referenced from `shipping-and-launch` (post-incident)

### 4. What NOT to change
- Do NOT remove anti-rationalization tables
- Do NOT remove verification checklists
- Do NOT change the process steps
- Do NOT add Thai-first content to engineering skills (engineering skills stay English for token efficiency per Cost Pyramid)

---

## Persona Layer

### 4 Specialist Personas

| Persona | Role | Perspective | Orchestration |
|---------|------|-------------|---------------|
| `code-reviewer` | Senior Staff Engineer | Five-axis review (correctness, readability, architecture, security, performance) | Standalone or via parallel fan-out |
| `test-engineer` | QA Specialist | Test strategy, coverage analysis, prove-it pattern | Standalone or via parallel fan-out |
| `security-auditor` | Security Engineer | Vulnerability detection, threat modeling, OWASP | Standalone or via parallel fan-out |
| `web-performance-auditor` | Web Performance Engineer | Core Web Vitals audit, metric-honesty rule | Standalone |

### Orchestration Rules (from agent-skills)

```
PERSONAS DO NOT INVOKE OTHER PERSONAS.
```

- **Allowed**: Parallel fan-out with merge step (e.g., run code-reviewer + security-auditor + test-engineer concurrently, synthesize reports)
- **Forbidden**: Persona-A spawns Persona-B (creates infinite delegation chains)
- **Orchestrator**: Slash commands (`/ship`) or Hermes manages persona fan-out

### Relationship to Existing Plan's 12 Agent Types

The existing plan (awiki-customization-hermes-live.md) defines 12 agent types for the Live Dashboard UI. These 4 personas are a leaner, well-tested subset. They can coexist — the Dashboard can surface personas as pre-configured templates while users define custom types. No conflict.

---

## Hermes Integration

Hermes is the runtime orchestrator for A-Wiki. Here's how it consumes lifecycle skills:

### 1. Intent → Skill Routing

Hermes loads `awiki-lifecycle-router` at session start (via SessionStart hook) and maps user intents:

```
User: "Build a REST API for task management"
  → Hermes routes: DEFINE phase
    → spec-driven-development (write spec first)
    → Confirm spec with user
    → PLAN phase
      → planning-and-task-breakdown (decompose into tasks)
    → BUILD phase
      → incremental-implementation (one slice at a time)
      → test-driven-development (test before code)
      → api-and-interface-design (contract-first)

User: "Fix the login bug"
  → Hermes routes: VERIFY phase
    → debug-mantra (A-Wiki skill, 4-step)
    → test-driven-development (write failing test)
    → Post-fix: post-mortem (A-Wiki skill, document root cause)

User: "Deploy to production"
  → Hermes routes: SHIP phase
    → shipping-and-launch (pre-launch checklist)
    → Parallel fan-out:
      ├── code-reviewer (review all changes)
      ├── security-auditor (OWASP check)
      └── test-engineer (coverage verification)
    → Merge reports → deploy
```

### 2. Parallel Fan-Out Orchestration

Hermes implements the only endorsed multi-persona pattern:

```yaml
# Hermes orchestration config (conceptual)
fan_out:
  pattern: parallel-merge
  personas: [code-reviewer, security-auditor, test-engineer]
  merge_strategy: union
  stop_on: critical  # critical finding blocks merge
  timeout_ms: 300000
```

### 3. Lifecycle Enforcement

Hermes enforces phase gates:

```
DEFINE → PLAN → BUILD → VERIFY → REVIEW → SHIP
  │       │       │        │        │        │
  ▼       ▼       ▼        ▼        ▼        ▼
 Spec   Tasks   Code    Tests    Review   Deploy
 gate   gate    gate    gate     gate     gate
```

- Spec gate: No code without spec (unless single-line fix)
- Task gate: No implementation without task breakdown
- Review gate: No ship without review (scrutinize or person fan-out)
- Anti-rationalization gate: Hermes reads each skill's rationalization table and blocks known shortcuts

### 4. Configuration

New file: `scripts/hermes/lifecycle-config.json` (tracked)

```json
{
  "phases": {
    "define": { "required_before": "plan", "skills": ["spec-driven-development", "idea-refine", "grill-me"] },
    "plan": { "required_before": "build", "skills": ["planning-and-task-breakdown"] },
    "build": { "required_before": "verify", "skills": ["incremental-implementation", "test-driven-development", "doubt-driven-development", "source-driven-development", "frontend-ui-engineering", "api-and-interface-design", "context-engineering"] },
    "verify": { "required_before": "review", "skills": ["debug-mantra", "browser-testing-with-devtools"] },
    "review": { "required_before": "ship", "skills": ["scrutinize", "code-simplification", "security-and-hardening", "performance-optimization"] },
    "ship": { "required_before": null, "skills": ["git-workflow-and-versioning", "ci-cd-and-automation", "deprecation-and-migration", "documentation-and-adrs", "observability-and-instrumentation", "shipping-and-launch", "post-mortem"] }
  },
  "personas": {
    "parallel_fan_out": ["code-reviewer", "test-engineer", "security-auditor"],
    "merge_on": ["critical", "important"],
    "rule": "personas_do_not_invoke_personas"
  },
  "shortcut_blocklist": [
    { "pattern": "implement_without_spec", "message": "Iron Law #1: No code without failing test. No implementation without spec." },
    { "pattern": "skip_review_before_ship", "message": "Review gate required before SHIP phase." }
  ]
}
```

---

## Hook Integration

### SessionStart Hook

New file: `hooks/lifecycle-session-start.sh`

Injects `awiki-lifecycle-router` at session start for all agents:

```bash
#!/bin/bash
# A-Wiki lifecycle skills — session start hook
# Injects the awiki-lifecycle-router meta-skill into every new session
# Works across: Kilo, Claude Code, Codex, Gemini CLI, Cursor, Windsurf, Copilot

META_SKILL="skills/engineering-lifecycle/awiki-lifecycle-router/SKILL.md"

if [ -f "$META_SKILL" ]; then
  CONTENT=$(cat "$META_SKILL")
  jq -cn --arg message "$CONTENT" '{priority: "IMPORTANT", message: $message}'
fi
```

### Hook Registration

New file: `hooks/hooks.json`

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash hooks/lifecycle-session-start.sh"
          }
        ]
      }
    ]
  }
}
```

---

## Slash Commands

Agent-agnostic command definitions. Each platform (Kilo, Claude Code, Gemini CLI, Antigravity) has its own format, but the command logic is shared.

| Command | Maps To | What It Does |
|---------|---------|--------------|
| `/spec` | `spec-driven-development` | Define what to build with spec + success criteria |
| `/plan` | `planning-and-task-breakdown` | Break spec into verifiable tasks |
| `/build` | `incremental-implementation` + `test-driven-development` | Build slice by slice, test-first |
| `/test` | `debug-mantra` + `test-driven-development` | Debug failures, fix with TDD |
| `/review` | `scrutinize` + `code-simplification` | Review quality, simplify |
| `/code-simplify` | `code-simplification` | Reduce complexity, preserve behavior |
| `/ship` | `shipping-and-launch` + parallel fan-out | Pre-launch checklist + persona review |
| `/webperf` | `web-performance-auditor` | Core Web Vitals audit |

---

## Cross-Agent Compatibility Matrix

| Agent | Skill Discovery | Slash Commands | Personas | Notes |
|-------|----------------|----------------|----------|-------|
| **Hermes** | Native (orchestrator) | Native (commands/) | Native (parallel fan-out) | First-class integration |
| **Kilo** | `.kilo/skills/` symlinks | `.kilo/command/*.md` | `.kilo/agent/*.md` | Already has skill tool |
| **Claude Code** | `.claude/skills/` symlinks | `.claude/commands/*.md` | `agents/*.md` auto-discovered | Plugin marketplace compatible |
| **Codex** | `AGENTS.md` references | N/A (AGENTS.md intent mapping) | `agents/*.md` via AGENTS.md | Intent→skill mapping in AGENTS.md |
| **Gemini CLI** | `.gemini/skills/` symlinks | `.gemini/commands/*.md` | `.gemini/agents/*.md` | Native skill support |
| **Cursor** | `.cursor/rules/` reference | N/A | Copy persona to rules | Manual setup |
| **Windsurf** | `.windsurfrules` reference | N/A | Same as Cursor | Manual setup |
| **Copilot** | `.github/copilot-instructions.md` | N/A | `.github/agents/*.md` | Persona support |
| **Aider** | `.aider.conf.yml` `read:` list | N/A | N/A | Read SKILL.md as context |

---

## Files Changed Summary

### New files (38)
```
skills/engineering-lifecycle/define/spec-driven-development/SKILL.md
skills/engineering-lifecycle/define/idea-refine/SKILL.md
skills/engineering-lifecycle/plan/planning-and-task-breakdown/SKILL.md
skills/engineering-lifecycle/build/incremental-implementation/SKILL.md
skills/engineering-lifecycle/build/test-driven-development/SKILL.md
skills/engineering-lifecycle/build/doubt-driven-development/SKILL.md
skills/engineering-lifecycle/build/source-driven-development/SKILL.md
skills/engineering-lifecycle/build/frontend-ui-engineering/SKILL.md
skills/engineering-lifecycle/build/api-and-interface-design/SKILL.md
skills/engineering-lifecycle/build/context-engineering/SKILL.md
skills/engineering-lifecycle/verify/browser-testing-with-devtools/SKILL.md
skills/engineering-lifecycle/review/code-simplification/SKILL.md
skills/engineering-lifecycle/review/security-and-hardening/SKILL.md
skills/engineering-lifecycle/review/performance-optimization/SKILL.md
skills/engineering-lifecycle/ship/git-workflow-and-versioning/SKILL.md
skills/engineering-lifecycle/ship/ci-cd-and-automation/SKILL.md
skills/engineering-lifecycle/ship/deprecation-and-migration/SKILL.md
skills/engineering-lifecycle/ship/documentation-and-adrs/SKILL.md
skills/engineering-lifecycle/ship/observability-and-instrumentation/SKILL.md
skills/engineering-lifecycle/ship/shipping-and-launch/SKILL.md
skills/engineering-lifecycle/awiki-lifecycle-router/SKILL.md
agents/code-reviewer.md
agents/test-engineer.md
agents/security-auditor.md
agents/web-performance-auditor.md
references/testing-patterns.md
references/security-checklist.md
references/performance-checklist.md
references/accessibility-checklist.md
references/observability-checklist.md
references/orchestration-patterns.md
hooks/hooks.json
hooks/lifecycle-session-start.sh
commands/spec.md
commands/plan.md
commands/build.md
commands/test.md
commands/review.md
commands/code-simplify.md
commands/ship.md
scripts/hermes/lifecycle-config.json
```

### New symlinks
```
.kilo/skills/engineering-lifecycle/ → skills/engineering-lifecycle/
.kilo/agent/code-reviewer.md → agents/code-reviewer.md
.kilo/agent/test-engineer.md → agents/test-engineer.md
.kilo/agent/security-auditor.md → agents/security-auditor.md
.kilo/agent/web-performance-auditor.md → agents/web-performance-auditor.md
```

### Modified files (2)
- `AGENTS.md` — Add lifecycle skills reference, intent→skill mapping table for Codex/OpenCode agents
- `CLAUDE.md` — Add lifecycle skills section, persona discovery

---

## Implementation Order

```
Phase 1: Foundation Skeleton
  ├── 1.1 Create directory structure (skills/engineering-lifecycle/*, agents/, references/, commands/, hooks/)
  ├── 1.2 Port references/ (6 files) — no dependencies, straightforward copy+adapt
  └── 1.3 Port awiki-lifecycle-router meta-skill — needed first for discovery

Phase 2: Define + Plan (minimal viable lifecycle start)
  ├── 2.1 spec-driven-development (complex — most adaptations needed)
  ├── 2.2 idea-refine
  └── 2.3 planning-and-task-breakdown

Phase 3: Build Skills (core engineering discipline)
  ├── 3.1 incremental-implementation
  ├── 3.2 test-driven-development
  ├── 3.3 api-and-interface-design
  ├── 3.4 source-driven-development
  ├── 3.5 frontend-ui-engineering
  ├── 3.6 context-engineering
  └── 3.7 doubt-driven-development (complex — needs Hermes-aware adaptation)

Phase 4: Verify + Review Skills
  ├── 4.1 browser-testing-with-devtools
  ├── 4.2 code-simplification
  ├── 4.3 security-and-hardening
  └── 4.4 performance-optimization

Phase 5: Ship Skills + Personas
  ├── 5.1 All 6 ship skills (simpler, mostly checklist-based)
  ├── 5.2 4 agent personas
  └── 5.3 orchestration-patterns.md reference

Phase 6: Cross-Agent Wiring
  ├── 6.1 hooks/lifecycle-session-start.sh + hooks.json
  ├── 6.2 commands/*.md (7 slash commands)
  ├── 6.3 .kilo/ symlinks (Kilo)
  ├── 6.4 AGENTS.md update (Codex/OpenCode/Copilot/Aider)
  ├── 6.5 CLAUDE.md update (Claude Code)
  └── 6.6 .gemini/ symlinks (Gemini CLI)

Phase 7: Hermes Integration
  ├── 7.1 scripts/hermes/lifecycle-config.json
  ├── 7.2 Hermes routing logic (if Hermes code exists in repo)
  └── 7.3 Integration test: Hermes runs full DEFINE→SHIP cycle

Phase 8: Health Check
  ├── 8.1 Verify all SKILL.md files pass lint-wiki
  ├── 8.2 Verify all symlinks resolve
  ├── 8.3 Verify hooks fire correctly
  └── 8.4 Verify Hermes loads lifecycle-config.json
```

---

## Validation Plan

### Per-Skill Validation
- [ ] YAML frontmatter valid (`name`, `description` present)
- [ ] Contains Overview, When to Use, Process, Rationalizations, Red Flags, Verification sections
- [ ] Under 500 lines (progressive disclosure rule)
- [ ] Anti-rationalization table present with ≥3 excuses
- [ ] Verification checklist present with ≥5 items
- [ ] Source attribution preserved (`source: addyosmani/agent-skills@v0.6.2`)
- [ ] No hardcoded agent-specific paths

### Cross-Agent Validation
- [ ] Kilo: `.kilo/skills/` symlinks resolve, `skill` tool loads skills
- [ ] Claude Code: SessionStart hook injects router, `/spec` command fires
- [ ] Codex: AGENTS.md intent mapping triggers correct skill
- [ ] Hermes: lifecycle-config.json loads, fan-out spawns personas

### Content Validation
- [ ] No contradictions with existing A-Wiki skills
- [ ] Cross-references between skills resolve correctly
- [ ] Confidence markers applied where content is adapted

---

## Risks

| Risk | Mitigation |
|------|-----------|
| **Too many skills at once** — context bloat | Progressive disclosure: meta-skill loads first, phase skills loaded on demand. Refs not loaded unless triggered. |
| **A-Wiki conventions conflict** — agent-skills assumes npm/JS ecosystem | Adapt command examples. Keep processes generic (not JS-specific). |
| **Hermes not ready** — lifecycle config depends on Hermes being functional | Phase 7 (Hermes) is last. Skills work standalone without Hermes. |
| **Maintenance burden** — 19 imported skills need updates when agent-skills upstream changes | Track upstream version in frontmatter. Spot-check quarterly. Not auto-sync. |
| **Token cost** — SessionStart hook injects meta-skill every session (~2K tokens) | Meta-skill is the only always-loaded artifact. Phase skills loaded only when triggered. Net positive: saves tokens by preventing blind implementation attempts. |
| **Skill overlap confusion** — debug-mantra vs debugging-and-error-recovery, scrutinize vs code-review-and-quality | A-Wiki skills are kept, agent-skills equivalents are NOT imported. Clear boundaries. |

---

## Open Questions

1. **Hermes CLI location**: Where does Hermes live in the repo? `scripts/hermes/`? Need to confirm before Phase 7.
2. **Gemini CLI symlinks**: Does Gemini CLI auto-discover `.gemini/skills/` or need explicit config?
3. **agent-skills upstream license**: MIT — confirmed. Attribution preserved in frontmatter.
4. **AGENTS.md size**: Adding intent→skill mapping table to AGENTS.md adds ~50 lines. Acceptable under progressive disclosure.
