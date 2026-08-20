# A-WIKI KERNEL — The Stable Contract

> Status: **normative** (vNext Phase 3). This document, `config/awiki.yaml`,
> `config/integrations.yaml`, and `schemas/` form the kernel contract surface.
> Changing any of them is an architecture decision requiring review.
> Parents: `docs/migration/awiki-vnext-plan.md` · roadmap · deltas (D-CTX-001..012).

## 1. Identity — what A-Wiki IS and IS NOT

A-Wiki is the **universal personal AI team OS / second-brain kernel**: one brain,
many agents, many projects, many models, one durable workflow + governance layer.

| The kernel IS | The kernel IS NOT |
|---|---|
| memory + knowledge contracts | an implementation monolith for product code |
| task / review / handoff contracts | a chat transport between agents |
| capability policy + routing rules | hardcoded vendor/model policy |
| safety, privacy, claims, gates | an orchestrator daemon (contracts only until Phase 12+) |
| skills registry + generated surfaces | hand-maintained per-vendor instructions |

Projects **attach** to A-Wiki (`.awiki/` adapter, Phase 4); A-Wiki is never
copied into projects (D-CTX-002 anti-duplication).

## 2. Contract surface (this phase)

| Artifact | Role |
|---|---|
| `config/awiki.yaml` | stable kernel config contract (boundaries, vocabulary, gates) |
| `config/integrations.yaml` | integration registry — every external module, default-off |
| `schemas/awiki-task/v1.schema.json` | durable task envelope (extends work-orders + task_board) |
| `schemas/awiki-review/v1.schema.json` | review state + findings lifecycle (extends Review Bus practice) |
| `schemas/awiki-handoff/v1.schema.json` | resume envelope (extends handoff.md chunk system) |
| `schemas/awiki-integrations/v1.schema.json` | registry schema (validated by `scripts/health/validate_integrations.py`) |
| this document | the prose normative contract |

## 3. Agent roles & capability vocabulary (vendor-neutral)

Stable policy is expressed as **capabilities**, never agent/model/provider
names (D-CTX-007). Vendor names appear only as `preferred` runtime candidates.

- Roles: `executor` · `reviewer` · `architect` · `tester` — assigned by
  capability requirement + independence constraints (`independent_from`).
- Closed capability enum lives in `schemas/awiki-task/v1.schema.json`
  (`repository-read/write`, `shell`, `tests`, `code-review`, `deep-reasoning`,
  `architecture-review`, `security-review`, `long-context`, `web-research`,
  `documentation`, `translation`, `data-analysis`, `independent-judgement`,
  `project-code-context`, `symbol-search`, `call-graph`, `blast-radius`,
  `memory-read`, `memory-write`). Context/memory capabilities mirror what the
  integration registry advertises, so tasks can request exactly what providers
  offer — one vocabulary across kernel/task/handoff/registry contracts.
- Agent availability states (runtime only, never committed policy):
  `AVAILABLE BUSY DEGRADED QUOTA_LOW QUOTA_EXHAUSTED RATE_LIMITED COOLDOWN
  OFFLINE AUTH_REQUIRED UNKNOWN`.
- Execution modes: `AUTO SOLO PAIR ARCHITECT_EXECUTOR PARALLEL COUNCIL SWARM`.
  AUTO picks the lightest sufficient mode; when independent review is required
  but unavailable: `independent_review: pending`, never fabricated (§12
  degraded-mode rules in the orchestrator roadmap).

## 4. State boundaries

### Durable vs runtime (enforced by CI + baselines)

- **Durable (committed, reviewable):** git branches/commits, `awiki-task/v1` +
  `awiki-review/v1` + `awiki-handoff/v1` records, kernel config, ADRs/protocols.
- **Runtime (machine-local, regenerable, NEVER committed as policy):** model
  pool + provider telemetry (untracked since P1.3), agent availability/quota,
  claim leases (TTL self-reaping), code-context caches, live `handoff.md`
  working copy (gitignored; `.example` tracked).

Full table: `config/awiki.yaml → state_boundaries`.

### Control-plane vs project state (D-CTX-009)

```text
A-Wiki control plane                    project repo
─────────────────────                   ────────────
project registry / adapter metadata     implementation code
task/review/handoff state               project tests + ADRs
reusable knowledge + promotion rules    deployment config
capability/safety/privacy policy        product-specific plans
```

