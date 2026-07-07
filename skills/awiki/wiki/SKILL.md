---
name: wiki
description: "Telegram /wiki command-skill — extracts the user's query from the message, invokes telegram-command-router → search-wiki.py (A-Wiki FTS5 local index), and returns the top 5 hits as path + title + snippet. Closes the C4 gap: /wiki returned 'Unknown command' on the live Pi5 bot. Use this when a /wiki <query> message lands via the Telegram gateway."
version: 1.0.0
domain: [wiki]
lifecycle_phase: none
category: awiki
agents: [all, hermes]
status: canonical
---

# /wiki — A-Wiki FTS5 Search via Telegram

> **Honest limit: LLM-route, ~1000 tokens/call.** This skill is the reliable
> Telegram surface for `/wiki` today (Hermes auto-exposes every skill dir as
> `/<dirname>`). The zero-LLM optimization (`quick_commands type:exec`) is
> blocked by upstream Hermes bug #44718 (the `{args}` placeholder never
> substitutes); it will swap in once that bug is fixed in the container's
> Hermes version. Until then, this skill costs ~1000 free-tier tokens per
> `/wiki` call.

## When to use

- A `/wiki <query>` message lands via the Telegram gateway (the canonical
  trigger — this skill IS the `/wiki` command surface).
- The user wants to find A-Wiki pages that mention a keyword, topic, or
  phrase (e.g. "mqtt broker", "esp32 temperature", "supabase auth").

This is **Level -1** of the Cost Pyramid — local FTS5, free, offline, no
network. Cheaper than any free API model.

## What it does

1. **Extract** the query from the Telegram message (everything after `/wiki`).
2. **Invoke** the router, which shells out to `search-wiki.py --json --limit 5`:
   ```
   bash scripts/hermes/telegram-command-router.sh --command wiki --message "<query>" --apply
   ```
3. **Return** the JSON hits formatted for Telegram: one block per hit with
   path (clickable), title, and a short snippet. Truncate to ~1500 chars total
   so the reply fits one Telegram message (4096-char cap).

If the router returns `[error: ...]`, surface it verbatim — do not fabricate
results. An empty result list means the query matched nothing; say so plainly.

## How to invoke

### Via Telegram (the intended surface)

```
/wiki mqtt broker
/wiki "home assistant"
/wiki supabase --field title
```

The gateway maps `/wiki` → this skill (auto-exposed from the skill dir name).
You extract the query and call the router.

### Via CLI (Pi5 or dev box — dry-run first, then apply)

```bash
# Dry-run: see the route, no script call (default, CI-safe).
bash scripts/hermes/telegram-command-router.sh --message "/wiki mqtt broker"

# Run for real (calls search-wiki.py, prints JSON).
bash scripts/hermes/telegram-command-router.sh --message "/wiki mqtt broker" --apply
```

## Output format (what to send back to Telegram)

Format the router's JSON output (a list of `{path, title, snippet, score}`)
as compact markdown blocks:

```
📚 A-Wiki: "mqtt broker" (5 hits)

1. wiki/sources/iot/mqtt-protocol-overview.md
   MQTT Protocol Overview
   …central «broker». «MQTT» v5.0 adds session expiry…

2. wiki/entities/iot/mosquitto.md
   Eclipse Mosquitto
   «MQTT» «Broker» (Open Source)…
```

Drop the `score` field (BM25 internal). Keep the `«»` highlight guillemets —
they mark the matched terms. Truncate snippets to ~150 chars each.

## Honest limits

- ❌ **LLM-route cost**: ~1000 free-tier tokens per call (router + LLM
  extract). Acceptable on the Pi5 free-tier pool; the `quick_commands exec`
  optimization is tracked for when bug #44718 is fixed.
- ❌ **Thai/special-char queries**: the LLM must pass the query to the router
  verbatim (one argv element). Do not transliterate or "normalize" Thai.
- ❌ **Index may be stale**: `search-wiki.py` auto-builds `.wiki-index.db` if
  missing, but recent wiki edits may not be indexed until the next
  `gen-index.py` run. A stale index still searches; it just misses new pages.
- ❌ **Not for synthesis questions**: `/wiki` is keyword lookup. For
  cross-file synthesis use `ask-notebooklm` (the LLM should redirect the user).

## Files

| File | Purpose |
|---|---|
| `scripts/hermes/telegram-command-router.py` | Pure router + CLI (Phase 1) |
| `scripts/hermes/telegram-command-router.sh` | POSIX wrapper |
| `scripts/hermes/telegram-commands.json` | Route map: `/wiki` → search-wiki.py |
| `scripts/wiki/search-wiki.py` | FTS5 search backend (Level -1, free) |
| `tests/test_telegram_command_router.py` | 22 unit tests (CI-safe) |

## See also

- `skills/awiki/search/SKILL.md` — `/search` alias of this skill
- `docs/architecture/hermes-cross-agent-handoff.md` §"Follow-up chunk proposal (chunk hermes-e)"
- `docs/runbooks/hermes-raspberry-pi5.md` §"Slash Commands"
- `skills/wiki/wiki-search-local/SKILL.md` — the underlying FTS5 query syntax reference
