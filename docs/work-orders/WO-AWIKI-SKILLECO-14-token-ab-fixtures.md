# WO-AWIKI-SKILLECO-14 — A/B token measurement fixtures (Thai/English, auto-on/off)

- Date: 2026-11-17
- Agent: GLM (Kilo)
- Branch: `feat/token-ab-fixtures`
- Status: OPEN
- Parent issue: #76 (SKILL-ECO) — "Compare 10+ matched A/B fixtures in Thai/English with
  auto-on/auto-off … explicitly disclose UNKNOWN billing where unavailable."

## Context

Issue #76 requires deterministic regression fixtures + actual A/B token/quality evidence for the
skill-economy track (caveman-style AUTO_ON_DEMAND output compression vs verbose). The standing
claims to ground: "Prompts sent outside: use English (saves ~30% tokens)" (AGENTS.md) and
caveman "~60-65% output tokens saved" (skills/claude-code/token-optimization) — currently
asserted without reproducible fixtures.

## Approach (reuse-first)

- Reuse the proven tokenizer resolver from `scripts/format-cost.py` (`_build_counter`,
  tiktoken → anthropic-key-gated → char/4 proxy) by extracting it verbatim into
  `scripts/lib/tokenizer_cost.py`; format-cost imports the lib (its existing tests guard the
  refactor).
- New deterministic fixtures `tests/fixtures/token_ab_pairs.json`: 12 matched Thai/English pairs
  across everyday A-Wiki output shapes; each language carries `verbose` (auto-off) and
  `compact` (caveman-style auto-on) variants of the SAME semantic content.
- New `scripts/token-ab-measure.py`: measures all variants, emits JSONL records + summary with
  per-pair ratios (thai/english per style, compact/verbose per language), tokenizer backend
  used, and explicit `billing: UNKNOWN` disclosure (offline tokenizer ≠ provider billing).
- Contract tests `tests/test_token_ab_fixtures.py` (RED-first): schema, ≥10 pairs, 4 non-empty
  variants per pair, compact < verbose in bytes (caveman contract), deterministic double-run
  counts, UNKNOWN-disclosure present.

## Alternatives considered

- Import format-cost via importlib hyphen hack — no refactor noise but leaves duplicate
  tokenizer logic; rejected (single source preferred).
- Provider-billed measurement (real API token usage) — non-deterministic, costs quota, needs
  keys in CI; out of scope for fixtures (recorded as billing UNKNOWN disclosure instead).

## Changes

1. `scripts/lib/tokenizer_cost.py` (NEW) — `build_counter(requested)` verbatim from
   format-cost.py.
2. `scripts/format-cost.py` — `_build_counter` delegates to the lib.
3. `tests/fixtures/token_ab_pairs.json` (NEW) — 12 pairs × {thai, english} × {verbose, compact}.
4. `scripts/token-ab-measure.py` (NEW) — measurement harness, JSONL + human output.
5. `tests/test_token_ab_fixtures.py` (NEW) — contract tests.
6. COLLAB claim row (this WO) + CIHERM-12 DONE marker riding this docs commit.

## Tests

- RED: `pytest tests/test_token_ab_fixtures.py -q` fails before files exist.
- GREEN: full `pytest tests/test_format_cost.py tests/test_token_ab_fixtures.py -q` +
  broader core subset; `python scripts/token-ab-measure.py --json | head` smoke.

## Review

GLM subagent independent review, anchored `VERDICT` line, before merge.

## Evidence

- Filled at close: RED transcript, GREEN counts, smoke output, ratios summary.
