# scripts/batch/ — Universal Cost-Aware Ingest Harness

Single entry point that **every** A-Wiki agent (Claude Code, Codex, Gemini CLI, Cursor, Windsurf, Cline, Copilot, Aider) uses for source ingestion. Routes work to the cheapest tier that still passes quality gates, never hardcodes prices or model names.

```
raw/<file>   →   route.py   →   tier 0/1/2/3 adapter   →   wiki/sources/<slug>.md
                     │
                     ▼
            cost-routing.conf  ←  scout.py  (refreshes free roster + prices)
```

## Why this exists

- Direct LLM calls in each agent scatter cost and bypass batch discounts. One harness = one price/model knob.
- Tier discounts (OpenAI Batch 50% off, Anthropic Batch 50% off) need a queue/poll/collect cycle. Each agent re-implementing that is wasted work and bugs.
- Free models drop weekly. The scout job refreshes the roster instead of stale hardcoded names.

## Tiers (DYNAMIC — see `wiki/context/cost-routing.conf` for live values)

| Tier | Backend | Mode | When |
|------|---------|------|------|
| 00 | Primary agent subscription | realtime | Planning, bugfix, validation — primary agent decides; harness never auto-routes here |
| 0 | OpenRouter free / Gemini Flash | realtime | Trivial single-file ASCII work (complexity_classifier picks this) |
| 1 | DeepSeek V4-Flash-Base | realtime | Default ingest 1-20 files |
| 2 | OpenAI GPT-4o-mini batch | batch (24h) | Backlog > 20 files, input-heavy |
| 3 | Anthropic Haiku 4.5 batch | batch (24h) | Quality escalation after Tier 1/2 fails the gate |

Selection logic: `router.select_tier()`. Override with `--tier N`, `--backend X`, or env vars `A_WIKI_ROUTE_TIER` / `A_WIKI_BACKEND`.

## Surfaces

```bash
# Surface 1 — CLI (any agent that can run a subprocess)
python scripts/batch/route.py --domain ai-tools --limit 50
python scripts/batch/route.py --estimate --limit 100
python scripts/batch/route.py --tier 1 --file raw/foo.md

# Surface 2 — Shell wrappers (per-OS native)
bash scripts/batch/route.sh --limit 50               # mac / linux / wsl / git bash
powershell scripts\batch\route.ps1 -Tier 1 -File raw\foo.md   # windows native
scripts\batch\route.cmd --tier 1 --file raw\foo.md   # cmd.exe shim

# Surface 3 — MCP tools (Claude Code, Cursor, Windsurf, Cline)
#   wiki_ingest_route(tier=1, domain="ai-tools", limit=50)
#   wiki_batch_status(batch_id="...")
#   wiki_batch_collect(batch_id="...")

# Surface 4 — ENV overrides (CI / scheduled tasks)
A_WIKI_ROUTE_TIER=2 python scripts/batch/route.py --limit 100
A_WIKI_BACKEND=openai python scripts/batch/route.py --limit 100
```

## Lifecycle

```
1. SUBMIT     route.py            picks tier, builds requests, dispatches
                                  ├─ Tier 0/1: returns results inline
                                  └─ Tier 2/3: returns batch_id, persists state.jsonl

2. POLL       poll.py             refreshes pending batches from provider
                                  (manual — no daemon; run after a few hours)

3. COLLECT    collect.py          downloads completed batch, validates,
                                  writes wiki/sources/<slug>.md,
                                  runs gen-index.py, appends log.md
```

State lives in `drive/batch-state/` (cloud-synced, gitignored). Cross-device: submit on one machine, collect on another — same state.

## Quality + enforcement

- `quality_gate.py` validates every output against the source provenance hook before writing. Failed outputs are skipped (not written) and listed in the run summary — re-route on a higher tier.
- `scripts/hooks/check_harness_routing.py` blocks any direct Write/Edit to `wiki/sources/<slug>.md` that lacks `routed_via: harness@v\d+`. Bypass intentionally allowed only with `HOOK_SKIP=check_harness_routing` (emergency).
- All adapter outputs carry `routed_via: harness@v1` plus the existing `original_file: raw/<slug>.md` required by `check_source_original_file.py`.

## Scout — keep the cost matrix fresh

```bash
python scripts/batch/scout.py --refresh     # pull OpenRouter free list
python scripts/batch/scout.py --show        # list cached free models
python scripts/batch/scout.py --benchmark <model-id>   # validate a candidate
python scripts/batch/scout.py --propose     # write cost-routing.conf.proposed
python scripts/batch/scout.py --apply       # after user reviews diff
```

The scout runs as the primary agent's subscription work (Tier 00) — marginal cost zero. Run weekly or whenever a new free model lands.

## File map

```
scripts/batch/
├── __init__.py
├── route.py                 CLI entry (Surface 1)
├── route.sh                 POSIX wrapper (Surface 2)
├── route.ps1                PowerShell wrapper (Surface 2)
├── route.cmd                cmd.exe shim (Surface 2)
├── router.py                Tier selection + dispatch (engine)
├── config.py                Read cost-routing.conf + ENV
├── state.py                 JSONL state on drive/batch-state/
├── prompt_template.py       Shared system + user prompt
├── quality_gate.py          Frontmatter validator
├── complexity_classifier.py Tier 0 gate (trivial?)
├── collect.py               Download + write + gen-index
├── poll.py                  Refresh Tier 2/3 status
├── scout.py                 Discover cheaper models, propose diff
└── adapters/
    ├── __init__.py          Adapter ABC + IngestRequest/Result
    ├── openrouter_free.py   Tier 0 (free)
    ├── gemini_free.py       Tier 0 fallback
    ├── deepseek.py          Tier 1 (sync)
    ├── openai_batch.py      Tier 2 (batch)
    └── anthropic_batch.py   Tier 3 (batch)
```

## Reused (no duplication)

- `scripts/lib/drive_secrets.py` — `fetch_secret(name)` for API keys
- `scripts/drive_path.py` — drive/ resolution across OSes
- `scripts/_extract_response.py` — provider response parsing (unused for now; available if collect.py needs richer error mapping)
- `scripts/gen-index.py` — invoked once post-collect
- `scripts/hooks/check_source_original_file.py` — still authoritative on `original_file:`

## Cross-platform

Pure `pathlib.Path`, no shell-isms in Python. Shell wrappers per OS; line endings pinned by `.gitattributes`. Python interpreter auto-detected (`python3 → python → py -3`).
