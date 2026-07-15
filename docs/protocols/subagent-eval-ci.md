# Subagent Eval CI Protocol

> Weekly automated eval of all subagent domain suites with pass@k regression detection + optional auto-apply.

## Overview

The `.github/workflows/subagent-eval.yml` workflow runs `scripts/eval/run_subagent_eval.py` across all domain suites, compares pass@k against the previous results file, and opens a regression issue when any (suite, model) pair dropped > 0.10.

**Current status**: `workflow_dispatch` only (manual trigger). The `schedule` block is commented out — uncomment it (Mon 3:23 UTC) after the first manual run verifies green.

## Required GitHub Secrets

Configure in **GitHub repo → Settings → Secrets and variables → Actions**:

| Secret | Required? | Why |
|--------|-----------|-----|
| `OPENROUTER_API_KEY` | **YES (hard requirement)** | Fallback for ALL candidate models — `AWIKI_FORCE_MODEL` in `delegate.sh` routes via OpenRouter when no direct provider key is set. Without it, eval cannot test ANY model. |
| `DEEPSEEK_API_KEY` | Optional | Direct DeepSeek route (free tier) — avoids OpenRouter overhead for DeepSeek models. |
| `GEMINI_API_KEY` | Optional | Direct Google AI Studio route (free 1500 req/day). **Unverified** — may not be set yet. |
| `ZHIPU_API_KEY` | Optional | Direct Z.ai route (GLM models). **Unverified** — may not be set yet. |

The "Verify required secrets" step fails hard if `OPENROUTER_API_KEY` is missing, and warns (non-blocking) if optional providers are missing.

## First Run (Manual Trigger)

1. **Ensure secrets are set** (see table above). At minimum `OPENROUTER_API_KEY`.
2. Trigger manually:
   ```bash
   # Via GitHub CLI
   gh workflow run subagent-eval.yml -f domains="" -f k="2" -f create_issue="true"
   # Or: GitHub repo → Actions → "A-Wiki Subagent Eval" → Run workflow
   ```
3. **Monitor**: Actions tab → watch the run. Eval takes ~10-30 min depending on suite count + rate limits.
4. **Check results**: `evals/subagents/results/results-<timestamp>.json` is committed to main automatically.
5. **Check regression issue**: if any pass@k dropped > 0.10, an issue titled "🚨 Subagent eval regression detected" is created/updated.

## Enabling the Weekly Schedule

After the first manual run verifies green (no logic bugs, secrets work, results committed):

1. Edit `.github/workflows/subagent-eval.yml`.
2. Uncomment the `schedule` block:
   ```yaml
   on:
     workflow_dispatch:
       inputs: { ... }
     schedule:
       - cron: "23 3 * * 1"  # Mon 3:23 UTC
   ```
3. Commit. The workflow now runs every Monday 3:23 UTC automatically.

## Inputs (workflow_dispatch)

| Input | Default | Description |
|-------|---------|-------------|
| `domains` | `""` (all) | Comma-separated domain suite names (e.g. `medical,finance`). Empty = all suites. |
| `k` | `2` | Samples per case. Lower = cheaper (CI rate-limit-safe). Default 2 (not the local default 3). |
| `create_issue` | `true` | Create/update a regression issue when pass@k drops detected. |

## Regression Detection Logic

See `scripts/eval/regression_check.py`:

- **threshold**: 0.10 (pass@k drop > 10 points flagged)
- **boundary exclusive**: drop exactly == 0.10 → NOT flagged (flat)
- **severity**: `regression` (drop > threshold) | `improvement` (gain > threshold) | `flat` | `removed` (in baseline, absent from new)
- **first run** (no baseline): all entries flat (nothing to regress from)

## CI Auto-Apply (Q6 — optional, tight guardrails)

When enabled (Q6), the workflow can auto-apply adaptive routing recommendations after eval:

- **Guardrails**: `--min-samples 30` (3× default) + `--min-delta 0.20` (1.33× default)
- **Trigger**: `workflow_dispatch` only (manual consent). `schedule` = preview-only.
- **Commit**: `feat(subagent): auto-apply model swap <date> [CI guardrails: 30s/0.20δ]`
- **Revert**: `git revert <commit>` — each auto-apply is a separate atomic commit.

## Reading the Regression Issue

The issue body contains a markdown table:

```
| Suite | Model | Baseline | New | Δ |
|-------|-------|----------|-----|---|
| medical | deepseek-v4-flash | 0.90 | 0.70 | **-0.20** |
```

Plus a "Removed" section (models that disappeared from results) and an "Improvements" section (models that got better).

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| "❌ OPENROUTER_API_KEY required" | Secret not set | GitHub repo → Settings → Secrets → add it |
| "Eval failed for X (rate limit?)" | Free-tier rate limit hit | Reduce `k` to 1, or run fewer domains per trigger |
| "No results file produced" | All eval calls failed | Check secrets + delegate.sh `AWIKI_FORCE_MODEL` logic |
| Regression issue not created | `create_issue=false` or no regressions | Check `has-regression` flag in workflow log |
| Results file not committed | `git push` permission denied | Check `permissions: contents: write` in workflow |

## Related

- `docs/protocols/subagent-eval.md` — local eval harness protocol
- `scripts/eval/run_subagent_eval.py` — eval runner
- `scripts/eval/regression_check.py` — regression detection
- `scripts/eval/apply_eval_results.py` — apply best model from eval results
- `scripts/eval/adaptive_routing.py` — adaptive routing with guardrails
