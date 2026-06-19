# Agent Model Auto-Scan Protocol

> Weekly benchmark-driven model swapping within safe cost-class boundaries.

## Overview

Every Monday at 02:41 UTC, a GitHub Actions workflow runs `scripts/agents/agent_model_scan.py` against the offline-first capability scorecard (`wiki/context/model-capability-scores.json`). If a cheaper or equal-cost model in the same cost class offers a capability gain >= 5 (on the agent's `role_dimension`), the scanner rewrites the agent `.md` frontmatter and commits the change.

## Architecture

```
wiki/context/model-capability-scores.json   ← Durable offline fallback (committed)
wiki/context/agent-model-policy.json         ← Policy: cost classes, agents, apply rules
wiki/context/agent-model-scan-log.jsonl      ← Revert log (one JSONL entry per apply)
scripts/agents/agent_model_scan.py           ← Scanner: decide_agent + rewrite + revert
.github/workflows/agent-model-scan.yml       ← Weekly cron + workflow_dispatch
```

## Cost Classes

| Class | Rank | Description | Auto-apply? |
|-------|------|-------------|-------------|
| `free` | 0 | Gemini Flash, Groq Llama, Fireworks free-credit models | ✅ Same class |
| `cheap-paid` | 1 | DeepSeek Chat, Z.ai direct | ✅ Same class |
| `premium-paid` | 2 | Claude Opus via OpenRouter | ✅ Same class |
| `subscription` | -1 | Z.ai Codeplan (pinned) | ❌ Never |

### Rules

1. **Same cost class** + capability gain >= `min_capability_gain` → **auto-apply** (rewrite `.md` frontmatter)
2. **Tier up** (more expensive) → **propose only** (creates issue)
3. **Tier down** (cheaper) → **auto-apply** (cost-first reward)
4. **Unmanaged agent** → **propose only** (never writes)

## Managed vs Unmanaged Agents

| Agent | Source of truth | Managed? | GHA action |
|-------|----------------|----------|------------|
| architect, code-reviewer, code-simplifier, code-skeptic, docs-specialist, frontend-specialist, test-engineer | `.kilo/agents/<name>.md` frontmatter (`model:` + `variant:`) | ✅ Yes | Auto-apply safe swaps |
| plan, ask, code, debug, orchestrator | `~/.config/kilo/kilo.jsonc` `agent.<name>.{model,variant}` | ❌ No | Propose only via issue |

**Why unmanaged:** Creating `.md` files for Kilo's built-in agents would **wipe the built-in prompt** (the `.md` body becomes the prompt). The only safe way to pin model+variant for built-ins is `kilo.jsonc` `agent.{name}.{model,variant}` — but that file is machine-local and not in the repo. GHA cannot edit it.

## The 7 Managed Agents

| Agent | Current model | Cost class | Role dimension | Candidate families |
|-------|---------------|------------|----------------|--------------------|
| architect | `claude-opus-4.8` | premium-paid | reasoning | claude, glm, deepseek |
| code-reviewer | `gemini-3.5-flash` | free | swe_bench | gemini-flash, llama, qwen, kimi |
| code-simplifier | `qwen3-32b` | free | swe_bench | qwen, llama, gemini-flash |
| code-skeptic | `kimi-k2p7-code` | free | swe_bench | kimi, qwen, gemini-flash |
| docs-specialist | `gemini-3.5-flash` | free | reasoning | gemini-flash, llama, qwen |
| frontend-specialist | `qwen3p7-plus` | free | swe_bench | qwen, gemini-flash, kimi |
| test-engineer | `kimi-k2p7-code` | free | swe_bench | kimi, qwen, gemini-flash |

## CLI Usage

```bash
# Dry-run (default) — report what would change
python3 scripts/agents/agent_model_scan.py --dry-run

# Apply safe swaps (+ write revert log)
python3 scripts/agents/agent_model_scan.py --apply

# Revert the last scan write
python3 scripts/agents/agent_model_scan.py --revert

# Offline-only (no network refresh)
python3 scripts/agents/agent_model_scan.py --offline
```

## Revert Process

Every auto-apply writes a line to `wiki/context/agent-model-scan-log.jsonl`:

```json
{"agent": "code-reviewer", "from": "google/gemini-3.5-flash", "to": "fireworks-ai/.../kimi-k2p7-code", "timestamp": "2026-06-19T10:30:00Z", "file": ".kilo/agents/code-reviewer.md"}
```

To undo the last scan:

```bash
python3 scripts/agents/agent_model_scan.py --revert
```

This reads the last log line, rewrites the `.md` frontmatter back to `from`, and strips the log line.

## Frontmatter Format

Agent `.md` files use Kilo's YAML frontmatter. The scanner uses **line-based** rewriting (no PyYAML dependency) — it finds `model:` in the frontmatter and replaces the value:

```yaml
---
model: google/gemini-3.5-flash
mode: primary
description: Senior software engineer conducting thorough code reviews
options:
  displayName: Code Reviewer
  id: code-reviewer
permission:
  read: allow
  bash: allow
  edit: deny
---
```

If `model:` is absent from the frontmatter, the scanner inserts it after the opening `---`.

## Symlink Strategy

`~/.config/kilo/agents` → `/Users/aase7en/Desktop/A-Wiki/.kilo/agents`

This makes the 7 managed `.md` files available globally (precedence level 4: global agent `.md` files). For A-Wiki project itself, project `.md` (level 5) takes priority. Since the symlink points to the same files, both levels resolve to the same content.

## Verification

```bash
python3 -m pytest tests/test_agent_model_scan.py -v
python3 scripts/agents/agent_model_scan.py --dry-run
python3 wiki/context/agent-model-policy.json -c "import json; json.load(open('wiki/context/agent-model-policy.json'))"
```

## Limitations

- **Built-in overrides (5 agents) are not auto-managed.** GHA can only propose via issue. The user must manually edit `~/.config/kilo/kilo.jsonc` to adjust built-in agent models.
- **Scorecard `[training]` confidence** means numeric scores are estimates, not verified benchmarks. The `min_capability_gain: 5` threshold prevents churn from noise.
- **Fireworks $6 prepaid credit models** are treated as `free` cost class. After credit exhaustion they become paid, but the scanner has no cost-sensing for that — the user must update the policy JSON to reclassify them.
