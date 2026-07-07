---
name: ship
description: "Telegram /ship command-skill (SHIP phase) — extracts the task from the message, invokes telegram-command-router → persona-orchestrator.py for the pre-launch checklist + parallel persona review gate. The SHIP phase fans out (code-reviewer, test-engineer, security-auditor) before sign-off. Closes the C4 gap on the live Pi5 bot."
version: 1.0.0
domain: [ai-ops]
lifecycle_phase: ship
category: awiki
agents: [all, hermes]
status: canonical
---

# /ship — Launch Gate via Telegram

> **Honest limit: LLM-route, ~1000 tokens/call (outer) + 3 hermes chat calls
> (inner fan-out).** This skill is the Telegram surface for `/ship`. SHIP is
> the second phase (after `/review`) that fans out — it runs the pre-launch
> checklist AND the 3-persona review gate before sign-off. Sequential, ~30-60s
> on free-tier. The `quick_commands exec` optimization is blocked by Hermes
> bug #44718.

## When to use

- A `/ship <task>` message lands via the Telegram gateway.
- The user believes the work is done and wants the launch gate: pre-launch
  checklist + parallel persona review.
- The lifecycle router requires a review before SHIP
  (`lifecycle-config.json` shortcut_blocklist: `skip_review_before_ship`).

## What it does

1. **Extract** the task from the message (everything after `/ship`).
2. **Invoke** the router, which shells out to `persona-orchestrator.py --task`:
   ```
   bash scripts/hermes/telegram-command-router.sh --command ship --message "<task>" --apply
   ```
3. The orchestrator runs the SHIP-phase fan-out: pre-launch checklist
   (versioning, rollback plan, observability) + the 3 personas
   (`code-reviewer`, `test-engineer`, `security-auditor`) **sequentially**.
4. **Merge** into one severity-sorted report and return it to Telegram.

The output is a **gate decision**: SHIP (no critical/important findings) or
HOLD (fix the findings first). The human makes the final call.

## How to invoke

### Via Telegram

```
/ship ship the auth refactor to production
/ship release v2.1.0 of the task API
```

### Via CLI

```bash
# Dry-run (default).
bash scripts/hermes/telegram-command-router.sh --message "/ship ship the auth refactor"

# Run for real (sequential fan-out — ~30-60s on free-tier).
bash scripts/hermes/telegram-command-router.sh --message "/ship ship the auth refactor" --apply
```

## Output format

Forward the merged report verbatim, with a gate decision line at the top:

```
🚢 Ship gate: "ship the auth refactor" (3 personas)

**Recommendation: HOLD** — 2 critical findings must be fixed first.

## Pre-launch checklist
- [x] Version bumped
- [x] Rollback plan documented
- [ ] Observability dashboard updated  ← gap

## CRITICAL (2)
- [security-auditor] JWT secret rotation not implemented
- [code-reviewer] rate-limit middleware missing
## IMPORTANT (1)
- [test-engineer] no integration test for token refresh
```

## Honest limits

- ❌ **Sequential fan-out.** SHIP fans out like `/review` — 3 model calls +
  sleeps = ~30-60s wall-clock. Hermes has no native concurrency.
- ❌ **Recommendation, not authority.** The gate decision is advisory. The
  human owns the final ship/hold call.
- ❌ **Draft, not deployment.** This skill produces a review report; it cannot
  deploy, tag a release, or merge a PR. The human does that on a dev box.
- ❌ **Read-only A-Wiki on Pi5.** Findings are returned to chat, not committed.

## Files

| File | Purpose |
|---|---|
| `scripts/hermes/telegram-command-router.py` | Pure router + CLI (Phase 1) |
| `scripts/hermes/persona-orchestrator.py` | Sequential fan-out backend (Chunk B) |
| `scripts/hermes/telegram-commands.json` | Route map: `/ship` → orchestrator, phase=ship |
| `scripts/hermes/lifecycle-config.json` | `parallel_fan_out` persona list + `skip_review_before_ship` blocklist |
| `agents/code-reviewer.md`, `agents/test-engineer.md`, `agents/security-auditor.md` | Persona definitions |

## See also

- `skills/awiki/review/SKILL.md` — the other fan-out phase (REVIEW)
- `skills/awiki/hermes-fan-out/SKILL.md` — the fan-out mechanism (Chunk B)
- `skills/engineering-lifecycle/ship/shipping-and-launch/SKILL.md` — the canonical SHIP skill
- `docs/architecture/hermes-cross-agent-handoff.md` §"Follow-up chunk proposal (chunk hermes-e)"
- `docs/runbooks/hermes-raspberry-pi5.md` §"Slash Commands"
