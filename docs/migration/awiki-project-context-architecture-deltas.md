# A-Wiki Project Context Architecture Deltas

> Source: prior A-Wiki conversations now grouped in the ChatGPT Project `A-wiki update`, reconciled against the active vNext master plan and the Multi-Agent Orchestrator roadmap.
> Status: architecture delta only; no implementation authorization.
> Parent docs: `awiki-vnext-plan.md`, `awiki-agent-review-bus-plan.md`, `awiki-multi-agent-orchestrator-roadmap.md`.

## Purpose

This document captures only requirements that materially sharpen the existing roadmap. It is intentionally delta-only: no duplication of architecture already covered elsewhere.

## D-CTX-001 — A-Wiki is the control tower/kernel, not the implementation monolith

A-Wiki owns the shared brain and governance layer:

- global/reusable knowledge
- memory contracts and promotion rules
- agent/team workflow protocols
- skills/routing policy
- safety/privacy/governance
- project index and project metadata
- review/orchestration contracts

Implementation repos own project-specific code, tests, deployment configuration, project-local ADRs, and product-specific plans.

Canonical relationship:

```text
A-Wiki (control tower / brain kernel)
        |
        +-- project registry / adapter metadata
        +-- reusable knowledge / skills / policy
        +-- task/review/handoff contracts
        |
        v
Implementation Repo A
Implementation Repo B
Implementation Repo C
```

A project should attach to A-Wiki; A-Wiki should not be copied into every project.

## D-CTX-002 — Explicit anti-duplication boundary

Do not maintain two competing sources of truth for one project plan.

Rules:

- do not duplicate the same `PLAN.md` in A-Wiki and the implementation repo;
- A-Wiki stores project index metadata, status, links, high-level decisions, reusable lessons, and durable handoff state;
- the implementation repo stores project-owned code plan, implementation detail, tests, findings, ADRs, and deployment/configuration specific to that repo;
- cross-repo references use ordinary stable GitHub/repository links or project-adapter identifiers;
- do not use Git submodules merely to make A-Wiki appear physically inside every project;
- avoid symlink-style coupling between public repos except where the existing private Drive boundary explicitly requires it.

## D-CTX-003 — Project adapter is the portability boundary

The portable contract remains:

```text
<project>/
├─ AGENTS.md
└─ .awiki/
   ├─ project.yaml
   ├─ context.md
   └─ state/
```

Expected operator flow:

```text
awiki attach .
awiki status
```

The adapter should tell any compatible agent:

- project identity
- project-local domains
- allowed skills/integrations
- memory scopes
- privacy/trust constraints
- project-owned repository links
- current task/review state

The central A-Wiki brain remains canonical and reusable; project adapters are thin attachment surfaces.

## D-CTX-004 — Progressive disclosure is a hard performance rule

Agents must not preload the whole A-Wiki, all skills, all MCP servers, all model inventories, or every external integration into every task.

Retrieval order:

```text
Current Task
  -> Current Project
  -> Current Domain
  -> Global Wiki
  -> External Modules
```

Progressive context loading:

```text
minimal AGENTS contract
  -> A-Router
  -> project profile
  -> relevant domain
  -> relevant skill/protocol
  -> external integration only if required
```

This is both a token-efficiency and reliability requirement. Context/tool overload is considered an architecture defect, not merely a cost issue.

## D-CTX-005 — External MCP/integrations are lazy and default-off

External MCP servers and integrations must be treated as optional modules, not globally active infrastructure.

Each integration should declare:

- capability
- trigger/domain
- trust/privacy level
- required permissions
- health check
- cost/runtime impact
- fallback/degraded behavior
- whether it is CORE / MODULE / PATTERN / REFERENCE / REJECT

A-Router / project profile may enable only the minimum set required for the active task.

Do not vendor an entire external tool family when a small reusable pattern or optional adapter is enough.

## D-CTX-006 — Universal contract + generated platform surfaces

Cross-agent compatibility must have one canonical contract rather than independent hand-maintained instructions per vendor.

Stable source:

```text
AGENTS.md + canonical registries/protocols
```

Platform-specific surfaces such as Claude/Codex/Gemini/ZCode/Kilo/etc. should be generated, adapted, or validated against that source where practical.

Hard safety must not depend on a vendor-specific hook or UI feature.

The compatibility matrix should cover at least:

