---
name: search
description: "Telegram /search command-skill — wiki FTS5 search alias of /wiki. Extracts the query, invokes telegram-command-router → search-wiki.py, returns the top 5 hits. Same backend as /wiki; provided as a separate slash command because users type /search by habit. Closes the C4 gap on the live Pi5 bot."
version: 1.0.0
domain: [wiki]
lifecycle_phase: none
category: awiki
agents: [all, hermes]
status: canonical
---

# /search — Wiki Search Alias via Telegram

> **Honest limit: LLM-route, ~1000 tokens/call.** Identical backend to `/wiki`;
> this is a separate slash command only because users type `/search` by habit.
> See `skills/awiki/wiki/SKILL.md` for the full honest-limit rationale (the
> `quick_commands exec` optimization is blocked by Hermes bug #44718).

## When to use

- A `/search <query>` message lands via the Telegram gateway.
- The user is looking for A-Wiki pages matching a keyword/phrase.

Functionally identical to `/wiki`. Same FTS5 backend, same output format.

## What it does

1. **Extract** the query from the message (everything after `/search`).
2. **Invoke** the router:
   ```
   bash scripts/hermes/telegram-command-router.sh --command search --message "<query>" --apply
   ```
3. **Return** the JSON hits formatted for Telegram (same format as `/wiki`).

The router routes both `/wiki` and `/search` to `scripts/wiki/search-wiki.py`
(see `telegram-commands.json`). The two skills exist as separate Telegram
commands so the user's habit (`/search`) works alongside the canonical name
(`/wiki`).

## How to invoke

### Via Telegram

```
/search mqtt broker
/search "home assistant"
```

### Via CLI

```bash
# Dry-run (default).
bash scripts/hermes/telegram-command-router.sh --message "/search mqtt broker"

# Run for real.
bash scripts/hermes/telegram-command-router.sh --message "/search mqtt broker" --apply
```

## Output format

Same as `/wiki` — see `skills/awiki/wiki/SKILL.md` §"Output format".

## Honest limits

Same as `/wiki` — see `skills/awiki/wiki/SKILL.md` §"Honest limits".

## Files

| File | Purpose |
|---|---|
| `scripts/hermes/telegram-command-router.py` | Pure router + CLI (Phase 1) |
| `scripts/hermes/telegram-commands.json` | Route map: `/search` → search-wiki.py |
| `scripts/wiki/search-wiki.py` | FTS5 search backend |
| `skills/awiki/wiki/SKILL.md` | Canonical `/wiki` skill (this is its alias) |

## See also

- `skills/awiki/wiki/SKILL.md` — the canonical `/wiki` command (full details)
- `docs/architecture/hermes-cross-agent-handoff.md` §"Follow-up chunk proposal (chunk hermes-e)"
