# Universal Cost-First Routing Protocol

**Scope**: Binding for every A-Wiki agent (Claude Code, Codex, Gemini CLI, Cursor, Windsurf, Cline, Copilot, Aider, plus any future agent that touches the brain).

**Authority**: Iron Law extension. Violations are blocked by `scripts/hooks/check_harness_routing.py` (PreToolUse Write/Edit/MultiEdit). Override only in emergencies via `HOOK_SKIP=check_harness_routing` — and log why in the session memory.

## Why universal routing?

The brain has many heads. Without a single routing layer:

1. **Cost leaks** — every agent picks its own model. No batch discount, no free-tier opportunism, no cost report.
2. **Quality drift** — each agent's prompt differs slightly; output frontmatter diverges; the source provenance hook (`check_source_original_file.py`) catches some failures but not all.
3. **Stale models** — hardcoded model names rot. Free tier shifts weekly. Without a scout layer, agents either over-pay or use deprecated names.
4. **No audit** — "who ingested this and at what cost?" is unanswerable.

The harness fixes all four with one engine, one config, one hook, one scout.

## The contract (binding)

Every agent must:

1. **Route ingestion through the harness.** Source writes that bypass the harness are blocked. Routing channels (pick any one):
   - CLI: `python scripts/batch/route.py ...`
   - Shell wrapper: `scripts/batch/route.sh` / `route.ps1` / `route.cmd`
   - MCP tools: `wiki_ingest_route`, `wiki_batch_status`, `wiki_batch_collect`
   - ENV-driven (CI): `A_WIKI_ROUTE_TIER`, `A_WIKI_BACKEND`
2. **Never hardcode model names or prices.** Read `wiki/context/cost-routing.conf` (the single source of truth). The scout job refreshes it from provider APIs.
3. **Respect the tier discount window.** Tier 2/3 results arrive within 24h. Do not poll faster than every 10 minutes; do not block users waiting for batch completion — return the `batch_id` and continue.
4. **Preserve `routed_via: harness@v1` frontmatter** when editing existing harness-produced sources. The hook grandfathers legacy sources (no marker) but blocks regressions.

## Tier semantics

| Tier | Who picks it | Why |
|------|-------------|-----|
| **00** | Primary agent itself | Planning, bugfix, validation, scout — subscription marginal cost is zero. Harness must never auto-route here (would double-bill). |
| **0** | `complexity_classifier.is_trivial()` | Single short ASCII file, classification-only — free models are good enough. |
| **1** | Default | 1-20 file backlog; DeepSeek realtime is fast + cheap enough that batch overhead loses. |
| **2** | Backlog > `escalation_threshold_files` | Input-heavy bulk; OpenAI Batch 50% discount + 24h SLA wins. |
| **3** | Manual escalation after Tier 1/2 quality fails | Anthropic Batch Haiku — Thai context + reasoning quality, still discounted. |

## Per-agent integration

| Agent | Channel | Example |
|-------|---------|---------|
| Claude Code | MCP `awiki` server | `wiki_ingest_route(file="raw/foo.md")` |
| Codex | Shell wrapper in workflow | `bash scripts/batch/route.sh --file raw/foo.md` |
| Gemini CLI | Tool definition → CLI | `python scripts/batch/route.py --file raw/foo.md` |
| Cursor | Rule file → shell exec | `.cursor/rules/` includes a routing directive |
| Windsurf | Same as Cursor or MCP | choose one and stick to it |
| Cline | Terminal tool | `route.sh --domain ai-tools` |
| Copilot Workspace | Task spec | shell call to `route.sh` |
| Aider | `/run` macro | `python scripts/batch/route.py ...` |

## Scout cadence

The scout is not a daemon — run it manually or schedule weekly:

```bash
python scripts/batch/scout.py --refresh    # pull OpenRouter free list
python scripts/batch/scout.py --propose    # diff against cost-routing.conf
# review wiki/context/cost-routing.conf.proposed
python scripts/batch/scout.py --apply      # swap in
```

Diffs are never auto-applied. The user reviews; nothing changes without consent.

## Emergency override

If the hook is wrong (e.g., editing a legacy source manually to fix a typo):

```bash
HOOK_SKIP=check_harness_routing <your-command>
```

Log the override in `wiki/context/session-memory.md` so the team knows why. Two overrides on the same path = file an issue.

## Related

- [scripts/batch/README.md](../../scripts/batch/README.md) — implementation guide
- [wiki/context/cost-routing.conf](../../wiki/context/cost-routing.conf) — live policy
- [scripts/hooks/check_harness_routing.py](../../scripts/hooks/check_harness_routing.py) — enforcement
- [agent-skills/swarm-intelligence/model-scouter.md](../../agent-skills/swarm-intelligence/model-scouter.md) — older spec the scout descends from