- skill discovery
- MCP
- hooks/lifecycle
- filesystem/shell
- Git/worktree support
- subagents
- review interfaces
- task/handoff state
- context injection

## D-CTX-007 — Capability routing applies to both agents and models

The Multi-Agent Orchestrator roadmap defines agents as replaceable capability providers. The same principle applies to models/providers inside an agent adapter.

Do not hardcode long-lived workflow policy to model names.

Stable policy should express:

- required capability
- quality threshold
- cost/latency envelope
- privacy/trust constraints
- fallback policy
- eval/regression threshold

Runtime discovery decides which current model/provider satisfies the contract.

Benchmark/eval and routing promotion remain separate. Promotion must be explicit and evidence-backed.

## D-CTX-008 — Observability spans the whole Team OS

The future operator surface must correlate, not merely display independently:

- active project/task
- selected execution mode
- agent assignment
- claims/worktrees
- hook failures
- review findings
- CI/eval state
- model/provider health
- quota/cooldown
- memory read/write/promotion events
- integration status
- attach/project-adapter status
- token/cost estimate
- stale cache/generated-surface drift

Runtime telemetry must stay out of Git history unless deliberately promoted into a durable evidence artifact/ADR.

## D-CTX-009 — Separate control-plane state from project implementation state

A-Wiki orchestration state should point to project work without swallowing the project repository.

Example durable control-plane record:

```yaml
project: env-wastewater-webapp
repo: <stable repository identity>
active_task: AW-219
branch: feature/example
head_sha: abc123
status: REVIEW_REQUESTED
owner_role: executor
reviewer_role: independent-reviewer
```

Project code and detailed implementation remain in the project repo.

This separation allows one A-Wiki brain to supervise many repositories without turning A-Wiki itself into a mega-repo.

## D-CTX-010 — Promote lessons, not project internals

Project experience may flow back to A-Wiki only through an explicit promotion pipeline:

```text
Project Experience
  -> Distill
  -> Privacy Check
  -> Generalize
  -> Evidence Check
  -> Global Promotion
```

Promote reusable patterns, decisions, tests, failure modes, and generalized lessons.

Do not automatically promote private/project-specific data, temporary implementation notes, customer/domain secrets, or raw agent chatter into global knowledge.

## D-CTX-011 — Architecture additions require measurable value

Before adding a new framework, MCP server, daemon, database, plugin, agent adapter, or workflow family, require evidence of at least one measurable benefit:

- fewer manual handoffs
- lower context/tool count
- faster reliable completion
- stronger safety/verification
- lower cost/quota pressure
- improved portability
- improved recovery/resumability

Prefer consolidate/extract-pattern/adapter before adding infrastructure.

## D-CTX-012 — Repository movement rules remain conservative

Before moving or reorganizing paths:

```text
rg / git grep references
identify generated surfaces
identify symlinks/private boundaries
identify CI/hooks/tests/docs dependencies
add compatibility shim if needed
move in a small reversible commit
verify mechanically
```

Behavior and contracts take priority over directory aesthetics. Large repository reorganization remains a late-stage option only after the kernel interfaces are stable.

## Integration into phases

These deltas map onto the existing roadmap rather than adding a competing phase sequence:

```text
Phase 3  Kernel Contract
         -> D-CTX-001/002/006/007/009

Phase 4  Project Adapter
         -> D-CTX-003/009

Phase 5  Memory Layers
         -> D-CTX-010

Phase 6  Hook Engine
         -> D-CTX-006/008

Phase 7  Model Control Plane
         -> D-CTX-007

Phase 8  Eval / Promotion / Reviewer Adapter
         -> D-CTX-007/008

Phase 10 External Modules
         -> D-CTX-004/005

Phase 11 Documentation / Compatibility
         -> D-CTX-004/006/012

Phase 12–16 Multi-Agent Orchestrator
         -> all deltas, especially D-CTX-001/004/008/009/011
```

## Acceptance principle

The final A-Wiki architecture should allow this without copying the brain into project repositories:

```text
Open any project
  -> awiki attach/status
  -> identify project + task
  -> load minimum relevant context
  -> select one or more available capable agents
  -> execute in isolated project worktree/repo
  -> review/verify through durable state
  -> record project outcome
  -> promote only reusable generalized lessons
```

That is the operational meaning of **one brain, many projects, many agents, one governance layer**.
