# WO-AGENT-EVIDENCE-ROADMAP-20260910 — Evidence-native agent engineering roadmap

Date: 2026-09-10 (Asia/Bangkok)
Status: ROADMAP_CAPTURED / GLM_READ_ONLY_AUDIT_READY / DRAFT_PR_59
Owner: GPT-5.6 Sol integrator
Risk: R2 architecture/governance docs
Branch: `docs/agent-evidence-roadmap-20260910`
Base: `origin/main@566637ac8d2636d6c63eda2bd6ebe81b55bd3d72`

## User outcome

Extend A-Wiki and A-Sunday Conductor using current, source-verifiable practices from AI developers, open-source projects, research, and public practitioner communities. Prefer reuse/copy-and-adapt over rebuilding when license and architecture allow it.

This work order captures roadmap decisions only. It does not authorize implementation, package installation, new always-on prompt growth, provider traffic, secret access, or changes to A-Conductor runtime authority.

## Brain Gate

- Gain: evidence-backed external-pattern adoption, agent trace/eval/security/memory provenance, and a safer path to reuse community work.
- Shape: one research evidence appendix plus additions to the existing canonical roadmap; no parallel roadmap or skill registry.
- Weight: roadmap-only now; future runtime features must be local/on-demand/adapter-first.
- Safety: public sources only; no private social scraping, secrets, PHI, raw private traces, or hidden reasoning in Git.
- Verify: source URL/date/license checks, scope/diff/UTF-8/privacy checks, exact-SHA review before merge.
## Authority / non-duplication boundary

A-Wiki remains the policy, knowledge, memory-promotion, skill-registry, and cross-project brain authority. A-Conductor remains the runtime execution, scheduling, worker/provider admission, durable job/evidence, and operator-control authority.

Every future node must run `REUSE -> WRAP -> EXTEND -> BUILD` in that order. A matching capability already present in either repository blocks a second implementation unless an explicit owner/adaptor migration decision says otherwise.

External instruction bundles are never pasted wholesale into `AGENTS.md`. Adopt only evidence-backed deltas after diffing existing Iron Laws, A-Suite skills, hooks, and protocols.

## Research standard

Evidence priority for a roadmap decision:
1. repository/source code, issue reproducer, official specification or first-party docs;
2. peer-reviewed/reproducible benchmark or independent executable evaluation;
3. public developer-community reports (Reddit, Hacker News, public X, Hugging Face community) as corroboration, not sole authority;
4. inaccessible/private Discord, Facebook, WhatsApp, closed groups, or unverified screenshots are not cited as evidence.

Each adopted pattern records source, date checked, license when code reuse is possible, known failure modes, A-Wiki overlap, and `REUSE/WRAP/EXTEND/PATTERN_ONLY/REJECT` classification.
## Roadmap decisions

1. Add an external-pattern evidence gate before adopting new agent frameworks/rulesets.
2. Add a sanitized execution-evidence bridge from A-Conductor into A-Wiki; traces are evidence, never automatic canonical memory.
3. Add an agent-evaluation corpus that separates outcome, constraint/safety, robustness, and efficiency metrics; no single blended score may hide a security failure.
4. Add evaluator self-tests and repeated trials before using benchmark results for routing or policy changes.
5. Add provenance/trust labels and quarantine for untrusted tool/agent-derived memory candidates.
6. Add a cross-repo policy/capability-attestation contract: A-Wiki defines required policy identities; A-Conductor proves effective runtime binding.
7. Add a public/authorized evidence radar that creates review candidates only; it never auto-promotes community claims into global knowledge.

## Copy-and-development rule

Source copying is permitted only when the exact upstream license is compatible and the implementation WO records the upstream commit/tag plus required notice/attribution. Prefer importing a narrow tested primitive or adapting a protocol shape rather than vendoring an entire framework.

Current compatible examples verified for roadmap consideration: Ponytail (MIT), Pydantic AI (MIT), AgentDojo (MIT), smolagents (Apache-2.0), and OpenTelemetry semantic conventions (Apache-2.0). License permission does not imply architectural fitness or permission to call an external service.

## Mutation scope

Allowed: this WO, `docs/research/agent-engineering-evidence-20260910.md`, `docs/migration/awiki-vnext-plan.md`, and the conductor-managed claim row in `COLLAB.md`.
Forbidden: production code, hooks, skills, registry, memory implementation, raw/private data, A-Conductor repository files, and the user's local-only `main@3a4e0fba...` commit.

## Execution priority overlay — preserve the current frontier

The new Phases 12–17 are future capability work, not a reason to reorder the current project. Execution follows this priority overlay:

