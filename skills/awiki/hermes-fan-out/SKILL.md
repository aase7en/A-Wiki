---
name: hermes-fan-out
description: "Sequential persona fan-out for Hermes — realizes multi-perspective review (code-reviewer, test-engineer, security-auditor) as a sequence of hermes chat calls since Hermes has no native concurrency. Use for /review tasks via Telegram or CLI when you want the same multi-angle scrutiny Claude Code gets from subagents."
version: 1.0.0
domain: [ai-ops]
lifecycle_phase: meta
category: swarm
agents: [all, hermes]
status: canonical
---

# Hermes Sequential Fan-Out

> **Honest limit: SEQUENTIAL, not parallel.** Hermes has no native subagent /
> fan-out capability. This skill emulates "fan-out" by running one
> `hermes chat -q --persona <name>` call per persona, **in sequence**, then
> merging the outputs into a single triaged report. There is no concurrency,
> by framework design — and on free-tier Pi5 models (15-30 RPM) sequential is
> also the only realistic option.

## When to use

- A `/review <task>` lands via Telegram and you want multi-perspective scrutiny
  (the same 3-persona fan-out Claude Code gets from subagents).
- You're about to SHIP and the lifecycle router requires a review gate before
  the SHIP phase (`lifecycle-config.json` shortcut_blocklist:
  `skip_review_before_ship`).
- You want a second/third perspective without leaving the Hermes chat.

## What it does

Given a task, the orchestrator runs each persona in `parallel_fan_out`
(default: `code-reviewer`, `test-engineer`, `security-auditor` from
`lifecycle-config.json`) sequentially:

```
hermes chat -q --persona code-reviewer  "$TASK"
hermes chat -q --persona test-engineer  "$TASK"
hermes chat -q --persona security-auditor "$TASK"
```

It sleeps `--sleep` seconds (default 4s) **between** calls (not after the
last) to respect free-tier rate limits, captures each output, and merges them
into one report sorted by severity:

```
## CRITICAL (2)
- [security-auditor] SQL injection in login()
- [code-reviewer] unhandled None return path
## IMPORTANT (1)
- [test-engineer] missing edge case for empty input
## OTHER (3)
...
```

## How to invoke

### Via Telegram (the intended surface)

```
/review review the auth refactor for security and correctness
```

The Telegram gateway maps `/review` to this skill, which calls the orchestrator.

### Via CLI (Pi5 or dev box)

```bash
# Dry-run: see the plan, no Hermes call (default, CI-safe).
bash scripts/hermes/persona-orchestrator.sh --task "review PR #42"

# Override the personas.
bash scripts/hermes/persona-orchestrator.sh \
    --personas code-reviewer,test-engineer \
    --task "review PR #42"

# Run for real (sequential hermes chat calls).
bash scripts/hermes/persona-orchestrator.sh --apply --task "review PR #42"

# Get the final report as JSON.
bash scripts/hermes/persona-orchestrator.sh --apply --json --task "..."
```

## Design principles (adapted from Dan Martell's Replacement Ladder)

This skill borrows operational discipline from the "Replacement Ladder"
playbook, even though that book is about human roles (admin/COO/marketing)
not technical fan-out:

| Playbook principle | How this skill applies it |
|---|---|
| **Draft, do not send** | The orchestrator produces a *draft* report. The human reviews and adds the final 10-20% before acting on anything. Nothing auto-ships. |
| **One sharp question, not a guess** | Each persona is told (via its `agents/*.md` system prompt) to ask one clarifying question when unsure rather than fabricate. |
| **Triage + merge** (Admin sorts Urgent/Delegate/FYI) | Outputs are bucketed by severity (`critical`/`important`/`low`) and sorted, mirroring an inbox triage. |
| **"Act without asking" low-stakes / ask on high-stakes** | `--dry-run` (default) never calls Hermes — safe to run anywhere. `--apply` is the high-stakes path that actually consumes rate limit. |
| **Personal Preference Handbook** (shared brain) | Hermes already loads `SOUL.md` + `MEMORY.md` + `USER.md` at startup. Personas inherit that context — they sound like *you*, not a generic AI, because the shared brain is already in context. |

## Honest limits

- ❌ **No concurrency.** This is sequential by necessity (Hermes framework has
  no fan-out primitive). A 3-persona pass on free-tier takes ~3 model calls +
  2 sleeps = at least ~30-60s wall-clock depending on model latency.
- ❌ **No native subagent discovery.** Personas are loaded from
  `agents/*.md` and named in `lifecycle-config.json`'s `parallel_fan_out`.
- ❌ **Read-only A-Wiki mount on Pi5.** The orchestrator cannot commit review
  findings back to the repo; it only reports them to chat/Telegram.
- ❌ **Rate-limit bound.** Free-tier (15-30 RPM) means aggressive `/review`
  storms will throttle. The default `--sleep 4` is tuned for this; raise it
  if you see 429s.

## Files

| File | Purpose |
|---|---|
| `scripts/hermes/persona-orchestrator.py` | Python module — pure logic (`build_plan`, `run`, `merge_report`) + CLI |
| `scripts/hermes/persona-orchestrator.sh` | Thin POSIX wrapper (python3 → python → py -3 fallback) |
| `tests/test_persona_orchestrator.py` | Unit tests (16, all pure — no subprocess, no Hermes call) |
| `scripts/hermes/lifecycle-config.json` | Source of `parallel_fan_out` persona list |
| `agents/code-reviewer.md`, `agents/test-engineer.md`, `agents/security-auditor.md` | Persona definitions |

## See also

- `docs/architecture/hermes-cross-agent-handoff.md` (Chunk B — this skill)
- `docs/architecture/skill-architecture-plan.md` (parent 5-layer contract)
- `docs/runbooks/hermes-raspberry-pi5.md` (live Pi5 verification — Chunk C)
