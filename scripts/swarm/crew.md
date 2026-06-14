# A-Wiki Swarm Crew — Capability-Role Reference

> **Updated**: 2026-06-14 — switched from model-name bindings to capability-role bindings.
> Model names are now discovered at runtime by `model-scout-current.py`.
> Use `bash scripts/swarm/delegate.sh <task_type> "<prompt>"` — routing is automatic.

---

## Crew Roles (Capability-Based)

| Role | Task Types | Routing | Cost |
|------|-----------|---------|------|
| **Scout** (local) | fts5-search, graph-lookup, file-read | scripts/search-wiki.py, query-graph.py | Free |
| **Navigator** | search, lookup, url | Gemini-flash:free via OpenRouter / direct | Free tier |
| **Archaeologist** | reason, compare, analyze | DeepSeek:free / Qwen3-235b:free | Free tier |
| **Engineer** | scan, lint, execute | Groq/Llama:free (high rate limit) | Free tier |
| **Strategist** | race (parallel winner-takes-first) | All free models in parallel | Free tier |
| **Admiral** (Planner) | planning, validation, wiki synthesis | Primary model (o3/Codex or claude-sonnet) | Paid, last resort |

---

## Routing Rules (enforced by `delegate.sh`)

```
task_type → role → model tier
─────────────────────────────────────────────────
search / lookup / summarize  →  Navigator   →  Tier 1 (free)
reason / compare             →  Archaeologist → Tier 2 (free)
scan                         →  Engineer    →  Tier 3 (free)
race                         →  All roles   →  Tier 0 (parallel free)
```

**Model scout**: `python3 scripts/model-scout-current.py` discovers current live free models.
**Roster update**: `bash scripts/update-model-roster.sh` refreshes `wiki/context/model-roster.conf`.

---

## Crew Aliases (backward compatibility)

Old Sanji's Kitchen names still work in `crew-dispatch.py`:

| Old Name | Role | task_type |
|----------|------|-----------|
| Nami | Navigator | search |
| Robin | Archaeologist | reason |
| Luffy | Engineer | scan |
| Franky | Strategist | race |
| Zoro | Archaeologist | compare |
| Usopp | Navigator | lookup |

---

## AG2 Orchestration (multi-step goals)

```
bash scripts/swarm/goal.sh "<multi-step goal>" --dry-run
```

AG2 Planner (Admiral role) decomposes the goal → dispatches to crew via `delegate.sh`.
See: `docs/protocols/ag2-orchestrator.md`

---

## Key Principles

1. **Local-first**: Scout role uses FTS5/sqlite-vec — zero API cost
2. **Free-first**: Navigator/Archaeologist/Engineer use free tiers; paid only on fallback
3. **Admiral validates**: Primary model reviews all crew outputs — never skipped
4. **Model names are NOT hardcoded**: Scout discovers current best free models at runtime
