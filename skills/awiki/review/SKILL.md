---
name: review
description: "Telegram /review command-skill (REVIEW phase) — extracts the task from the message, invokes telegram-command-router → persona-orchestrator.py for sequential multi-persona review (code-reviewer, test-engineer, security-auditor), returns the merged severity-sorted report. Closes the C4 gap on the live Pi5 bot."
version: 1.0.0
domain: [ai-ops]
lifecycle_phase: review
category: awiki
agents: [all, hermes]
status: canonical
---

# /review — Sequential Persona Review via Telegram

> **Honest limit: LLM-route, ~1000 tokens/call (outer) + 3 hermes chat calls
> (inner).** This skill is the Telegram surface for `/review`. The inner
> persona fan-out is sequential (Hermes has no native concurrency — see
> `skills/awiki/hermes-fan-out/SKILL.md`). A 3-persona pass on free-tier
> takes ~30-60s wall-clock. The `quick_commands exec` optimization is blocked
> by Hermes bug #44718.

## When to use

- A `/review <task>` message lands via the Telegram gateway.
- The user wants multi-perspective scrutiny of code, a design, or a change
  (the same 3-persona fan-out Claude Code gets from subagents).
- You are about to SHIP and the lifecycle router requires a review gate
  before the SHIP phase (`lifecycle-config.json` shortcut_blocklist:
  `skip_review_before_ship`).

## What it does

1. **Extract** the task from the message (everything after `/review`).
2. **Invoke** the router, which shells out to `persona-orchestrator.py --task`:
   ```
   bash scripts/hermes/telegram-command-router.sh --command review --message "<task>" --apply
   ```
3. The orchestrator runs each persona in `parallel_fan_out` (default:
   `code-reviewer`, `test-engineer`, `security-auditor` from
   `lifecycle-config.json`) **sequentially**, sleeping ~4s between calls:
   ```
   hermes chat -q --persona code-reviewer    "<task>"
   hermes chat -q --persona test-engineer    "<task>"
   hermes chat -q --persona security-auditor "<task>"
   ```
4. **Merge** the outputs into one severity-sorted report (critical → important
   → low → other) and return it to Telegram.

## How to invoke

### Via Telegram (the intended surface)

```
/review review the auth refactor for security and correctness
/review check this PR for bugs and test coverage
```

### Via CLI (Pi5 or dev box)

```bash
# Dry-run: see the route, no orchestrator call (default, CI-safe).
bash scripts/hermes/telegram-command-router.sh --message "/review review PR #42"

# Run for real (sequential persona fan-out — ~30-60s on free-tier).
bash scripts/hermes/telegram-command-router.sh --message "/review review PR #42" --apply
```

To override the persona set or sleep interval, call the orchestrator directly
(the router is a thin dispatcher):

```bash
bash scripts/hermes/persona-orchestrator.sh \
    --personas code-reviewer,security-auditor \
    --task "review PR #42" --apply
```

## Output format (what to send back to Telegram)

Forward the orchestrator's merged report verbatim, truncated to ~3500 chars:

```
🔍 Review: "review the auth refactor" (3 personas)

## CRITICAL (2)
- [security-auditor] SQL injection in login()
- [code-reviewer] unhandled None return path
## IMPORTANT (1)
- [test-engineer] missing edge case for empty input
## OTHER (3)
…
```

If the report is longer than one Telegram message, send the CRITICAL +
IMPORTANT sections first, then offer to send the rest.

## Honest limits

- ❌ **Sequential, not parallel.** Hermes has no native fan-out. A 3-persona
  pass = 3 model calls + 2 sleeps = ~30-60s wall-clock on free-tier.
- ❌ **Double LLM cost.** This skill (outer LLM extracts the task) + the
  orchestrator (3 inner hermes chat calls). Acceptable on free-tier for
  high-value review; avoid spamming `/review`.
- ❌ **Rate-limit bound.** Free-tier (15-30 RPM) means aggressive `/review`
  storms will throttle. The default `--sleep 4` is tuned for this.
- ❌ **Read-only A-Wiki on Pi5.** The orchestrator cannot commit review
  findings back to the repo; it only reports them to chat/Telegram.
- ❌ **Draft, not verdict.** The report is a draft for human review — the
  human adds the final 10-20% before acting. Nothing auto-ships.

## Files

| File | Purpose |
|---|---|
| `scripts/hermes/telegram-command-router.py` | Pure router + CLI (Phase 1) |
| `scripts/hermes/persona-orchestrator.py` | Sequential fan-out backend (Chunk B) |
| `scripts/hermes/telegram-commands.json` | Route map: `/review` → orchestrator, phase=review |
| `scripts/hermes/lifecycle-config.json` | `parallel_fan_out` persona list |
| `agents/code-reviewer.md`, `agents/test-engineer.md`, `agents/security-auditor.md` | Persona definitions |

## See also

- `skills/awiki/hermes-fan-out/SKILL.md` — the fan-out mechanism (Chunk B)
- `skills/awiki/{spec,plan,build,ship}/SKILL.md` — sibling lifecycle command-skills
- `docs/architecture/hermes-cross-agent-handoff.md` §"Follow-up chunk proposal (chunk hermes-e)"
- `docs/runbooks/hermes-raspberry-pi5.md` §"Slash Commands"
