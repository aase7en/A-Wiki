# WO-AGENT-EVIDENCE-ROADMAP-20260910 — Evidence-native agent engineering roadmap

Date: 2026-09-10 (Asia/Bangkok)
Status: ACTIVE / DOCS-ONLY ROADMAP CAPTURE
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
