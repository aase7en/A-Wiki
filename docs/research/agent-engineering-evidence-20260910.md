# Agent Engineering Evidence Map — 2026-09-10

Status: research evidence for roadmap decisions; not implementation authority.
Checked: 2026-09-10. Public sources only.

## Evidence rule

Facts below come from current public source code/docs/issues, reproducible research, or public practitioner discussions. Community reports are treated as signals, not proof. Private/inaccessible Discord, Facebook, WhatsApp, or closed-group claims were not inferred or cited.

Adoption labels:
- `REUSE`: existing A-Wiki/A-Conductor capability already covers it; strengthen rather than duplicate.
- `WRAP`: consume an external interface/pattern behind existing authority.
- `EXTEND`: add a missing bounded capability to an existing owner.
- `PATTERN_ONLY`: borrow the design lesson, not the implementation.
- `REJECT`: conflicts with current authority/safety/cost model.

## 1. Minimality / over-engineering

**Ponytail independent benchmark** — https://github.com/DietrichGebert/ponytail/issues/236
- Corrected v3 used the real plugin, executable grading, 24 jobs × 4 levels × 5 repeats = 480 builds.
- Reported ~44% less code / ~53% fewer logical statements without measured correctness/security loss, but worse robustness on 5 jobs with unstated edge cases, increasingly at stronger modes.
- Decision: `EXTEND` A-Wiki review/think policy and A-Conductor coding-agent policy with risk-adaptive minimality; never optimize LOC alone.
**Ponytail maintainer benchmark notes** — https://github.com/DietrichGebert/ponytail/blob/main/benchmarks/README.md
- Maintainer explicitly records that the original single-shot baseline overstated the effect and links independent benchmarks.
- Cost effects are model-dependent; shorter generated code does not guarantee lower reasoning/token cost on every model.
- Decision: benchmark A-Wiki/A-Conductor on its own models/tasks before enabling minimality by default.

**Practitioner signals**
- Reddit: https://www.reddit.com/r/OpenaiCodex/comments/1vzbd3v/experiences_with_ponytail_andor_caveman/
- Hacker News: https://news.ycombinator.com/item?id=49592706
- Reports are mixed: useful for bounded/new code and reviewer cleanup; risky as a broad refactor rule; several commenters argue reducing concepts/cognitive load is a better target than reducing LOC.
- Decision: minimality runs after task understanding and before implementation/review; default OFF for safety-critical state machines and broad refactors until benchmarked.

License: Ponytail MIT — https://github.com/DietrichGebert/ponytail/blob/main/LICENSE

## 2. Durable execution / effective capability truth

**Pydantic AI durable execution** — https://pydantic.dev/docs/ai/capabilities/durable_execution/overview/
- Durable execution is designed for progress preservation across transient failures/restarts and long-running/HITL workflows.
- A-Wiki/A-Conductor already owns durable job/recovery machinery; adopting Temporal/DBOS/etc. wholesale would duplicate authority.
- Decision: `REUSE/PATTERN_ONLY`, not framework replacement.
**Stable operation identity** — https://github.com/pydantic/pydantic-ai/blob/main/docs/capabilities/custom.md and https://pydantic.dev/docs/ai/capabilities/durable_execution/backends/
- Durable operations need stable capability IDs and operation names because recovery/replay uses persisted identities.
- Backend guidance warns that a side effect can happen before its checkpoint commits, so durable operations should be idempotent or use suitable at-most-once semantics.
- Decision: audit A-Conductor's existing task/execution/operation identities before adding anything; `EXTEND` only missing replay/version invariants.

**Silent durability-loss incident** — https://github.com/pydantic/pydantic-ai/issues/6911
- A real Prefect probe showed a capability override could silently remove durability and make model/tool work run non-durably with no warning.
- Decision: configuration is not proof of effective behavior. Add policy/capability attestation with fail-closed required-capability checks before broad autonomous execution.

License: Pydantic AI MIT — https://github.com/pydantic/pydantic-ai/blob/main/LICENSE

## 3. Instrumentation / execution evidence

**Hugging Face smolagents** — https://huggingface.co/docs/smolagents/en/tutorials/inspect_runs
- The project describes agent runs as difficult to validate/debug and treats instrumentation as necessary in production; it adopted OpenTelemetry for run inspection.
- Decision: `EXTEND` A-Conductor's existing durable evidence with structured traces; do not replace its SQLite/job/evidence SSoT.

**OpenTelemetry GenAI conventions** — https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/
- Provides common identities for agent, operation, conversation, tools, provider/model and usage/evaluation telemetry.
- Explicitly warns that input/output/system instructions/retrieval text can contain sensitive or PII data.
- Decision: metadata-first tracing; prompt/tool payload content OFF by default; optional local/export adapter only.
**Semantic-convention maturity** — https://opentelemetry.io/docs/specs/semconv/
- Semantic conventions provide cross-library naming, but GenAI conventions are still evolving/moving between repositories.
- Decision: store an internal versioned A-Conductor event schema and map/export to a pinned OTel GenAI version; OTel must not become runtime authority.

