# Model Routing Verification

- generated_at: 2026-06-12 01:41:28 +07
- repo: A-Wiki
- PASS count: 2/3
- threshold: PASS

| Agent | Result | Evidence |
|---|---|---|
| claude | PASS | Use model-cost-switching: tier 4a/4b/4c with effort. |
| codex | PASS | Default 4b, escalate to 4c, de-escalate to 4a. |
| gemini | FAIL | Use the best available model. |