The control plane **points at** project work (`repo`, `branch`, `head_sha`,
`status`) without swallowing it. One A-Wiki supervises many repositories.

## 5. Memory promotion contract (D-CTX-010)

The ONLY path from project experience to global knowledge:

```text
Project Experience → Distill → Privacy Check → Generalize → Evidence Check → Global Promotion
```

Promote: reusable patterns, decisions, tests, failure modes, generalized
lessons. Never promote: raw agent chatter, private/project data, customer
secrets, temporary notes, source-code excerpts. Default is
`manual-with-evidence` (an `awiki promote-memory` command is a Phase 5
candidate, not a Phase 3 deliverable).

## 6. ProjectCodeContextProvider — G0 CONTRACT ONLY

Vendor-neutral project code-context plane (graft plan §5). A-Wiki Knowledge
Graph ≠ Project Code Graph; the latter is ephemeral, project-local, regenerable.

Operations (the durable workflow vocabulary — vendor tool names stay debug-only):

- `status` — provider health/availability for a project
- `orient` — repo map / subsystem boundaries (budget-aware)
- `find` — symbol/implementation lookup by query
- `file_api` — signatures-only file API
- `trace` — call/reference traversal (direction + depth; blast radius)
- `search` — graph-aware pattern search, ranked by coupling
- `freshness` — pre-query working-tree freshness probe

Provider routing rule: no provider needed → native file/grep; one sufficient →
enable one; degraded → fallback; **never load all providers because they
exist**. Graft is registered `MODULE + PATTERN`, `default: false`, `lazy: true`,
`storage: local-regenerable-cache, commit: false` (registry entry is the
contract; installation/adapter/benchmark are Phase 10+ / G1–G4). The
freshness pattern (`probe → answer|refresh-only-what-is-consumed`) is absorbed
as a pattern regardless of provider choice.

## 7. Integration gate

Every external repo/tool enters through `docs/protocols/integration-intake`
checklist → classification `CORE | MODULE | PATTERN | REFERENCE | REJECT` →
decision record → **then** a `config/integrations.yaml` entry. External
modules are default-off + lazy; A-Router / project profiles enable the minimum
set per active task (progressive disclosure, D-CTX-004/005). The registry is
validated deterministically on every wiki-health/CI run.

## 8. Review, task, and handoff contracts

- **awiki-review/v1** — verdicts `PASS / PASS_WITH_NOTES / CHANGES_REQUIRED /
  BLOCK`; findings carry stable ids (`R-*-NNN`), severities
  `blocker/major/minor/note`, lifecycle `open→addressed→verified` (+ `wont_fix`,
  `superseded`); every cycle is attributable to exactly one HEAD SHA; a new SHA
  invalidates an older approval; unresolved blockers prevent READY.
- **awiki-task/v1** — capability-based assignment, mechanical acceptance,
  claims as file/path leases (extends `task_board`), stop states including
  `security_stop` / `data_loss_stop` (immediate-report rules).
- **awiki-handoff/v1** — resume evidence: decisions, tests, risks,
  `reproduce_commands`, and `context_queries` the receiver re-runs fresh
  instead of trusting copied prose. No private chain-of-thought, ever.

Durable transport today: git branch / PR / commit SHA / review files /
machine-readable state (Review Bus). New transports (MCP, queues) normalize
into the same contracts via adapters.

## 9. Hard invariants (already enforced)

1. No scheduled automation mutates `main` ungated (Phase 1 promotion gates).
2. Runtime telemetry never churns git (P1.3 + scan_repo baselines).
3. Hard safety has CI parity across agent vendors (ci-core smokes).
4. Wiki health is truthful, portable, and ratcheted (Phase 2).
5. Claims block conflicting writes; dirty WIP is never silently rebased (DISC-001).
6. `raw/` immutable; public/private boundary enforced by privacy gates.
7. Contracts change only via review — this file included.

## 10. Roadmap hooks (explicitly NOT this phase)

Project adapter `awiki attach/status` (Phase 4) · memory layers + promotion
command (Phase 5) · hook engine consolidation (Phase 6) · model control plane
(Phase 7) · eval/promotion split + first reviewer adapter (Phase 8) · A-Loop v2
(Phase 9) · external modules incl. any Graft installation (Phase 10) ·
orchestrator phases 12–16 per the roadmap.
