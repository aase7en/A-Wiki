# WO-AGENT-EVIDENCE-ROADMAP-20260910 — Evidence-native agent engineering roadmap

Date: 2026-09-10 (Asia/Bangkok)
Status: ROADMAP_CAPTURED / GLM_READ_ONLY_AUDIT_READY / DRAFT_PR_59
Owner: GPT-5.6 Sol integrator
Risk: R2 architecture/governance docs
Branch: `docs/agent-evidence-roadmap-20260910`
Base: `origin/main@566637ac8d2636d6c63eda2bd6ebe81b55bd3d72`

## User outcome

Extend A-Wiki and A-Sunday Conductor using current, source-verifiable practices from AI developers, open-source projects, research, and public practitioner communities. Prefer reuse/copy-and-adapt over rebuilding when license and architecture allow it.

This WO captures roadmap decisions only. It does not authorize implementation, package installation, new always-on prompt growth, provider traffic, secret access, or changes to A-Conductor runtime authority.

## Brain Gate

- Gain: evidence-backed external-pattern adoption, agent trace/eval/security/memory provenance, and a safer path to reuse community work.
- Shape: one research appendix plus the existing canonical roadmap; no parallel roadmap or skill registry.
- Weight: roadmap-only now; future runtime features stay local/on-demand/adapter-first.
- Safety: public sources only; no private social scraping, secrets, PHI, raw private traces, or hidden reasoning in Git.
- Verify: source/date/license, scope/diff/UTF-8/privacy, and exact-SHA review before merge.

## Authority / non-duplication boundary

A-Wiki remains policy, knowledge, memory-promotion, skill-registry, and cross-project brain authority. A-Conductor remains runtime execution, scheduling, worker/provider admission, durable job/evidence, and operator-control authority.

Every future node uses `REUSE -> WRAP -> EXTEND -> BUILD`. A matching capability blocks a second implementation unless an explicit owner/adaptor migration decision says otherwise. External instruction bundles are delta-diffed; never pasted wholesale into `AGENTS.md`.

## Research standard

Evidence priority: repository/source/official docs; reproducible evaluation; public developer-community reports as corroboration; inaccessible/private communities are not reconstructed or cited. Adopted patterns record source/date/license/failure modes/overlap and `REUSE/WRAP/EXTEND/PATTERN_ONLY/REJECT`.

## Roadmap decisions

1. external-pattern evidence gate;
2. sanitized A-Conductor execution-evidence bridge;
3. agent-evaluation corpus separating correctness, safety, robustness, efficiency;
4. evaluator self-tests and repeated trials where needed;
5. provenance/trust quarantine for agent/tool memory candidates;
6. cross-repo policy/capability attestation;
7. public/authorized evidence radar creating candidates only.

## Copy-and-development rule

Copy/adapt source only when the exact upstream license is compatible and the implementation WO records upstream ref plus required notice. Prefer a narrow tested primitive/protocol shape over vendoring an entire framework. Current permissive candidates include Ponytail (MIT), Pydantic AI (MIT), AgentDojo (MIT), smolagents (Apache-2.0), and OpenTelemetry semantic conventions (Apache-2.0). License permission does not imply architectural fitness or service authorization.

## Execution priority overlay

1. Current READY/P0 authority wins; existing higher-priority work stays ahead.
2. Parallel-safe read-only archaeology/overlap/evaluator/threat/source work may proceed now.
3. Phase 14 evaluator truth is the normal first future implementation candidate after a fresh gate.
4. Phases 12/15/16 are assessed as trust prerequisites before scale-up where current architecture requires them.
5. Phase 13 waits for the matching accepted A-Conductor runtime evidence contract.
6. Phase 17 evidence radar remains candidate-generation and lower than core execution/verification/security/continuity.

No phase becomes READY from this ordering alone.

## GPT × GLM parallel contract

GPT-5.6 Sol owns architecture, cross-repo boundaries, SSoT reconciliation, trust/security decisions, acceptance, merge, and release.

GLM/ZCode gets one bounded read-only evidence lane that does not steal mutable capacity.

### Task packet `GLM-XREPO-EVIDENCE-RO1`

Status: `READY / READ_ONLY / PARALLEL_SAFE / NO SOURCE MUTATION`

Goal: audit A-Wiki Phases 12–17 and A-Conductor AEET-0..8, prove existing coverage/ownership, identify real gaps, and propose only the smallest reuse-first future slices.

Startup:
1. fetch both repos; record exact live SHAs;
2. A-Wiki: `BRAIN-ENTRY -> PROJECT-GRAPH -> AGENTS -> COLLAB -> this WO -> research evidence -> vNext roadmap`;
3. A-Conductor: `00-AGENT-ENTRY -> PROJECT-GRAPH -> AGENTS -> actual Git/claims -> CURRENT-WORK -> COLLAB -> WO171 -> PROJECT-PLAN`;
4. inspect A-Conductor Issue #233; use it as owner-map authority/destination, never create a parallel owner map;
5. recover live PRs/branches/claims before relying on older docs.

Required result table:
`roadmap node | existing owner | exact path/symbol/test evidence | OWNER/CONSUMER/ADAPTER/FALLBACK | REUSE/WRAP/EXTEND/BUILD | proven gap | risk | dependency | smallest next slice`.

Also identify roadmap nodes that can close `REUSE / NO NEW IMPLEMENTATION`, candidate evaluator fixtures from existing defects, stale/conflicting authority docs, and blockers as `UNVERIFIED`. Finish with exactly one recommended next safe mutation candidate or `NONE`.

Forbidden: editing either repo; implementation branches/worktrees/claims; changes to source/tests/docs for this audit; WO168/169/Zero-Relay worktrees; credentials/config/workers/processes/DB/private Drive/secrets; new scheduler/task/review/claim/lease/model-policy/trace/memory authority; hidden chain-of-thought/private tool payloads.

Result destination: one Issue #233 comment titled `GLM-XREPO-EVIDENCE-RO1 RESULT`, including exact inspected SHAs. Do not merge.

Known transport note: latest Windows independent-review attempt on Issue #233 reached ZCode but failed before model review with CoinTH/Anthropic `HTTP 401 invalid_key`. If still current, classify `UNVERIFIED / PROVIDER_TRANSPORT_BLOCKED`; never weaken auth or expose secrets to bypass it.

## Mutation scope

Roadmap-capture files only: this WO, research appendix, vNext roadmap, bounded claim row. No production code/hooks/skills/registry/memory/private data.

## Dispatch checkpoint

This WO is the stable pointer. At task start, fetch and pin live PR #59, PR #244, PR #243, A-Conductor main, and claims. Run only `GLM-XREPO-EVIDENCE-RO1`. GPT continues architecture/reconciliation; no roadmap source implementation or priority inversion is authorized.