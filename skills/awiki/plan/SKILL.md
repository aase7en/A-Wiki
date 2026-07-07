---
name: plan
description: "Telegram /plan command-skill (PLAN phase) — extracts the task from the message, invokes telegram-command-router → persona-orchestrator.py to break work into verifiable tasks. Produces a task breakdown the human reviews before /build. Closes the C4 gap on the live Pi5 bot."
version: 1.0.0
domain: [ai-ops]
lifecycle_phase: plan
category: awiki
agents: [all, hermes]
status: canonical
---

# /plan — Task Breakdown via Telegram

> **Honest limit: LLM-route, ~1000 tokens/call.** Telegram surface for `/plan`.
> Routes to `persona-orchestrator.py --task` (single pass — PLAN decomposes,
> does not fan out). The `quick_commands exec` optimization is blocked by
> Hermes bug #44718.

## When to use

- A `/plan <task>` message lands via the Telegram gateway.
- The user has a spec (from `/spec` or otherwise) and wants it broken into
  verifiable, ordered tasks before implementation.
- The lifecycle router is in the PLAN phase.

## What it does

1. **Extract** the task from the message (everything after `/plan`).
2. **Invoke** the router:
   ```
   bash scripts/hermes/telegram-command-router.sh --command plan --message "<task>" --apply
   ```
3. The orchestrator produces a task breakdown (single LLM pass).
4. **Return** the breakdown to Telegram for human review.

## How to invoke

### Via Telegram

```
/plan break down the task management API into implementable slices
/plan decompose the JWT auth migration
```

### Via CLI

```bash
bash scripts/hermes/telegram-command-router.sh --message "/plan break down the API" --apply
```

## Output format

Return the breakdown verbatim, markdown-formatted:

```
🗂️ Plan: "break down the task management API"

1. [DEFINE] Confirm data model (Task, List, User)
2. [BUILD] Set up Express + Postgres scaffold
   - test: healthcheck endpoint
3. [BUILD] CRUD for Task
   - test: create/read/update/delete
…
```

## Honest limits

- ❌ **Draft, not schedule.** The breakdown is a draft; the human reorders,
  splits, or drops tasks before `/build`.
- ❌ **Single LLM pass.** PLAN does not fan out. The decomposition reflects
  one model's view.
- ❌ **No dependency graph.** The output is an ordered list, not a DAG. If the
  user needs dependency analysis, redirect to the dev-box lifecycle router.

## Files

| File | Purpose |
|---|---|
| `scripts/hermes/telegram-command-router.py` | Pure router + CLI (Phase 1) |
| `scripts/hermes/persona-orchestrator.py` | Single-pass task runner (Chunk B) |
| `scripts/hermes/telegram-commands.json` | Route map: `/plan` → orchestrator, phase=plan |

## See also

- `skills/awiki/{spec,build,review,ship}/SKILL.md` — sibling lifecycle command-skills
- `skills/engineering-lifecycle/plan/planning-and-task-breakdown/SKILL.md` — the canonical PLAN skill
- `docs/architecture/hermes-cross-agent-handoff.md` §"Follow-up chunk proposal (chunk hermes-e)"
