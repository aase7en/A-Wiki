# WO-AWIKI-PIPE-01 — Conductor read-only pipeline status (A-Conductor Inspector seam)

Status: CLAIMED / IN_PROGRESS
Parent goal: A-Wiki Knowledge Pipeline Modernization + A-Conductor integration (operator brief 2026-11-11).
Related: Issue #76 (skill economy), A-Wiki-Conductor Issue #739 (Tool/Hook/Skill Inspector).
Claim: WO-AWIKI-PIPE-01 (COLLAB row, cache id 748050ece0d3) | Agent: GLM (Kilo)
Branch: `feat/conductor-pipeline-status` | Base: `origin/main@f17ec316f3d24f92c6959bf2053fb6831afbad29`
Worktree: isolated fresh clone (macOS, `~/GitHub/A-Wiki`) — Windows shared checkout is stale/dirty and untouched.

## Goal

Expose A-Wiki knowledge-pipeline and skill-routing state to A-Conductor through the
sanctioned brain-side bridge (`python -m conductor ...`), per
`docs/architecture/brain-vs-conductor-division.md` ("if A-Conductor needs a capability,
open a brain-side WO to add it to the bridge"). READ-ONLY projection; no scheduler,
no task DB, no queue, no claim store, no dashboard authority, no A-Wiki-Conductor
mutation.

## Allowed scope

- NEW `conductor/pipeline.py` — evidence-derived projection only.
- `conductor/cli.py` — additive `pipeline` subcommand wiring only.
- NEW `tests/test_conductor_pipeline.py` — RED-first contract tests.
- THIS Work Order; COLLAB.md claim row (written via `python -m conductor claim`) and
  a DONE marker on the merged WO-AWIKI-76-01 row.

Forbidden: `skills-registry.json`, generated skill surfaces, `scripts/skills_registry/**`
(except reading), hooks, A-Wiki-Conductor / SunDayRemoteMCP repos, any write during
status projection.

## Contract (what `python -m conductor pipeline --json` returns)

- `routing`: state READY/DEGRADED/UNKNOWN with a documented classification rule,
  registry counts (canonical/deprecated/alias), router + skill-cards importability
  probes, optional `--query` bounded sample decision (<=3 cards, 0 bodies loaded,
  reuses merged WO-AWIKI-76-01 `build_cards`), MCP `skill_route` presence.
- `ingestion`: source-note count, last `wiki/sources` commit ts (git evidence),
  raw-file count + latest mtime (gitignored tree -> filesystem evidence, labeled),
  ingest tool presence, freshness READY/STALE/UNKNOWN against a documented,
  output-exposed `stale_after_days` threshold.
- `verification`: `surfaces_drift` CLEAN/DRIFT/UNKNOWN via opt-in `--check-drift`
  (`regen-skill-surfaces.py --check`); UNKNOWN by default (fast, honest).

Everything unverifiable is reported UNKNOWN with its evidence source; no invented
values; no mutation (functions only read files, git, and import modules).

## Acceptance / test plan

1. RED: import `conductor.pipeline` fails before implementation.
2. Freshness classifier unit tests (READY/STALE/UNKNOWN/clock-skew-refusal).
3. Real-repo integration: schema keys, counts match `skills-registry.json`,
   classification rule consistency, bounded sample query with 0 body loads,
   labeled evidence sources, drift UNKNOWN without flag, no registry mutation.
4. CLI subprocess tests (`-m conductor pipeline --json`, with/without `--query`).
5. Related: existing conductor suite; privacy/compile checks; Loop-Evidence PR.

## Continuity

Claim committed and pushed before source mutation. After GREEN: freeze exact
candidate SHA, open PR, hosted CI, leave open for independent exact-SHA review
(author does not self-merge). Checkpoint appended below at every stop.

## Checkpoints

- 2026-11-11 claim acquired via `python -m conductor claim` (row in COLLAB.md);
  base `f17ec316`; docs commit first, source second.
