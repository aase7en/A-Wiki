# WO-AWIKI-CIHERM-12 — Fresh-clone FTS index self-build in tests

- Date: 2026-11-16
- Agent: GLM (Kilo)
- Branch: `fix/fresh-clone-fts-index`
- Status: OPEN

## Context

Independent reviewer of PR #94 (2026-11-16) found: on a **fresh clone** of `origin/main`,
first `pytest tests/test_conductor.py -q` run yields 73 passed + 1 failed —
`TestBridgeSearch::test_search_fts_returns_structured_hits`. Reviewer reproduced the identical
failure on a fresh `origin/main` clone: pre-existing, not a PR #94 regression.

## Root cause

- The test asserts non-empty FTS hits for `"esp32 lora"`, which requires the generated
  `.wiki-index.db` (gitignored) at repo root.
- CI is green because `ci-core.yml` ("Prepare local generated config") runs
  `python scripts/build-wiki-index.py` before tests.
- A fresh dev clone has no index until something builds it → first run fails; subsequent runs
  pass once any workflow (e.g. `gen-index.py`) has built it. Env-coupled test, same family as
  WO-AWIKI-CIHERM-11.
- `TestBridgeSearch::test_search_hybrid_mode_is_default` shares the coupling (hybrid downgrades
  to FTS on missing vector deps; FTS with no index also returns no hits), even though the
  reviewer only observed the fts test fail.

## Options considered

- **A (chosen). Session fixture self-build:** `tests/conftest.py` gains a session-scoped
  autouse fixture that runs `scripts/build-wiki-index.py` via subprocess **only when
  `.wiki-index.db` is absent** — mirrors CI prep semantics exactly; no-op where the index
  exists; keeps the real-content assertions intact.
- **B. Skip-if-no-index:** hides the coupling and reduces coverage — rejected.
- **C. Fully hermetic fixture wiki index:** `search_wiki` resolves scripts relative to the
  package repo root, so hermetic would require a search-path refactor — out of proportion.

Decision: A. Jev/Terra unavailable (same disclosure as CIHERM-11).

## Changes

1. `tests/conftest.py`: session-scoped autouse `_ensure_wiki_index` fixture — subprocess
   `[sys.executable, "scripts/build-wiki-index.py"]` when index missing.

## Tests (RED → GREEN)

- RED: `mv .wiki-index.db .wiki-index.db.hold` → run
  `pytest tests/test_conductor.py::TestBridgeSearch -q` → fts test fails (empty hits).
- GREEN: with fixture added and index STILL held away → same selection passes (fixture
  self-built the index); restore/refresh index afterwards; full
  `pytest tests/test_conductor.py -q` green.

## Review

GLM subagent independent review with anchored `VERDICT` line before merge.

## Evidence

- Reviewer note on PR #94 (fresh-clone failure, reproduced on `origin/main`).
- RED/GREEN transcripts in session log 2026-11-16.