1. **Current READY/P0 authority first.** Whatever the live `conductor status`, active WO, exact-SHA review, or release gate says is already higher priority remains ahead of this roadmap.
2. **Parallel-safe groundwork now.** Read-only archaeology, overlap mapping, evaluator/test inventory, threat-model inventory, and source/license re-verification may proceed without claiming a mutable implementation lane.
3. **First future implementation candidate: evaluator truth.** Phase 14 evaluator self-test/baseline should normally precede any optimization policy that depends on benchmark claims, subject to a fresh live gate.
4. **Trust and provenance before scale-up.** Phase 12 evidence intake, Phase 15 adversarial coverage, and Phase 16 provenance/quarantine are assessed before broadening autonomous mutation or memory promotion where the then-current architecture makes them prerequisites.
5. **Cross-repo evidence bridge only after runtime owner is ready.** Phase 13 waits for the matching accepted A-Conductor execution-evidence/trace contract; A-Wiki does not invent a parallel trace authority.
6. **Evidence radar last among these nodes.** Phase 17 remains candidate-generation only and should not consume implementation capacity needed by core execution, verification, security, or continuity work.

No future phase is activated by this ordering alone. Every mutation still requires a new WO, live ownership check, risk classification, tests/evidence, and appropriate exact-SHA review.

## GPT × GLM parallel contract

GPT-5.6 Sol remains integrator for architecture, cross-repo owner boundaries, SSoT reconciliation, trust/security decisions, acceptance, and merge/release decisions.

GLM/ZCode is assigned a bounded **read-only evidence-audit lane** that can run in parallel without stealing a mutable lane from higher-priority work. Its job is to discover what already exists, prove overlap, and prepare deterministic candidate test/eval slices. It is not authorized to implement Phases 12–17 yet.

### Task packet `GLM-XREPO-EVIDENCE-RO1`

Status: `READY / READ_ONLY / PARALLEL_SAFE / NO SOURCE MUTATION`

Goal: audit A-Wiki and A-Sunday Conductor against the new evidence/AEET roadmaps and produce an evidence-backed reuse map so future implementation starts from `REUSE/WRAP/EXTEND` instead of duplicate `BUILD`.

Required startup:
1. fetch both repositories and pin the exact branch/PR heads before analysis;
2. A-Wiki: read `BRAIN-ENTRY.md -> docs/graph/PROJECT-GRAPH.yaml -> AGENTS.md -> COLLAB.md -> this WO -> docs/research/agent-engineering-evidence-20260910.md -> docs/migration/awiki-vnext-plan.md`;
3. A-Sunday Conductor: read `00-AGENT-ENTRY.md -> PROJECT-GRAPH.yaml -> AGENTS.md -> CURRENT-WORK.md -> COLLAB.md -> docs/work-orders/WO-P1-171-agent-evidence-roadmap.md -> PROJECT-PLAN.md`;
4. read A-Conductor Issue #233 because it is the existing cross-repo authority-dedup gate; do not create a competing owner map.

Audit targets:
- A-Wiki Phases 12–17;
- A-Conductor AEET-0..8;
- existing tests, protocols, stores, event/evidence surfaces, review/claim/lease/provider/model-policy/memory/defect authorities that already satisfy part or all of each target;
- exact duplication/ownership hazards across both repositories;
- the smallest future candidate slices and deterministic tests needed only for proven gaps.

Required result shape:
- one row per roadmap node with `existing owner`, `evidence path/symbol/test`, `REUSE/WRAP/EXTEND/BUILD`, `gap`, `risk`, `dependency`, `smallest next slice`;
- explicit owner class for every cross-repo overlap: `OWNER / CONSUMER / ADAPTER / COMPATIBILITY_FALLBACK`;
- list of roadmap items that should be closed as `REUSE / NO NEW IMPLEMENTATION` if existing evidence already proves them;
- candidate evaluator fixtures drawn from existing real defects, but no new test/code files in this task;
- blockers/unknowns separated from findings; tool/transport failure is `UNVERIFIED`, never inferred PASS/FAIL.

Forbidden:
- editing either repository;
- creating branches/worktrees/claims for implementation;
- changing `AGENTS.md`, skills, hooks, registry, runtime code, tests, memory, private Drive, provider config, worker state, or live databases;
- copying private prompts/tool payloads/hidden reasoning into results;
- proposing a second scheduler, task store, review lifecycle, claim/lease authority, model-policy store, trace SSoT, or memory store.

Result destination: add a durable comment to A-Sunday Conductor Issue #233 titled `GLM-XREPO-EVIDENCE-RO1 RESULT`, including exact repository SHAs inspected. Do not merge anything.

Stop after posting the evidence map. GPT/integrator will reconcile it against the current roadmaps and decide whether any implementation node becomes READY.

## Transport blocker semantics

The latest Windows independent-review attempt recorded on A-Sunday Conductor Issue #233 reached ZCode but failed before model review with CoinTH/Anthropic `HTTP 401 invalid_key`. If that condition is still current when this task is invoked, record `UNVERIFIED / PROVIDER_TRANSPORT_BLOCKED`, do not treat it as a repository failure, and do not weaken authentication or expose a secret value to bypass it.

## Dispatch checkpoint

Roadmap capture is frozen for handoff. GPT continues architecture/reconciliation. GLM executes only `GLM-XREPO-EVIDENCE-RO1` read-only; no source implementation is authorized. Exact candidate heads must be read from the live PRs at task start; do not trust stale embedded SHAs.