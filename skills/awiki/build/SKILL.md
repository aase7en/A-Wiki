---
name: build
description: "Telegram /build command-skill (BUILD phase) — extracts the task from the message, invokes telegram-command-router → persona-orchestrator.py for incremental implementation + TDD guidance. Emphasizes slice-by-slice with a failing test first (Iron Law #1). Closes the C4 gap on the live Pi5 bot."
version: 1.0.0
domain: [ai-ops]
lifecycle_phase: build
category: awiki
agents: [all, hermes]
status: canonical
---

# /build — Incremental Implementation via Telegram

> **Honest limit: LLM-route, ~1000 tokens/call.** Telegram surface for `/build`.
> Routes to `persona-orchestrator.py --task` (single pass — BUILD implements,
> does not fan out). The `quick_commands exec` optimization is blocked by
> Hermes bug #44718. **Note: this skill drafts implementation guidance; it
> cannot write files on the Pi5 (read-only A-Wiki mount).**

## When to use

- A `/build <task>` message lands via the Telegram gateway.
- The user wants incremental implementation guidance for a slice of work
  (slice-by-slice, with a failing test first).
- The lifecycle router is in the BUILD phase.

## What it does

1. **Extract** the task from the message (everything after `/build`).
2. **Invoke** the router:
   ```
   bash scripts/hermes/telegram-command-router.sh --command build --message "<task>" --apply
   ```
3. The orchestrator drafts implementation guidance (single LLM pass),
   emphasizing: write the failing test first → implement the minimum to pass
   → refactor.
4. **Return** the guidance to Telegram for the human to act on (on a real
   dev box, not the Pi5).

## How to invoke

### Via Telegram

```
/build implement the Task CRUD endpoints with tests
/build add the JWT middleware, test-first
```

### Via CLI

```bash
bash scripts/hermes/telegram-command-router.sh --message "/build implement Task CRUD" --apply
```

## Output format

Return the guidance verbatim, markdown-formatted:

```
🔧 Build: "implement the Task CRUD endpoints with tests"

## Slice 1: Task model + create endpoint
1. Write failing test: `POST /tasks` returns 201 with body
2. Implement: model migration + route handler
3. Run test → green
4. Refactor: extract validation
…
```

## Honest limits

- ❌ **Guidance only — cannot write code on Pi5.** The Pi5 A-Wiki mount is
  read-only. This skill drafts the steps; the human executes them on a dev
  box. Do not claim the code is "written" — it's a plan.
- ❌ **Single LLM pass.** BUILD does not fan out. Multi-perspective scrutiny
  happens at `/review`.
- ❌ **No test execution.** The orchestrator cannot run the user's test suite.
  It describes the test to write; the human runs it.

## Files

| File | Purpose |
|---|---|
| `scripts/hermes/telegram-command-router.py` | Pure router + CLI (Phase 1) |
| `scripts/hermes/persona-orchestrator.py` | Single-pass task runner (Chunk B) |
| `scripts/hermes/telegram-commands.json` | Route map: `/build` → orchestrator, phase=build |

## See also

- `skills/awiki/{spec,plan,review,ship}/SKILL.md` — sibling lifecycle command-skills
- `skills/engineering-lifecycle/build/incremental-implementation/SKILL.md` — the canonical BUILD skill
- `skills/engineering-lifecycle/build/test-driven-development/SKILL.md` — TDD discipline
- `docs/architecture/hermes-cross-agent-handoff.md` §"Follow-up chunk proposal (chunk hermes-e)"
