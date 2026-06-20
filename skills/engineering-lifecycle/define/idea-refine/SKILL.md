---
name: idea-refine
description: Structured divergent/convergent thinking to turn vague ideas into concrete proposals. Use when you have a rough concept that needs exploration before it's ready for a spec.
source: addyosmani/agent-skills@v0.6.2
adapted_for: A-Wiki
---

# Idea Refinement

## Overview

Not every idea arrives fully formed. When you have a rough concept — something in the direction of what you want but not yet concrete — this skill helps you explore the possibility space (diverge), then converge on the most promising path. It's the gap between "I have an idea" and "I have a spec."

## When to Use

- You have a rough concept that needs exploration
- You're early in a project and want to consider multiple approaches
- You have a vague requirement like "we should make this better"
- Before committing to a specific direction

**When NOT to use:** You already know exactly what you want. Skip to `spec-driven-development` or `grill-me`.

## The Process

### Phase 1: Diverge — Expand the Possibility Space

Generate multiple directions without evaluating them yet:

1. **Restate the goal** in your own words. Confirm with the user.
2. **List dimensions** that could vary: scope, technology, user experience, timeline, risk appetite
3. **Generate at least 3 approaches** (minimum) — for each approach, describe the shape in 2-3 sentences
4. **Add one wildcard option** — something unconventional that might work

Aim for breadth over depth at this stage. Don't optimize yet.

### Phase 2: Converge — Evaluate and Select

Narrow to one direction with an explicit rationale:

1. **Define evaluation criteria** (with the user): cost, speed, maintainability, learning opportunity, risk
2. **Score each approach** against the criteria — qualitative is fine ("high," "medium," "low")
3. **Surface the tradeoffs** — every choice has a cost; name it explicitly
4. **Recommend one direction** with the rationale for why the others didn't win
5. **Document discarded options** briefly — saves re-debating them later

### Phase 3: Next Step

Based on the converged direction, recommend the next skill:

- Ready to define requirements → `spec-driven-development`
- Still need to interview the user → `grill-me`
- Clear enough to plan → `planning-and-task-breakdown`

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The first idea that comes to mind is probably right" | First ideas are often the most obvious — rarely the best. The best option often appears second or third. |
| "Exploring alternatives wastes time" | Committing to the wrong direction wastes far more time. Idea refinement takes 5-15 minutes at most. |
| "I have enough experience to skip exploration" | You still benefit from having options to choose from explicitly rather than converging on the first approach unconsciously. |

## Red Flags

- Only one approach considered
- Evaluation criteria not shared with the user
- Tradeoffs not stated explicitly
- The "winner" was decided before the process started
- Discarded options not documented — they'll come back

## Verification

- [ ] At least 3 approaches documented (plus optional wildcard)
- [ ] Evaluation criteria defined with the user
- [ ] Tradeoffs named for the selected approach
- [ ] Discarded options recorded with reasons
- [ ] Next step skill identified (spec, grill-me, or plan)
