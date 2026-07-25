---
name: continuous-agent-loop
description: "Canonical patterns & architectures for autonomous agent loops — cross-agent (Claude Code / Gemini CLI / Codex / Aider / Hermes / ZCode / Cursor), not Claude-only. 6 patterns: sequential pipeline, NanoClaw REPL, infinite agentic loop, continuous-PR loop, de-sloppify, RFC-driven DAG. Headless CLI cheat-sheet + cross-agent gotchas. Trigger: 'autonomous loop', 'agent loop', 'CI dev', 'run agent unattended', 'continuous claude'."
version: 2.0.0
author: A-Wiki
origin: ECC (v1.8 supersedes autonomous-loops; v2.0.0 cross-agent port)
domain: [engineering, automation]
lifecycle_phase: build
category: pipeline
agents: [all]
invocation: manual
# 2026-07-25: v2.0.0 — port full 611-line content from autonomous-loops (deprecated) +
#              generalize claude -p → cross-agent CLI table. Closes "supersede but never
#              ported content" gap. autonomous-loops now slimmed to a redirect pointer.
---

# Continuous Agent Loop (cross-agent)

Patterns, architectures, and reference implementations for running AI coding agents **autonomously in loops** — from the simplest one-shot pipeline to RFC-driven multi-agent DAG orchestration. **Agent-agnostic**: works with Claude Code, Gemini CLI, Codex, Aider, Hermes, ZCode, Cursor, and any agent that supports a headless/non-interactive mode.

> **Why cross-agent:** the original ECC pattern (autonomous-loops v1.x) used `claude -p` exclusively. A-Wiki runs Codex, Gemini, Hermes, and others side-by-side; locking loops to one CLI blocks cost-routing and swarm allocation (see §Cost-First Decision Pyramid in AGENTS.md).

## When to Use

- Setting up autonomous development workflows that run without human intervention
- Choosing the right loop architecture for your problem (simple vs complex)
- Building CI/CD-style continuous development pipelines
- Running parallel agents with merge coordination
- Implementing context persistence across loop iterations
- Adding quality gates and cleanup passes to autonomous workflows

## Loop Pattern Spectrum

From simplest to most sophisticated:

