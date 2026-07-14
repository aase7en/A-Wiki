# Subagent Model Routing — Anti Rate-Limit Protocol

> **Status:** Active (Chunk SA1 of the Specialized Domain Subagents plan)
> **Enforced by:** `scripts/hooks/check_subagent_fanout.py` (warn-only) + convention in `delegate-subagent` skill
> **Related:** `docs/protocols/delegation.md` · `docs/protocols/model-switching.md` · `docs/protocols/cross-agent-plan-handoff.md`

---

## TL;DR

When the primary agent fans out to N parallel subagents, **never point all N at the same provider/model** — they share one rate-limit bucket and the second/third call fails with `Provider rate limited the model request`. Spread parallel subagents across different providers, and fall back to a second provider on a 429.

---

## Root Cause (2026-07-14 incident)

ZCode's built-in `Explore` subagent was pinned (via `~/.zcode/v2/agents-state.json` → `builtInModelOverrides.Explore`) to a single free-tier model:

```json
{ "builtInModelOverrides": { "Explore": "custom:c8222819-ee91-4f45-8dd5-5f3d2ea4f5f3:gemini-3.5-flash" } }
```

When the primary agent launched 3 Explore subagents in one message (parallel fan-out), all 3 hit Gemini's free-tier per-key rate-limit bucket simultaneously → all 3 returned `Provider rate limited the model request`. This is the failure the user reported as "Explore ชอบ failed".

The bug is **not** in the Explore agent's logic — it is in the **model routing**. One bucket cannot serve N concurrent requests when N ≥ 3.

---

## The Rule

> **Fan-out diversity rule.** A single primary-agent message may launch at most **2 parallel subagents against the same provider**. If 3+ subagents are launched in parallel, each must resolve to a **different provider** (or a different model on the same provider whose limits are tracked separately).

This mirrors the **Director Agent / Smart Scheduler** pattern from [FinRobot](https://github.com/AI4Finance-Foundation/FinRobot), whose explicit job is "ensuring model diversity and optimizing the selection of the most appropriate LLM for each task," and Agency Swarm's multi-provider router (LiteLLM/OpenRouter fallback).

---

## Provider → Rate-Limit Bucket Map

Providers configured on this machine (from `~/.zcode/v2/config.json`). Machine-specific IDs live in the private config; only the **bucket identity** matters for routing decisions.

| Provider (bucket) | Enabled | Free? | Best for | Parallel-safe up to |
|---|---|---|---|---|
| **Z.ai GLM-5.2** (`builtin:zai-coding-plan`) | yes | plan | conversational, Thai, general | ~3 |
| **DeepSeek v4-flash / v4-pro** | yes | paid (cheap) | reasoning, code, retrieval | ~5 (paid) |
| **OpenRouter free** (`openrouter/free`, nemotron-free) | yes | free | fallback, light work | ~2 |
| **Gemini 3.5 Flash** (Google AI Studio) | yes | free | fast retrieval, fan-out | **1–2 only** (free tier tight) |
| Primary agent (Sonnet) | — | paid | deep reasoning, validation | n/a (supervisor) |

> **Bucket = provider API key**, not model. Two models on the same key share one quota.

---

## Model Diversity Matrix (for parallel fan-out)

When launching N parallel subagents, assign models round-robin across providers:

| N | Subagent 1 | Subagent 2 | Subagent 3 | Subagent 4 |
|---|---|---|---|---|
| 2 | DeepSeek v4-flash | GLM-5.2 | — | — |
| 3 | DeepSeek v4-flash | GLM-5.2 | OpenRouter free | — |
| 4 | DeepSeek v4-flash | GLM-5.2 | OpenRouter free | DeepSeek v4-pro |

**Never:** 3× Gemini Flash. **Never:** 3× any single free-tier key.

---

## Fallback Chain

When a subagent call returns `Provider rate limited` (HTTP 429) or `Provider rate limited the model request`:

```
1. Primary provider for that subagent  →  FAIL (429)
2. DeepSeek v4-flash                   →  retry
3. OpenRouter free                     →  retry
4. GLM-5.2                             →  retry
5. Gemini 3.5 Flash                    →  last resort (single call only)
```

Implemented by `scripts/swarm/subagent_fallback.sh`. The primary agent invokes it with the subagent type + prompt; the script walks the chain until one succeeds.

---

## Per-Domain Default Models

To make diversity automatic, each domain cluster defaults to a different primary model. See the Specialized Domain Subagents plan (chunks SA3–SA5) for the full list. Summary:

| Domain cluster | Default model | Reason |
|---|---|---|
| Coding / Data / Engineering (reasoning-heavy) | `sonnet` or DeepSeek v4-pro | needs deep reasoning |
| Health / Finance / Business (factual + retrieval) | DeepSeek v4-flash | strong + cheap |
| Assistant / Tutor / Thought-partner (conversational) | GLM-5.2 or OpenRouter free | economize |
| Explore-style (read-only, fan-out heavy) | DeepSeek v4-flash (not Gemini) | avoid the single tight bucket |

---

## How the primary agent should fan out

1. **Classify** each sub-task → pick the subagent type.
2. **Look up** that subagent's default model (from its frontmatter `model:` field).
3. **Check diversity**: if ≥3 subagents in this message share a provider, reassign one to the next provider in the matrix.
4. **Launch** the subagents in parallel.
5. **On 429**: re-invoke the failed subagent via `scripts/swarm/subagent_fallback.sh` with its original prompt.

---

## Hook enforcement

`scripts/hooks/check_subagent_fanout.py` (PreToolUse on the Agent tool) inspects the `subagent_type` of each Agent call in the current message, resolves each to its default provider, and **warns** (exit 0, stderr message) when ≥3 calls would hit the same provider. It does **not** block — the primary agent may intentionally override. Override env: `HOOK_SKIP=check_subagent_fanout`.

---

## References

- FinRobot — Director Agent / Smart Scheduler: https://github.com/AI4Finance-Foundation/FinRobot
- Agency Swarm — multi-provider router: https://github.com/VRSEN/agency-swarm
- A-Wiki Cost-First Decision Pyramid: `AGENTS.md` §💰
- Delegation protocol: `docs/protocols/delegation.md`
- Model switching protocol: `docs/protocols/model-switching.md`
