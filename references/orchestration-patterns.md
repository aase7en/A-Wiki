# Orchestration Patterns

**source**: addyosmani/agent-skills@v0.6.2 | **adapted**: A-Wiki | **verified**: 2026-06-20

Reference catalog of agent orchestration patterns. The governing rule: **the user (or a slash command) is the orchestrator. Personas do not invoke other personas.**

---

## Endorsed Patterns

### Pattern 1: Direct Invocation

Single persona, single perspective, single artifact. The default and cheapest option.

```
user → code-reviewer → report → user
```

**Use when:** the work is one perspective on one artifact.

**Cost:** one round trip. The baseline to compare orchestrated patterns against.

---

### Pattern 2: Single-Persona Slash Command

A slash command that wraps one persona with skills. Saves re-explaining the workflow.

```
/review → code-reviewer (with code-review-and-quality skill) → report
```

**Use when:** the same single-persona invocation happens repeatedly.

**Cost:** same as direct invocation.

---

### Pattern 3: Parallel Fan-Out with Merge

Multiple personas operate on the same input concurrently, each producing an independent report. A merge step synthesizes them.

```
/ship → fan out ─┼─→ code-reviewer     ─┤→ merge → go/no-go
                 └─→ security-auditor  ─┘
```

**Use when:**
- Sub-tasks are genuinely independent (no shared mutable state)
- Each sub-agent benefits from its own context window
- Wall-clock latency matters

**Validation checklist:**
- [ ] Can I run all sub-agents at the same time without ordering issues?
- [ ] Does each persona produce a different *kind* of finding?
- [ ] Will the merge step fit in the main agent's remaining context?

---

### Pattern 4: Sequential Pipeline (User-Driven)

The user runs slash commands in a defined order. No orchestrator agent — the user IS the orchestrator.

```
user runs: /spec → /plan → /build → /test → /review → /ship
```

**Use when:** the workflow has dependencies and human judgment between steps adds value.

---

### Pattern 5: Research Isolation

When a task requires reading large amounts of material, spawn a research sub-agent that returns only a digest.

```
main agent → research sub-agent (reads 50 files) → digest → main agent continues
```

**Use when:** the investigation result is much smaller than the input it consumes.

---

## Anti-Patterns

### A. Router Persona ("Meta-Orchestrator")

A persona whose job is to decide which other persona to call.

**Why it fails:** Pure routing with no domain value, adds paraphrasing hops and token cost.

**What to do instead:** add or refine slash commands.

### B. Persona Calls Another Persona

A `code-reviewer` that internally invokes `security-auditor`.

**Why it fails:** Personas produce a single perspective; chaining defeats that. Summary passing loses context.

**What to do instead:** have the calling persona *recommend* a follow-up in its report.

### C. Sequential Orchestrator That Paraphrases

An agent that calls `/spec`, then `/plan`, then `/build` on the user's behalf.

**Why it fails:** Loses human checkpoints, accumulated context drift, doubled token cost.

### D. Deep Persona Trees

`/ship` calls a coordinator that calls another coordinator that calls `code-reviewer`.

**Why it fails:** Each layer adds latency and tokens with no decision value.

---

## Decision Flow

```
Is the work one perspective on one artifact?
├── Yes → Direct invocation. Stop.
└── No  → Will the same composition repeat?
         ├── No  → Direct invocation, ad hoc. Stop.
         └── Yes → Are sub-tasks independent?
                  ├── No  → Sequential slash commands (Pattern 4)
                  └── Yes → Parallel fan-out with merge (Pattern 3)
```

---

## Hermes Orchestrator Integration

Hermes implements these patterns as runtime workflows:

| Pattern | Hermes Implementation |
|---------|----------------------|
| Direct invocation | `hermes spawn code-reviewer --file path/to/file` |
| Parallel fan-out | `hermes fan-out --personas code-reviewer,security-auditor,test-engineer` |
| Sequential pipeline | `hermes lifecycle --start spec --end ship` |
| Research isolation | `hermes research --query "find all API endpoints" --depth 50` |

Config: `scripts/hermes/lifecycle-config.json`

**Critical rule**: Hermes enforces "personas do not invoke personas" at the orchestrator level. Personas spawned by Hermes cannot spawn sub-personas.
