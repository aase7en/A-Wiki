# Hermes Model Priority & Routing Overhaul

> Plan for: Hermes agent on Raspberry Pi 5 (offline during authoring; work done on Windows PC + Kilo)
> Brain: A-Wiki (shared second brain)
> Created: 2026-06-23

## Goal

Restructure Hermes Pi5 model selection so it routes tasks across a clear priority chain — Codeplan subscription (with accepted restrict risk) as Priority 1 for heavy work, DeepSeek V4-Flash as the cost-saving default, and Z.AI pay-per-token / Gemini / OpenRouter free as fallbacks. Add restrict detection + manual recovery, and a benchmark scanner that surfaces cheaper/smarter models as advisory reports (never auto-applied).

## Resolved Decisions

| # | Decision | Value |
|---|----------|-------|
| 1 | Default model | `deepseek/deepseek-v4-flash` — save Codeplan quota |
| 2 | Codeplan in Hermes | Use anyway (accepted restrict risk) via Z.AI OpenAI-compatible endpoint |
| 3 | Codeplan quota | Limited (5h + weekly) → default stays DeepSeek |
| 4 | Codeplan models | `glm-4.7` (routine, 1×) + `glm-5.2` (complex, 3× peak) + `glm-5-turbo` |
| 5 | Restrict recovery | Provider-level blacklist + manual recovery only (no auto-retry) |
| 6 | Benchmark scanner | Advisory only → report + Telegram notify, never auto-apply |

### Priority Chain (final, for Hermes Pi5)

```
DEFAULT   : deepseek/deepseek-v4-flash              (light tasks, save quota)
COMPLEX   : zai-codeplan/glm-5.2 (3× peak)          (heavy reasoning/coding)
ROUTINE   : zai-codeplan/glm-4.7 (1×)               (Codeplan routine)
FALLBACK 1: deepseek/deepseek-v4-pro                (Codeplan quota exhausted / restricted)
FALLBACK 2: zai/glm-4.7-flash (FREE pay-per-token)  (DeepSeek limited)
FALLBACK 3: gemini / openrouter free                (last resort)
```

### Codeplan facts (from docs.z.ai/devpack/overview.md)

- Supported models: GLM-5.2, GLM-5-Turbo, GLM-4.7 (all plans)
- GLM-5.2 / GLM-5-Turbo multiplier: 3× peak (14:00–18:00 UTC+8), 2× off-peak; Z.AI recommends GLM-4.7 for routine, GLM-5.2 for complex
- Quota: 5-hour limit + weekly limit (Lite/Pro/Max tiers)
- Endpoint: same `open.bigmodel.cn/api/paas/v4` as pay-per-token, distinguished by API key
- Risk: officially limited to Claude Code / Kilo / Cline / OpenCode — Hermes is SDK-based, may be restricted (user accepted risk)

## Files to Change

| File | Action | Notes |
|------|--------|-------|
| `scripts/hermes/model-pool/model-pool.json` | Edit | **Partially edited before plan mode** (DeepSeek v4-flash/v4-pro added, fallback_chain reordered). Implementation agent MUST reconcile with this plan: add a separate `zai-codeplan` provider distinct from `zai` pay-per-token. |
| `scripts/hermes/model-pool/cost-router.py` | Rewrite via `Write` tool | Previous attempt failed due to Windows PowerShell escaping — use `Write` tool directly. Add Codeplan tier + Z.AI pay-per-token entries. |
| `scripts/hermes/model-pool/model-priority-config.json` | Create (new) | Priority chain + Codeplan quota config + restrict policy |
| `scripts/hermes/model-pool/model-fallback-router.py` | Edit | Add 403/401 restrict detection, provider-level blacklist, manual-recovery flag |
| `scripts/hermes/model-pool/benchmark-scanner.py` | Create (new) | Scan 3 sources, advisory report only |
| `scripts/hermes/model-pool/restrict-state.json` | Create (new) | Persistent blacklist state (Codeplan provider) |
| `scripts/hermes/notify-telegram.sh` | Use existing | Send advisory report + restrict alert |

### Pre-existing state to reconcile

- `model-pool.json` was edited mid-session: `fallback_chain.text` now starts with `zai/glm-4.7-flash` (pay-per-token FREE), `deepseek/deepseek-v4-flash`, `deepseek/deepseek-v4-pro`; `providers.deepseek` now has `deepseek-v4-flash` + `deepseek-v4-pro`. Verify these align with the final chain above before building on top.
- `cost-router.py` is still the original (edit attempts failed on PowerShell). Rewrite fully via `Write`.
- `wiki/context/agent-model-policy.json` exists for Kilo/Claude agents (Codeplan pinned on `plan`). Do NOT change it — this plan targets Hermes Pi5 only.