License: OpenTelemetry semantic conventions Apache-2.0 — https://github.com/open-telemetry/semantic-conventions

## 4. Trace inspection / replay / evaluation

**SWE-agent trajectories** — https://swe-agent.com/latest/usage/trajectories/
- Per-run outputs include trajectory data, exact run configuration, logs and exit statuses; evaluation is a separate step.
- Decision: `PATTERN_ONLY`: A-Conductor should preserve observable action/tool/process events + config/evidence manifest separately from evaluation verdicts.
- Privacy deviation: do not persist hidden model chain-of-thought. A-Wiki/A-Conductor traces record observable operations/results metadata and bounded/redacted evidence only.

**Hugging Face community evaluation guide** — https://huggingface.co/blog/phranzia/how-to-evaluate-ai-agents
- Recommends representative tasks, controlled environments, observable traces and repeated trials.
- Decision: evaluation must separate outcome success, constraints/safety, robustness and efficiency. Efficiency comparisons are valid only among runs that first satisfy required outcome/safety gates.

**Ponytail benchmark corrections** also prove evaluator quality matters: faulty/ambiguous gates can manufacture apparent regressions or wins.
- Decision: every material benchmark suite gets known-good + known-bad evaluator self-tests before model spend or routing-policy promotion.
## 5. Agent security / provenance / inter-agent trust

**OWASP AI Agent Security Cheat Sheet** — https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html
- Threats include tool abuse, exfiltration, memory poisoning, goal hijacking, excessive autonomy, approval manipulation, cascading multi-agent failures, sensitive logging, denial-of-wallet and supply-chain compromise.
- Decision: agent/tool/memory/provider inputs are trust-boundary data; authorization and high-impact action gates remain deterministic and outside model confidence.

**AgentDojo (ETH Zurich / NeurIPS benchmark)** — https://arxiv.org/abs/2406.13352 and https://github.com/ethz-spylab/agentdojo
- 97 realistic tool-use tasks and 629 security test cases evaluate prompt-injection attacks/defenses over untrusted tool data.
- Decision: build a small A-Conductor/A-Wiki-specific adversarial suite first; import upstream cases/code only if useful and license/fit gates pass.
- License: AgentDojo MIT — https://github.com/ethz-spylab/agentdojo/blob/main/LICENSE

**AgentDyn** — https://github.com/leolee99/AgentDyn
- Extends dynamic/open-ended security evaluation with 60 tasks and 560 injection cases across shopping, GitHub and daily-life scenarios.
- Decision: avoid assuming a static prompt-injection test proves production safety; add evolving/adaptive fixtures where risk warrants it.

**Aider architect→editor trust-boundary issue** — https://github.com/Aider-AI/aider/issues/5058
- A reported/reproduced chain allowed poisoned repository content to influence architect output that was passed to the editor and committed malicious code.
- Decision: `PATTERN_ONLY` negative lesson: planner/reviewer/worker output never gains transitive mutation authority merely because another model produced it.
## 6. Public practitioner/developer signals

**Public X developer post** — https://x.com/qianl_cs/status/2021286707405234490
- Describes a DBOS/OpenAI Agents SDK durable pattern with restart recovery, long-lived workflows, parallel steps, auditing and explicit cancel/resume/fork semantics.
- Signal only; architecture decisions rely on primary durable-execution docs and A-Conductor's existing accepted runtime evidence.

**Reddit production-agent discussions** show recurring concern around state, retries, approvals, observability, permissions and recovery rather than model choice alone. Example: https://www.reddit.com/r/aiagents/comments/1uv3gxc/best_agent_framework_in_2026_there_isnt_one_heres/
- Decision: corroborates the existing A-Conductor direction; no new framework is justified by community popularity.

**Hacker News Ponytail discussions** — https://news.ycombinator.com/item?id=49592706 and https://news.ycombinator.com/item?id=48527946
- Repeated criticism: tiny ruleset wrapped in a large distribution repo; contextual judgment matters; LOC is a weak quality proxy.
- Decision: copy the useful decision ladder/pattern, not the distribution layer, unless a future host specifically benefits from its plugin hooks.

## Adopted synthesis

1. Optimize accepted outcomes, concepts/files/dependencies and maintenance burden — not LOC alone.
2. `DECLARED/CONFIGURED != EFFECTIVELY_BOUND`: prove required runtime policy/capabilities before autonomous action.
3. Trace every material run using local, versioned, privacy-safe observable metadata; raw content capture is opt-in and normally off.
4. Separate execution evidence from evaluation verdicts; keep replay identities stable and operations idempotent where retries can repeat side effects.
5. Treat every agent-to-agent handoff, repository text, tool result and memory candidate as untrusted until the receiving authority validates it.
6. Turn real production failures into deterministic/adversarial eval fixtures; validate the evaluator itself before trusting its score.
7. Feed only sanitized, provenance-bound summaries into A-Wiki memory promotion; traces never auto-promote.
8. Monitor public/authorized upstream/community sources as candidate evidence only; human/repo gates decide adoption.
