---
name: spec
description: "Telegram /spec command-skill (DEFINE phase) — extracts the task from the message, invokes telegram-command-router → persona-orchestrator.py to draft a specification before code. Forces the Iron Law #1 discipline (spec before implementation). Closes the C4 gap on the live Pi5 bot."
version: 1.0.0
domain: [ai-ops]
lifecycle_phase: define
category: awiki
agents: [all, hermes]
status: canonical
---

# /spec — Define Requirements via Telegram

> **Honest limit: LLM-route, ~1000 tokens/call.** This skill is the Telegram
> surface for `/spec`. It routes to `persona-orchestrator.py --task` (single
> pass, not fan-out — DEFINE is a drafting phase). The `quick_commands exec`
> optimization is blocked by Hermes bug #44718.

## When to use

- A `/spec <task>` message lands via the Telegram gateway.
- The user wants to write a specification / requirements doc **before** code
  (the Iron Law #1 discipline: no production code without a spec for
  non-trivial changes).
- The lifecycle router is in the DEFINE phase and needs a spec artifact.

## What it does

1. **Extract** the task from the message (everything after `/spec`).
2. **Invoke** the router, which shells out to `persona-orchestrator.py --task`:
   ```
   bash scripts/hermes/telegram-command-router.sh --command spec --message "<task>" --apply
   ```
3. The orchestrator drafts a specification (single LLM pass — no fan-out at
   this phase; fan-out is reserved for `/review` and `/ship`).
4. **Return** the draft spec to Telegram for human review.

## How to invoke

### Via Telegram

```
/spec build a REST API for task management
/spec add JWT auth to the existing Express app
```

### Via CLI

```bash
# Dry-run (default, CI-safe).
bash scripts/hermes/telegram-command-router.sh --message "/spec build a REST API"

# Run for real.
bash scripts/hermes/telegram-command-router.sh --message "/spec build a REST API" --apply
```

## Output format

Return the orchestrator's output verbatim (the drafted spec), formatted as
markdown. Typical shape:

```
📋 Spec: "build a REST API for task management"

## Goal
…
## Requirements
- …
## Out of scope
- …
## Acceptance criteria
- …
```

Truncate to ~3500 chars if the spec is long; offer to send the rest.

## Honest limits

- ❌ **Draft, not contract.** The spec is a draft for human review. The human
  approves it before `/plan` or `/build` proceeds.
- ❌ **Single LLM pass.** DEFINE does not fan out (no `code-reviewer` etc.
  here — that happens at `/review` and `/ship`). The draft reflects one
  model's view; expect to iterate.
- ❌ **Read-only A-Wiki on Pi5.** The spec is returned to chat, not committed
  to the repo. The human commits it if they want it durable.

## Files

| File | Purpose |
|---|---|
| `scripts/hermes/telegram-command-router.py` | Pure router + CLI (Phase 1) |
| `scripts/hermes/persona-orchestrator.py` | Single-pass task runner (Chunk B) |
| `scripts/hermes/telegram-commands.json` | Route map: `/spec` → orchestrator, phase=spec |

## See also

- `skills/awiki/{plan,build,review,ship}/SKILL.md` — the rest of the lifecycle
- `skills/engineering-lifecycle/define/spec-driven-development/SKILL.md` — the canonical DEFINE skill
- `docs/architecture/hermes-cross-agent-handoff.md` §"Follow-up chunk proposal (chunk hermes-e)"