## Data Flow

```
Task arrives
  → DEFAULT: deepseek/deepseek-v4-flash (light, save Codeplan quota)
  → COMPLEX detected (reasoning/coding heavy)
      → zai-codeplan/glm-5.2 (3×) or glm-4.7 (1×)
  → Codeplan returns 403/401 (restrict detected)
      → BLACKLIST zai-codeplan provider (persistent, manual recovery)
      → notify Telegram
      → route to deepseek/deepseek-v4-pro
  → Codeplan returns 429 (quota, not restrict)
      → short cooldown, then retry chain (no blacklist)
  → DeepSeek 429
      → zai/glm-4.7-flash (FREE pay-per-token)
  → all exhausted
      → gemini / openrouter free (last resort)

Daily cron → benchmark-scanner.py
  → advisory report (no config change)
  → Telegram notify if cheaper+smarter model found
```

## Failure Modes

1. **Codeplan restrict (403/401 consecutive)** → blacklist `zai-codeplan` provider entirely + Telegram alert + use DeepSeek until manual reset (clear `restrict-state.json`).
2. **Codeplan quota exhausted (429)** → fallback by chain, NO blacklist (transient).
3. **DeepSeek limit (429)** → fallback to Z.AI pay-per-token GLM-4.7-Flash (free).
4. **All providers exhausted** → Gemini/OpenRouter free last resort; alert Telegram.
5. **Distinguishing restrict vs quota**: 403/401 (auth/restrict) → long blacklist; 429 (rate) → short cooldown only. Detect via HTTP status code + response body keywords.

## Validation

- `python scripts/hermes/model-pool/cost-router.py --tokens 10000` → prints priority tiers correctly (Codeplan tier highest, then DeepSeek default, then Z.AI pay-per-token, then free fallback)
- `python scripts/hermes/model-pool/model-fallback-router.py zai-codeplan/glm-5.2 text` with blacklisted state → skips entire `zai-codeplan` provider, returns DeepSeek
- `python scripts/hermes/model-pool/benchmark-scanner.py --dry-run` → generates advisory report JSON, does NOT modify any config
- `python scripts/hermes/model-pool/benchmark-scanner.py` (live) → writes report to `reports/benchmark-<date>.json` + Telegram notify stub
- Unit tests (new `tests/test_model_routing.py`): restrict detection (403 → blacklist), quota (429 → cooldown), chain exhaustion, priority ordering
- Manual: verify `model-pool.json` JSON valid after reconciliation

## Rollout / Migration

1. Author all files on Windows PC (this plan) → commit to main
2. Pi5 auto-sync cron (every 6h, existing `auto-sync-from-git.sh`) pulls new scripts
3. On Pi5: set env vars `ZAI_CODEPLAN_API_KEY` (Codeplan key), `ZAI_API_KEY` (pay-per-token key), `DEEPSEEK_API_KEY`
4. Run `python model-pool-scanner.py` to refresh pool, then `benchmark-scanner.py --dry-run` to verify
5. First Codeplan restrict will trigger blacklist + Telegram alert; user manually clears `restrict-state.json` when safe

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Z.AI bans Codeplan account permanently from SDK abuse | Blacklist-on-403 + manual recovery (Decision 5); never auto-retry restrict |
| Codeplan quota consumed too fast by routine tasks | Default = DeepSeek; Codeplan only for complex (GLM-5.2) / explicit routine (GLM-4.7) |
| Wrong API key used (Codeplan vs pay-per-token) | Separate `zai-codeplan` provider entry with its own `api_key_env` field |
| Benchmark scanner accidentally auto-applies | Advisory-only enforced; scanner writes report, never edits config |
| Pi5 offline during authoring | All edits land in repo; Pi5 syncs when online |

## Out of Scope

- Windows PC / Kilo / Claude Code model config (uses `agent-model-policy.json` + Codeplan directly — unchanged)
- OpenAI/Anthropic premium paid tiers (Claude Opus via OpenRouter) — emergency only, not in default chain
- Changing `wiki/context/agent-model-policy.json` (Kilo agents, separate concern)

## Open Questions for Implementation Agent

1. **Codeplan API key separation**: Confirm whether Codeplan uses a distinct API key vs the pay-per-token key. If same key, distinguish by a header or model prefix (`glm-5.2` route). Check `https://docs.z.ai/devpack/quick-start.md` during implementation.
2. **Restrict detection keywords**: Z.AI restrict response body format unknown — implement defensive matching on status 401/403 + keywords like `restricted`, `unauthorized tool`, `unsupported`. Refine after first real restrict event.
3. **Telegram notify integration**: Verify `notify-telegram.sh` exists and works on Pi5; if missing, the restrict alert is the highest-priority use case.
