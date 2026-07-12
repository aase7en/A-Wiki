# A-Wiki Capability Upgrade Roadmap

> [verified 2026-06-12] Source-of-truth for upgrading A-Wiki from a broad second brain into measurable capability lanes without adding heavy always-loaded context.

## Current Baseline

| Surface | Current state | Verification |
|---|---|---|
| Repo health | Preflight, hooks, model router, skill quality, and skill evals pass locally | `python3 scripts/verify-awiki-ready.py` |
| Wiki graph | Graph is generated and queryable; broken links are currently clean, while orphan pages remain a triage backlog | `python3 scripts/wiki/query-graph.py --stats` |
| Skills | Owned skills are quality-checked and eval-covered | `python3 scripts/skill-quality-report.py --fail-on-warn` |
| Capability map | Generated from scripts, skills, protocols, render surfaces, graph stats, and strategic lanes | `python3 scripts/wiki/build-capability-map.py --out -` |

## Strategic Lanes

| Lane | Hub | Primary route | Hard gate |
|---|---|---|---|
| Design/Web | `wiki/synthesis/design-web-capability-hub.md` | frontend-design -> webapp-testing -> Canva only for handoff/export | Visual smoke before done |
| High-end lightweight game | `wiki/synthesis/game-lightweight-highend-capability-hub.md` | Phaser/Vite/TypeScript -> PixelLab manifest -> asset report | Asset/performance gate |
| Revenue engine | `wiki/synthesis/revenue-engine-capability-hub.md` | wiki evidence -> Creator Layer -> verified market research -> product/content package | Public-safe/privacy gate |
| Premium auto trading | `wiki/synthesis/premium-auto-trading-capability-hub.md` | paper -> read-only -> live backend after security review | No client secrets, no live execution by default |

## P0 Graph Hygiene Loop

Run this loop before changing capability routing or after a major ingest:

```bash
python3 scripts/wiki/query-graph.py --broken
python3 scripts/wiki/query-graph.py --orphans
python3 scripts/gen-index.py --check
```

Triage order:

| Priority | Fix first | Reason |
|---|---|---|
| P0 | Broken links from hub pages, protocols, and synthesis pages | They affect agent routing and planning |
| P1 | Broken links from entity/concept pages | They reduce retrieval quality |
| P2 | Orphans that should be discoverable by domain | They hide useful knowledge from graph traversal |
| P3 | Source-page person/company wikilinks that are not intended as wiki nodes | Convert to plain text only when editing that source for another reason |

## Capability Upgrade Matrix

| Area | Existing capability | Upgrade | Verify |
|---|---|---|---|
| Second brain | Search, graph, skills, protocols, generated context | Four lanes with explicit routing, verification, and safety gates | `python3 scripts/wiki/build-capability-map.py --out -` |
| Design website | Strong design skill and web testing skill exist | Add visual QA route and Canva export policy | Target app build + Playwright/browser smoke |
| Game | Sunday Invest Moon, Phaser, PixelLab pipeline exist | Lock asset manifest, performance budget, and no-secret runtime pattern | Asset pack report + game build checks |
| Revenue | Creator Layer and Thai/social skills exist | Add public-safe monetization loop from wiki source to validated product/content | Privacy scan + source/date/link review |
| Auto trading | Freqtrade reference, read-only feed, and Bot Trading Iron Law exist | Separate paper/read-only/live backend tiers | Trading security review before live adapter |

## MCP And Plugin Policy

Keep MCP lightweight and allowlisted:

| MCP/plugin | Policy |
|---|---|
| `awiki` MCP | Keep; local wiki search/read/graph only |
| Filesystem MCP | Keep scoped to repo paths only |
| GitHub MCP | Use when repo/issue/PR context is needed; prefer read-only for review |
| Supabase MCP | Use only for projects that actually use Supabase |
| Canva connector | Use for visual assets, presentations, social posts, and brand handoff; not a memory source-of-truth |
| Trading/exchange MCP | Reject by default; trading authority belongs only in reviewed backend services |

Any new skill, plugin, MCP, or upstream snapshot must pass `docs/protocols/brain-improvement-gate.md` and `docs/runbooks/upstream-refresh.md`.

## Source Watchlist

Use these official upstreams for volatile capability decisions. Record the retrieval date in any new source page or capability note.

| Area | Official source | Current routing decision |
|---|---|---|
| MCP discovery | https://registry.modelcontextprotocol.io/ and https://github.com/modelcontextprotocol/servers | Registry is the discovery surface; reference server repo is not a production allowlist by itself |
| GitHub MCP | https://github.com/github/github-mcp-server | Allowed when repo/issue/PR context is needed; prefer scoped/read-only review usage |
| Supabase MCP | https://supabase.com/docs/guides/ai-tools/mcp | Allowed only for active Supabase projects, preferably project-scoped and read-only when reviewing |
| Agent Skills | https://github.com/anthropics/skills and https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview | Track patterns and install candidates, but every adopted skill needs local eval/quality checks |
| Game stack | https://github.com/phaserjs/template-vite-ts | Phaser + Vite + TypeScript remains the default lightweight high-end route; verify template version before bootstrapping |
| Trading stack | https://www.freqtrade.io/en/stable/, https://hummingbot.org/docs/, https://docs.ccxt.com/ | Use for paper/read-only research; Hummingbot MCP/skills and CCXT agent skills still require trading safety review before adoption |

## Update Loop

| Cadence | Action | Verify |
|---|---|---|
| Weekly | Refresh model roster and inspect diff | `bash scripts/update-model-roster.sh` |
| Monthly | Review upstream skills/plugins/MCP candidates | `docs/runbooks/upstream-refresh.md` checklist |
| After capability change | Regenerate context and update release tracking | `python3 scripts/gen-index.py && python3 scripts/gen-index.py --check` |
| Before handoff | Verify repo and graph health | `python3 scripts/verify-awiki-ready.py` |

## Verification Notes

- Game asset pipeline moved to the product repo (2026-07-12): run
  `python3 scripts/game/report_phaser_asset_pack.py game-assets/manifests --root . --check-files`
  from the company webapp repo — that remains the right gate for real game asset work.
- Do not create placeholder manifests just to make the report green; manifests must represent real PixelLab/Phaser assets.
