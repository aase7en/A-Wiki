# Agile Swarm — Dynamic Parallel Model Allocation

> **Purpose:** Divide background parallel work across dynamically-scouted models,
> with the Primary Agent acting as Senior Critic enforcing Iron Laws.

## Swarm Architecture

```
┌─────────────────────────────────────────────────────────┐
│                PRIMARY AGENT (Senior Critic)             │
│  ─── Validates ALL outputs against Iron Laws before      │
│       merge. Cannot be delegated.                        │
├─────────────────────────────────────────────────────────┤
│                    SWARM LAYER                            │
│                                                          │
│  ┌─────────────────────┐  ┌─────────────────────────┐   │
│  │   ARCHITECT ROLE    │  │    EXECUTIONER ROLE      │   │
│  │ (Reasoning/CoT)     │  │  (Fast Coder/Flash Tier) │   │
│  │                     │  │                          │   │
│  │ - Root cause        │  │ - Code generation        │   │
│  │ - Architecture plan  │  │ - Test writing           │   │
│  │ - Design decisions   │  │ - Refactoring            │   │
│  │ - Debug direction    │  │ - Documentation          │   │
│  └─────────────────────┘  └─────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Role Definitions

### 1. Architect Role
- **Routing:** Cheapest available "Reasoning/Chain-of-Thought" model
- **Outputs:** Plans, designs, root cause analyses, architecture decisions
- **Characteristics needed:** Deep reasoning, wide context window, step-by-step thinking
- **Example models (scouted):** DeepSeek-R1 variants, QwQ, Gemini Thinking, Claude Sonnet (cheap tier)

### 2. Executioner Role
- **Routing:** High-speed, cheap or free "Flash/Coder" model tier
- **Outputs:** Code blocks, components, test files, patches
- **Characteristics needed:** Fast generation, good at code, cheap per token
- **Example models (scouted):** Gemini Flash, Claude Haiku, GPT-4o Mini, DeepSeek Coder

### 3. Senior Critic (Primary Agent — NOT DELEGATABLE)
- **Always the Primary Agent.** Cannot be parallelized or delegated.
- **Validates:**
  - ✅ Does the Architect's plan respect the Iron Laws?
  - ✅ Does the Executioner's code have a **failing test first**?
  - ✅ Was proper root cause analysis completed before any fix?
  - ✅ Are all breadcrumbs cross-referenced?
- **On violation:** DISCARD the output. FLAG the violation. REWRITE.

## Swarm Workflow

```
1. SCOUT → Query model-scouter.md for available free/beta models
2. PLAN  → Primary Agent creates work breakdown
3. ALLOCATE → Route Architect tasks to Reasoning model
                Route Executioner tasks to Coder model
4. PARALLEL EXECUTE → Run both paths concurrently
5. VALIDATE → Primary Agent reviews ALL outputs against Iron Laws
6. MERGE  → If all pass → merge into final output
             If any fail → FLAG → DISCARD → REWRITE → re-validate
```

## Operational Rules

1. **No parallel execution without Iron Law validation.**
2. **Architect output must include explicit "Constraints Enforced" section** listing which Iron Laws were checked.
3. **Executioner output MUST include a failing test** before any production code block.
4. **If scouting returns zero free models** → collapse to single-agent mode (Primary Agent does all work).
5. **Session memory** (`session-memory.md`) is updated with swarm decisions for cross-device continuity.
