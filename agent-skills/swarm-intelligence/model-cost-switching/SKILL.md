---
name: model-cost-switching
description: Choose the cheapest capable primary-model tier and effort before expensive multi-step work, architecture, subagent spawning, or cost-sensitive tasks.
---

# Model-Cost Switching

Use this skill to classify work before spending primary-agent budget. Full policy lives in `docs/protocols/model-switching.md`; source verification lives in `wiki/sources/claude-model-cost-switching-strategy-2026-06.md`.

## Triggers

- Starting a multi-step project, roadmap chunk, feature build, or architecture pass.
- Before spawning subagents or delegating many file reads.
- Before an expensive task, long-context task, or task likely to need model escalation.
- User asks about cost, model choice, Fable, Opus, Sonnet, Haiku, effort, batching, or context compression.
- Work involves trading, real money, irreversible design decisions, or critical review.

## Non-Triggers

- Simple lookup, search, summarization, or verifiable extraction that fits Cost-First Pyramid Level -1 through Level 3.
- Tasks that should route through `docs/protocols/delegation.md` first.
- One-file mechanical edits where the current model is already active and the answer is obvious.

## Decision Algorithm

1. Classify the job: lookup, implementation, architecture, risk, or review.
2. If it fits Level -1, Level 0, Level 1, Level 2, or Level 3, use local/search/delegation/subagent first.
3. If it must use primary-agent reasoning, start at 4b.
4. Use 4a only when the spec is complete and output is easy to verify.
5. Use 4c only for architecture, trading/risk, critical review, or repeated root-cause failure.
6. Pick the lowest effort that still preserves quality: `low`, `medium`, `high`, `xhigh`, or `max`.
7. Cache stable context, batch related architecture questions, and compress handoff context before switching.
8. After any 4c architect pass, write the spec/checklist, then de-escalate to 4b for execution.

## Escalate

- Escalate to 4c when root-cause investigation fails twice or the solution space is still ambiguous.
- Escalate to 4c for real-money paths, trading strategy, risk safeguards, security-sensitive decisions, or irreversible schema/design choices.
- Escalate effort to `xhigh` for complex coding/agentic work with many constraints.
- Use `max` only for one-shot architecture where asking the wrong question later would cost more than the premium.

## De-escalate

- De-escalate to 4b immediately after a 4c architecture/spec phase.
- De-escalate to 4a when the task becomes boilerplate, parsing, formatting, classification, or checklist expansion.
- De-escalate effort from `high` to `medium` or `low` for review passes with clear acceptance criteria.
- Do not keep expensive context active just because it is already open; compact and hand off.

## Mnemonic

| Tier | Thai role | Use |
|---|---|---|
| 4a | ผู้ช่วย | cheap verified helpers: boilerplate, parsing, formatting |
| 4b | ทีมช่าง | default builder: tests, implementation, docs, debugging |
| 4c | สถาปนิก | expensive architect: system design, strategy, critical risk review |

## Output

When useful, state the routing decision in one short line:

```text
Model tier: 4b/high by default; escalate to 4c only for architecture blocker or trading-risk review.
```
