# Subagent Eval Protocol

> **Purpose:** Data-driven model selection for the 28 specialized subagents. Replaces the heuristic `model:` choices (seeded in SA1–SA6) with measured pass@k results.

## When to run

- **After deploying new subagents** — to verify the seeded model is actually the best on real prompts.
- **When a provider changes pricing or deprecates a model** — re-evaluate fallback candidates.
- **Periodically (monthly)** — catch model-quality regressions early.

## The eval suites

Located in `evals/subagents/*.json`. Each suite is a JSON file matching the `evals/awiki/` convention:

```json
{
  "suite": "<domain>",
  "description": "...",
  "cases": [
    {
      "id": "<case-id>",
      "subagent": "<target-subagent-name>",
      "prompt": "<the task>",
      "required": ["keyword"],   // response must contain all (case-insensitive)
      "forbidden": ["keyword"]   // response must contain none
    }
  ]
}
```

Current suites (10 files, ~100 cases total):

| Suite | Domain | Subagents covered |
|---|---|---|
| `medical.json` | medical | medical-lit-reviewer, clinical-reasoner, medical-safety-checker |
| `finance.json` | trader/data | finance-data-fetcher, finance-analyst, finance-debater |
| `coding.json` | code/debug/engineering | code-explorer, code-architect, debug-investigator, test-engineer-agent |
| `ai-ops.json` | ai-ops | cost-auditor, model-router-advisor, token-optimizer |
| `webapp.json` | code/design/ux-ui | frontend-architect, ui-ux-reviewer, db-schema-designer, mobile-pattern-advisor |
| `business.json` | business/thai | marketing-strategist, realestate-tax-advisor, business-doc-drafter |
| `assistant.json` | productivity | inbox-triage, schedule-planner, draft-responder |
| `thought-partner.json` | productivity/business | workflow-simplifier, copywriting-partner |
| `tutor.json` | productivity/thai | language-tutor, skill-coach |
| `data.json` | data | data-profiler |

## How to run

### 1. Dry-run (default — zero API calls, safe)

```bash
python scripts/eval/run_subagent_eval.py --all
# or one domain:
python scripts/eval/run_subagent_eval.py --domain medical
```

Prints the plan: which suites, how many cases, estimated API calls (0 in dry-run).

### 2. Real run (routes through delegate.sh — uses free-tier quota)

```bash
python scripts/eval/run_subagent_eval.py --all --apply
# compare specific models only:
python scripts/eval/run_subagent_eval.py --domain medical \
  --models deepseek-v4-flash,glm-5.2 --apply
```

Results written to `evals/subagents/results/results-<timestamp>.json`.

### 3. Apply the winning model

```bash
# Preview the recommended changes first (no writes):
python scripts/eval/apply_eval_results.py --latest

# If the recommendations look good, apply them:
python scripts/eval/apply_eval_results.py --latest --write
```

This rewrites the `model:` field in each subagent's `agents/subagents/<name>.md`
frontmatter to the model with the highest pass@k for its domain.

## pass@k definition

Standard pass@k from the code-eval literature: given `n` samples and `c` passing,
the probability that at least one of `k` randomly-drawn samples passes:

```
pass@k = 1 − ∏_{i=0}^{k−1} (n−c−i)/(n−i)
```

Default `k=3`. Higher = more reliable (a single flaky pass doesn't inflate the score).

## Cost

Every real run routes through `scripts/swarm/delegate.sh`, which selects free-tier
models by default. A full `--all --apply` run with 10 suites × 3 models × k=3
≈ 300 calls, all on free tier (~$0, uses quota). Budget accordingly — run one
domain at a time if quota is tight.

## Extending the suites

Add a case to the relevant `evals/subagents/<domain>.json`. Keep prompts synthetic
(no real patient/customer data — Iron Law: public-safe). The `required`/`forbidden`
keywords are the simplest possible judge; upgrade to an LLM-as-judge rubric only
if keyword matching proves too coarse for a domain.
