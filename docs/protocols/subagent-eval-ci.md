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
2. Trigger via the helper script (checks `gh` CLI + auth + workflow presence, then triggers + watches):
   ```bash
   # Recommended — preflight checks + post-run schedule-enable guidance
   bash scripts/eval/trigger_ci.sh --dry-run        # preview the plan
   bash scripts/eval/trigger_ci.sh                  # trigger + watch (default inputs)
   bash scripts/eval/trigger_ci.sh --domains medical,finance --k 2
   bash scripts/eval/trigger_ci.sh --no-watch       # trigger, don't block on watch
   ```
   Or trigger directly via GitHub CLI / web UI:
   ```bash
   gh workflow run subagent-eval.yml -f domains="" -f k="2" -f create_issue="true"
   # Or: GitHub repo → Actions → "A-Wiki Subagent Eval" → Run workflow
   ```
3. **Monitor**: Actions tab → watch the run. Eval takes ~10-30 min depending on suite count + rate limits.
4. **Check results**: `evals/subagents/results/results-<timestamp>.json` is committed to main automatically.
5. **Check regression issue**: if any pass@k dropped > 0.10, an issue titled "🚨 Subagent eval regression detected" is created/updated.

The helper script prints the exact one-line edit to enable the weekly schedule when the run finishes green (see "Enabling the Weekly Schedule" below).

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

## Multi-Model Race (S5 + T4 — concurrent, ทุก suite)

หลัง eval หลักเสร็จ + commit ผลลัพธ์ CI จะรัน **race step** เพิ่มเติม:

- **ทำอะไร**: ยิง 3 candidate models (`deepseek-v4-flash`, `deepseek-v4-pro`, `glm-5.2`) ที่ **ทุก single-agent suite** พร้อมกันแบบ concurrent (ThreadPool, k=1, max-workers=6)
- **T4 ขยายจาก S5**: เดิม (S5) ทำเฉพาะ `medical` pilot → T4 ขยายเป็น loop ทุก suite (ข้าม `pipeline-*.json` ที่เป็น DAG)
- **continue-on-error: true** — race failure (rate limit, timeout) **ไม่บล็อค** eval pipeline หลัก เป็น bonus comparison เท่านั้น
- **ผลลัพธ์**: `.tmp/subagent-eval/races/<suite>.json` (แยกไฟล์ต่อ suite ใน artifact `subagent-eval-report`)
- **สรุปผล**: CI แสดงตาราง `suite | best model | pass@k` หลัง race ทุก suiteเสร็จ
- **วิธีอ่านผล** (ในแต่ละ suite JSON):
  - `winner` = model ที่ pass sample แรกเร็วที่สุด (first-past-the-post — เหมาะกับ latency-sensitive routing)
  - `best` = model ที่ pass@k สูงสุด (quality-sensitive)
  - `overall` = mean pass@k + win counts รวมทุก case

ดู `scripts/eval/race_eval.py` (R2) สำหรับรายละเอียด race logic + CLI options

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
- `scripts/eval/trigger_ci.sh` — first-run trigger helper (R1)
- `scripts/eval/run_subagent_eval.py` — eval runner
- `scripts/eval/regression_check.py` — regression detection
- `scripts/eval/apply_eval_results.py` — apply best model from eval results
- `scripts/eval/adaptive_routing.py` — adaptive routing with guardrails
