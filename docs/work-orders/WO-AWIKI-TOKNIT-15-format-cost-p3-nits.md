# WO-AWIKI-TOKNIT-15 — format-cost P3 nits from PR #98 review

- Date: 2026-11-17
- Agent: GLM (Kilo)
- Branch: `fix/format-cost-p3-nits`
- Status: OPEN

## Context

PR #98 review (VERDICT APPROVE) left two P3 findings on `scripts/format-cost.py`:
1. Dead `import os` — its only usage moved to `scripts/lib/tokenizer_cost.py` in the
   CIHERM/SKILLECO-14 extraction.
2. `_build_counter` performs `sys.path.insert(0, ...)` on every call → duplicate path
   entries when called repeatedly.

## Changes

1. `scripts/format-cost.py`: remove dead `import os`; guard the `sys.path.insert`
   behind a membership check.
2. `tests/test_token_ab_fixtures.py`: RED-first regression — load format-cost via
   importlib, call `_build_counter` twice, assert the lib path appears exactly once in
   `sys.path` (and counter still works).
3. COLLAB: SKILLECO-14 DONE marker rides the docs commit.

## Tests

- RED: new test fails on current code (duplicate insert).
- GREEN: `pytest tests/test_token_ab_fixtures.py tests/test_format_cost.py -q`.

## Review

GLM subagent independent review, anchored `VERDICT` line.

## Evidence

- Filled at close.