| Pattern | Complexity | Best For |
|---------|-----------|----------|
| [Sequential Pipeline](#1-sequential-pipeline) | Low | Daily dev steps, scripted workflows |
| [NanoClaw REPL](#2-nanoclaw-repl) | Low | Interactive persistent sessions |
| [Infinite Agentic Loop](#3-infinite-agentic-loop) | Medium | Parallel content generation, spec-driven work |
| [Continuous PR Loop](#4-continuous-pr-loop) | Medium | Multi-day iterative projects with CI gates |
| [De-Sloppify Pattern](#5-the-de-sloppify-pattern) | Add-on | Quality cleanup after any Implementer step |
| [RFC-Driven DAG](#6-rfc-driven-dag-orchestration) | High | Large features, multi-unit parallel work with merge queue |

---

## 0. Headless CLI Cheat-Sheet (cross-agent)

Every pattern below is built from a single primitive: **run the agent non-interactively with a prompt, exit when done**. The flag differs per agent.

| Agent | Headless command | Notes |
|-------|-----------------|-------|
| **Claude Code** | `claude -p "<prompt>"` | `-p` / `--print`. Add `--allowedTools "Read,Grep"` to lock tools; `--model opus` to route. |
| **Gemini CLI** | `gemini -p "<prompt>"` | `-p` / `--prompt`. Add `--output-format json` for scripting; `--approval-mode yolo` to skip confirmations. |
| **Codex (OpenAI)** | `codex exec "<prompt>"` | `exec` subcommand = non-interactive. Verify on your version; older builds used `codex --non-interactive`. |
| **Aider** | `aider --message "<prompt>" --yes-always` | `--message` / `-m` = one-shot. `--yes-always` skips confirmations for CI. Pair with `--model <name>`. |
| **Hermes** | `hermes run "<prompt>"` | A-Wiki orchestrator; reads `lifecycle-config.json`. Use `--non-interactive` for headless. |
| **ZCode / Cursor / Windsurf** | GUI-only or vendor CLI | No stable headless flag — drive via their plugin/extension API, not as a `-p` step. |

> **Verified 2026-07-25:** `claude -p` and `gemini -p` confirmed via local `--help` output. Codex/Aider flags are public-documented but vary by version — run `<cli> --help` on your install before scripting.

### Universal wrapper pattern

To make any loop agent-agnostic, wrap the CLI in a shell function and parameterize:

```bash
#!/usr/bin/env bash
# run-agent.sh — universal headless agent wrapper
# Usage: AGENT=claude ./run-agent.sh "implement feature X with TDD"
#        AGENT=gemini ./run-agent.sh "review code for security"

set -eu
AGENT="${AGENT:-claude}"
PROMPT="$1"

case "$AGENT" in
  claude)  claude -p "$PROMPT" ;;
  gemini)  gemini -p "$PROMPT" ;;
  codex)   codex exec "$PROMPT" ;;
  aider)   aider --message "$PROMPT" --yes-always ;;
  hermes)  hermes run "$PROMPT" --non-interactive ;;
  *) echo "unknown agent: $AGENT" >&2; exit 2 ;;
esac
```

Now every pattern below uses `./run-agent.sh "<prompt>"` instead of a hardcoded CLI.

---

## 1. Sequential Pipeline

**The simplest loop.** Break daily development into a sequence of non-interactive agent calls. Each call is a focused step with a clear prompt.

### Core Insight

> If you can't figure out a loop like this, it means you can't even drive the LLM to fix your code in interactive mode.

The headless flag runs the agent non-interactively with a prompt, exits when done. Chain calls to build a pipeline:

```bash
#!/usr/bin/env bash
# daily_dev.sh — Sequential pipeline for a feature branch

set -e

# Step 1: Implement the feature
./run-agent.sh "Read the spec in docs/auth-spec.md. Implement OAuth2 login in src/auth/. Write tests first (TDD). Do NOT create any new documentation files."

# Step 2: De-sloppify (cleanup pass)
./run-agent.sh "Review all files changed by the previous commit. Remove any unnecessary type tests, overly defensive checks, or testing of language features (e.g., testing that TypeScript generics work). Keep real business logic tests. Run the test suite after cleanup."

# Step 3: Verify
./run-agent.sh "Run the full build, lint, type check, and test suite. Fix any failures. Do not add new features."

# Step 4: Commit
./run-agent.sh "Create a conventional commit for all staged changes. Use 'feat: add OAuth2 login flow' as the message."
```

### Key Design Principles

1. **Each step is isolated** — A fresh context window per call means no context bleed between steps.
2. **Order matters** — Steps execute sequentially. Each builds on the filesystem state left by the previous.
3. **Negative instructions are dangerous** — Don't say "don't test type systems." Instead, add a separate cleanup step (see [De-Sloppify Pattern](#5-the-de-sloppify-pattern)).
4. **Exit codes propagate** — `set -e` stops the pipeline on failure.

### Variations

**With model routing (per-agent):**
```bash
# Research with a reasoning model
AGENT=claude AGENT_FLAGS="--model opus" ./run-agent.sh "Analyze the codebase architecture and write a plan for adding caching..."

# Implement with a fast coder
AGENT=codex ./run-agent.sh "Implement the caching layer according to the plan in docs/caching-plan.md..."

# Review with a thorough model
AGENT=gemini ./run-agent.sh "Review all changes for security issues, race conditions, and edge cases..."
```

**With environment context:**
```bash
# Pass context via files, not prompt length
echo "Focus areas: auth module, API rate limiting" > .agent-context.md
./run-agent.sh "Read .agent-context.md for priorities. Work through them in order."
rm .agent-context.md
```

**With tool restrictions:**
```bash
# Read-only analysis pass (Claude syntax)
AGENT_FLAGS='--allowedTools "Read,Grep,Glob"' AGENT=claude ./run-agent.sh "Audit this codebase for security vulnerabilities..."

# Write-only implementation pass
AGENT_FLAGS='--allowedTools "Read,Write,Edit,Bash"' AGENT=claude ./run-agent.sh "Implement the fixes from security-audit.md..."
```

---

## 2. NanoClaw REPL

**ECC's built-in persistent loop.** A session-aware REPL that calls a headless agent synchronously with full conversation history.

```bash
# Start the default session
node scripts/claw.js

# Named session with skill context
CLAW_SESSION=my-project CLAW_SKILLS=tdd-workflow,security-review node scripts/claw.js
```

### How It Works

1. Loads conversation history from `~/.claude/claw/{session}.md`
2. Each user message is sent to the headless agent with full history as context
3. Responses are appended to the session file (Markdown-as-database)
4. Sessions persist across restarts

### When NanoClaw vs Sequential Pipeline

| Use Case | NanoClaw | Sequential Pipeline |
|----------|----------|-------------------|
| Interactive exploration | Yes | No |
| Scripted automation | No | Yes |
| Session persistence | Built-in | Manual |
| Context accumulation | Grows per turn | Fresh each step |
| CI/CD integration | Poor | Excellent |

> **Cross-agent note:** NanoClaw as shipped calls `claude -p`. To repoint at another agent, edit the spawn call in `scripts/claw.js` to invoke your wrapper (§0). The session-persistence pattern itself is agent-agnostic.

---

## 3. Infinite Agentic Loop

**A two-prompt system** that orchestrates parallel sub-agents for specification-driven generation. Developed by disler (credit: @disler).

### Architecture: Two-Prompt System

```
PROMPT 1 (Orchestrator)              PROMPT 2 (Sub-Agents)
┌─────────────────────┐             ┌──────────────────────┐
│ Parse spec file      │             │ Receive full context  │
│ Scan output dir      │  deploys   │ Read assigned number  │
│ Plan iteration       │────────────│ Follow spec exactly   │
│ Assign creative dirs │  N agents  │ Generate unique output │
│ Manage waves         │             │ Save to output dir    │
└─────────────────────┘             └──────────────────────┘
```

### The Pattern

1. **Spec Analysis** — Orchestrator reads a specification file (Markdown) defining what to generate
2. **Directory Recon** — Scans existing output to find the highest iteration number
3. **Parallel Deployment** — Launches N sub-agents, each with:
   - The full spec
   - A unique creative direction
   - A specific iteration number (no conflicts)
   - A snapshot of existing iterations (for uniqueness)
4. **Wave Management** — For infinite mode, deploys waves of 3-5 agents until context is exhausted

### Implementation via Agent Commands

Create `.claude/commands/infinite.md` (or `.gemini/commands/infinite.md`, `.codex/commands/infinite.md` — same body):

```markdown
Parse the following arguments from $ARGUMENTS:
1. spec_file — path to the specification markdown
2. output_dir — where iterations are saved
3. count — integer 1-N or "infinite"

PHASE 1: Read and deeply understand the specification.
PHASE 2: List output_dir, find highest iteration number. Start at N+1.
PHASE 3: Plan creative directions — each agent gets a DIFFERENT theme/approach.
PHASE 4: Deploy sub-agents in parallel (Task tool). Each receives:
  - Full spec text
  - Current directory snapshot
  - Their assigned iteration number
  - Their unique creative direction
PHASE 5 (infinite mode): Loop in waves of 3-5 until context is low.
```

**Invoke:**
```bash
/project:infinite specs/component-spec.md src/ 5
/project:infinite specs/component-spec.md src/ infinite
```

### Batching Strategy

| Count | Strategy |
|-------|----------|
| 1-5 | All agents simultaneously |
| 6-20 | Batches of 5 |
| infinite | Waves of 3-5, progressive sophistication |

### Key Insight: Uniqueness via Assignment

Don't rely on agents to self-differentiate. The orchestrator **assigns** each agent a specific creative direction and iteration number. This prevents duplicate concepts across parallel agents.

---

## 4. Continuous PR Loop

**A production-grade shell script** that runs an agent in a continuous loop, creating PRs, waiting for CI, and merging automatically. Created by AnandChowdhary (credit: @AnandChowdhary) as `continuous-claude`; the pattern generalizes to any agent with a headless mode.

### Core Loop

```
┌─────────────────────────────────────────────────────┐
│  CONTINUOUS AGENT ITERATION                         │
│                                                     │
│  1. Create branch (continuous-agent/iteration-N)    │
│  2. Run agent headless with enhanced prompt         │
│  3. (Optional) Reviewer pass — separate agent call  │
│  4. Commit changes (agent generates message)        │
│  5. Push + create PR (gh pr create)                 │
│  6. Wait for CI checks (poll gh pr checks)          │
│  7. CI failure? → Auto-fix pass (agent headless)    │
│  8. Merge PR (squash/merge/rebase)                  │
│  9. Return to main → repeat                         │
│                                                     │
│  Limit by: --max-runs N | --max-cost $X             │
│            --max-duration 2h | completion signal     │
└─────────────────────────────────────────────────────┘
```

### Installation

> **Warning:** Install `continuous-claude` (or a port) from its repository after reviewing the code. Do not pipe external scripts directly to bash. For non-Claude agents, fork and swap the `claude -p` call for your wrapper (§0).

### Usage

```bash
# Basic: 10 iterations
continuous-claude --prompt "Add unit tests for all untested functions" --max-runs 10

# Cost-limited
continuous-claude --prompt "Fix all linter errors" --max-cost 5.00

# Time-boxed
continuous-claude --prompt "Improve test coverage" --max-duration 8h

# With code review pass
continuous-claude \
  --prompt "Add authentication feature" \
  --max-runs 10 \
  --review-prompt "Run npm test && npm run lint, fix any failures"

# Parallel via worktrees
continuous-claude --prompt "Add tests" --max-runs 5 --worktree tests-worker &
continuous-claude --prompt "Refactor code" --max-runs 5 --worktree refactor-worker &
wait
```

### Cross-Iteration Context: SHARED_TASK_NOTES.md

The critical innovation: a `SHARED_TASK_NOTES.md` file persists across iterations:

```markdown
## Progress
- [x] Added tests for auth module (iteration 1)
- [x] Fixed edge case in token refresh (iteration 2)
- [ ] Still need: rate limiting tests, error boundary tests

## Next Steps
- Focus on rate limiting module next
- The mock setup in tests/helpers.ts can be reused
```

The agent reads this file at iteration start and updates it at iteration end. This bridges the context gap between independent headless invocations.

### CI Failure Recovery

When PR checks fail, the loop automatically:
1. Fetches the failed run ID via `gh run list`
2. Spawns a new headless agent call with CI fix context
3. The agent inspects logs via `gh run view`, fixes code, commits, pushes
4. Re-waits for checks (up to `--ci-retry-max` attempts)

### Completion Signal

The agent can signal "I'm done" by outputting a magic phrase:

```bash
continuous-claude \
  --prompt "Fix all bugs in the issue tracker" \
  --completion-signal "CONTINUOUS_AGENT_PROJECT_COMPLETE" \
  --completion-threshold 3  # Stops after 3 consecutive signals
```

Three consecutive iterations signaling completion stops the loop, preventing wasted runs on finished work.

### Key Configuration

| Flag | Purpose |
|------|---------|
| `--max-runs N` | Stop after N successful iterations |
| `--max-cost $X` | Stop after spending $X |
| `--max-duration 2h` | Stop after time elapsed |
| `--merge-strategy squash` | squash, merge, or rebase |
| `--worktree <name>` | Parallel execution via git worktrees |
| `--disable-commits` | Dry-run mode (no git operations) |
| `--review-prompt "..."` | Add reviewer pass per iteration |
| `--ci-retry-max N` | Auto-fix CI failures (default: 1) |

---

## 5. The De-Sloppify Pattern

**An add-on pattern for any loop.** Add a dedicated cleanup/refactor step after each Implementer step.

### The Problem

When you ask an LLM to implement with TDD, it takes "write tests" too literally:
- Tests that verify TypeScript's type system works (testing `typeof x === 'string'`)
- Overly defensive runtime checks for things the type system already guarantees
- Tests for framework behavior rather than business logic
- Excessive error handling that obscures the actual code

### Why Not Negative Instructions?

Adding "don't test type systems" or "don't add unnecessary checks" to the Implementer prompt has downstream effects:
- The model becomes hesitant about ALL testing
- It skips legitimate edge case tests
- Quality degrades unpredictably

### The Solution: Separate Pass

Instead of constraining the Implementer, let it be thorough. Then add a focused cleanup agent:

```bash
# Step 1: Implement (let it be thorough)
./run-agent.sh "Implement the feature with full TDD. Be thorough with tests."

# Step 2: De-sloppify (separate context, focused cleanup)
./run-agent.sh "Review all changes in the working tree. Remove:
- Tests that verify language/framework behavior rather than business logic
- Redundant type checks that the type system already enforces
- Over-defensive error handling for impossible states
- Console.log statements
- Commented-out code

Keep all business logic tests. Run the test suite after cleanup to ensure nothing breaks."
```

### In a Loop Context

```bash
for feature in "${features[@]}"; do
  # Implement
  ./run-agent.sh "Implement $feature with TDD."

  # De-sloppify
  ./run-agent.sh "Cleanup pass: review changes, remove test/code slop, run tests."

  # Verify
  ./run-agent.sh "Run build + lint + tests. Fix any failures."

  # Commit
  ./run-agent.sh "Commit with message: feat: add $feature"
done
```

### Key Insight

> Rather than adding negative instructions which have downstream quality effects, add a separate de-sloppify pass. Two focused agents outperform one constrained agent.

---

## 6. RFC-Driven DAG Orchestration

**The most sophisticated pattern.** An RFC-driven, multi-agent pipeline that decomposes a spec into a dependency DAG, runs each unit through a tiered quality pipeline, and lands them via an agent-driven merge queue. Created by enitrat (credit: @enitrat) as "Ralphinho".

### Architecture Overview

```
RFC/PRD Document
       │
       ▼
  DECOMPOSITION (AI)
  Break RFC into work units with dependency DAG
       │
       ▼
┌──────────────────────────────────────────────────────┐
│  RALPH LOOP (up to 3 passes)                         │
│                                                      │
│  For each DAG layer (sequential, by dependency):     │
│                                                      │
│  ┌── Quality Pipelines (parallel per unit) ───────┐  │
│  │  Each unit in its own worktree:                │  │
│  │  Research → Plan → Implement → Test → Review   │  │
│  │  (depth varies by complexity tier)             │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  ┌── Merge Queue ─────────────────────────────────┐  │
│  │  Rebase onto main → Run tests → Land or evict │  │
│  │  Evicted units re-enter with conflict context  │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### RFC Decomposition

The orchestrator agent reads the RFC and produces work units:

```typescript
interface WorkUnit {
  id: string;              // kebab-case identifier
  name: string;            // Human-readable name
  rfcSections: string[];   // Which RFC sections this addresses
  description: string;     // Detailed description
  deps: string[];          // Dependencies (other unit IDs)
  acceptance: string[];    // Concrete acceptance criteria
  tier: "trivial" | "small" | "medium" | "large";
}
```

**Decomposition Rules:**
- Prefer fewer, cohesive units (minimize merge risk)
- Minimize cross-unit file overlap (avoid conflicts)
- Keep tests WITH implementation (never separate "implement X" + "test X")
- Dependencies only where real code dependency exists

The dependency DAG determines execution order:
```
Layer 0: [unit-a, unit-b]     ← no deps, run in parallel
Layer 1: [unit-c]             ← depends on unit-a
Layer 2: [unit-d, unit-e]     ← depend on unit-c
```

### Complexity Tiers

Different tiers get different pipeline depths:

| Tier | Pipeline Stages |
|------|----------------|
| **trivial** | implement → test |
| **small** | implement → test → code-review |
| **medium** | research → plan → implement → test → PRD-review + code-review → review-fix |
| **large** | research → plan → implement → test → PRD-review + code-review → review-fix → final-review |

This prevents expensive operations on simple changes while ensuring architectural changes get thorough scrutiny.

### Separate Context Windows (Author-Bias Elimination)

Each stage runs in its own agent process with its own context window. The reviewer never wrote the code it reviews — this eliminates author bias, the most common source of missed issues in self-review.

**Cross-agent tier routing** (A-Wiki cost-pyramid aware):

| Stage | Suggested tier | Why |
|-------|---------------|-----|
| Research | Free / cheap (Gemini Flash, Haiku) | Read-heavy, low reasoning |
| Plan | Primary (Opus-class) | Highest leverage — design correctness |
| Implement | Cheap-capable (Sonnet, Codex) | Mechanical codegen following plan |
| Test | Free / cheap | Run + report |
| PRD Review | Cheap-capable | Spec compliance check |
| Code Review | Primary (Opus-class) | Quality + security gate |
| Review Fix | Cheap-capable | Address review issues |
| Final Review | Primary (Opus-class) | Last gate (large tier only) |

> Map tier names to current models via `python3 scripts/model-scout-current.py` — never hardcode model names (AGENTS.md Cost-First Pyramid).

### Merge Queue with Eviction

After quality pipelines complete, units enter the merge queue:

```
Unit branch
    │
    ├─ Rebase onto main
    │   └─ Conflict? → EVICT (capture conflict context)
    │
    ├─ Run build + tests
    │   └─ Fail? → EVICT (capture test output)
    │
    └─ Pass → Fast-forward main, push, delete branch
```

**File Overlap Intelligence:**
- Non-overlapping units land speculatively in parallel
- Overlapping units land one-by-one, rebasing each time

**Eviction Recovery:**
When evicted, full context is captured (conflicting files, diffs, test output) and fed back to the implementer on the next Ralph pass:

```markdown
## MERGE CONFLICT — RESOLVE BEFORE NEXT LANDING

Your previous implementation conflicted with another unit that landed first.
Restructure your changes to avoid the conflicting files/lines below.

{full eviction context with diffs}
```

### Data Flow Between Stages

```
research.contextFilePath ──────────────────→ plan
plan.implementationSteps ──────────────────→ implement
implement.{filesCreated, whatWasDone} ─────→ test, reviews
test.failingSummary ───────────────────────→ reviews, implement (next pass)
reviews.{feedback, issues} ────────────────→ review-fix → implement (next pass)
final-review.reasoning ────────────────────→ implement (next pass)
evictionContext ───────────────────────────→ implement (after merge conflict)
```

### Worktree Isolation

Every unit runs in an isolated worktree (Ralphinho uses jj/Jujutsu; git worktrees also work):
```
/tmp/workflow-wt-{unit-id}/
```

Pipeline stages for the same unit **share** a worktree, preserving state (context files, plan files, code changes) across research → plan → implement → test → review.

### Key Design Principles

1. **Deterministic execution** — Upfront decomposition locks in parallelism and ordering
2. **Human review at leverage points** — The work plan is the single highest-leverage intervention point
3. **Separate concerns** — Each stage in a separate context window with a separate agent
4. **Conflict recovery with context** — Full eviction context enables intelligent re-runs, not blind retries
5. **Tier-driven depth** — Trivial changes skip research/review; large changes get maximum scrutiny
6. **Resumable workflows** — Full state persisted to SQLite; resume from any point

### When to Use RFC-DAG vs Simpler Patterns

| Signal | Use RFC-DAG | Use Simpler Pattern |
|--------|-------------|-------------------|
| Multiple interdependent work units | Yes | No |
| Need parallel implementation | Yes | No |
| Merge conflicts likely | Yes | No (sequential is fine) |
| Single-file change | No | Yes (sequential pipeline) |
| Multi-day project | Yes | Maybe (continuous-PR) |
| Spec/RFC already written | Yes | Maybe |
| Quick iteration on one thing | No | Yes (NanoClaw or pipeline) |

---

## Choosing the Right Pattern

### Decision Matrix

```
Is the task a single focused change?
├─ Yes → Sequential Pipeline or NanoClaw
└─ No → Is there a written spec/RFC?
         ├─ Yes → Do you need parallel implementation?
         │        ├─ Yes → RFC-Driven DAG
         │        └─ No → Continuous PR Loop
         └─ No → Do you need many variations of the same thing?
                  ├─ Yes → Infinite Agentic Loop
                  └─ No → Sequential Pipeline with de-sloppify
```

### Combining Patterns

These patterns compose well:

1. **Sequential Pipeline + De-Sloppify** — The most common combination. Every implement step gets a cleanup pass.

2. **Continuous PR + De-Sloppify** — Add `--review-prompt` with a de-sloppify directive to each iteration.

3. **Any loop + Verification** — Use `verification-loop` skill as a gate before commits.

4. **RFC-DAG's tiered approach in simpler loops** — Even in a sequential pipeline, you can route simple tasks to a free/cheap model and complex tasks to a primary model:
   ```bash
   # Simple formatting fix
   AGENT=gemini ./run-agent.sh "Fix the import ordering in src/utils.ts"

   # Complex architectural change
   AGENT_FLAGS="--model opus" AGENT=claude ./run-agent.sh "Refactor the auth module to use the strategy pattern"
   ```

---

## Anti-Patterns

### Common Mistakes

1. **Infinite loops without exit conditions** — Always have a max-runs, max-cost, max-duration, or completion signal.

2. **No context bridge between iterations** — Each headless call starts fresh. Use `SHARED_TASK_NOTES.md` or filesystem state to bridge context.

3. **Retrying the same failure** — If an iteration fails, don't just retry. Capture the error context and feed it to the next attempt.

4. **Negative instructions instead of cleanup passes** — Don't say "don't do X." Add a separate pass that removes X.

5. **All agents in one context window** — For complex workflows, separate concerns into different agent processes. The reviewer should never be the author.

6. **Ignoring file overlap in parallel work** — If two parallel agents might edit the same file, you need a merge strategy (sequential landing, rebase, or conflict resolution).

7. **Hardcoding one agent CLI** — A loop that calls `claude -p` in 30 places cannot be cost-routed to Gemini/Codex when Claude is rate-limited or expensive. Always go through a wrapper (§0).

8. **Hardcoding model names** — "Always use Opus" breaks when pricing shifts or a new model drops. Route by tier (free / cheap-capable / primary), resolve to current model via `scripts/model-scout-current.py`.

---

## Cross-Agent Gotchas

| Agent | Gotcha |
|-------|--------|
| **Claude Code** | `--allowedTools` syntax is comma-separated string; rejects unknown tool names silently. |
| **Gemini CLI** | `--approval-mode yolo` is required for unattended writes; default mode prompts and stalls the loop. |
| **Codex** | `exec` subcommand may be renamed across versions — always probe `--help` first. |
| **Aider** | `--yes-always` is mandatory in CI; without it the TUI waits for `<enter>` and hangs the loop. |
| **Hermes** | Reads `lifecycle-config.json` for phase ordering — edits there affect every loop, not just one. |
| **ZCode / Cursor / Windsurf** | No headless CLI — drive via extension API or skip from scripted loops. |
| **All** | Context windows differ; a prompt that fits Claude may overflow Gemini Flash. Keep prompts < 4k chars; offload bulk to files. |

---

## Failure Modes & Recovery

| Symptom | Cause | Recovery |
|---------|-------|----------|
| Loop churn without measurable progress | No acceptance criteria per iteration | Freeze loop; add explicit done-criteria; replay |
| Repeated retries with same root cause | Blind retry instead of context-fed retry | Capture failure context; feed to next attempt |
| Merge queue stalls | Two units with overlapping files both evicted | Serialize overlapping units; parallelize non-overlapping |
| Cost drift from unbounded escalation | No `--max-cost` or tier routing | Set budget; route cheap tiers via §0 wrapper |
| Loop dies on rate limit | One hardcoded agent CLI | Swap via wrapper; fall back to free-tier agent |

**Recovery commands (A-Wiki):**
- `python3 scripts/agent-preflight.py` — portable safety check
- `bash scripts/hermes/sync-all.sh` — sync loop state across devices
- `python3 scripts/model-scout-current.py` — refresh free-tier roster

---

## References

| Project | Author | Link |
|---------|--------|------|
| Ralphinho | enitrat | credit: @enitrat |
| Infinite Agentic Loop | disler | credit: @disler |
| Continuous Claude | AnandChowdhary | credit: @AnandChowdhary |
| NanoClaw | ECC | `/claw` command |
| Verification Loop | ECC | `skills/ecosystem/verification-loop/` |
| Headless CLI flags | claude/gemini `--help` | verified locally 2026-07-25 |

---

## Migration Note (from `autonomous-loops`)

This skill (`continuous-agent-loop` v2.0.0) supersedes `autonomous-loops` (v1.x, ECC origin). All 611 lines of pattern content have been ported here and generalized to be agent-agnostic. The old skill is slimmed to a redirect pointer — do not author new loop guidance there.

If you have scripts calling `autonomous-loops`, they continue to work (the file still exists) but route to this canonical version for any new work.
