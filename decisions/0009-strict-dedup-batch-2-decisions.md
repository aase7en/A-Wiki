---
adr: 0009
title: Strict dedup batch 2 — no further aliases; motion/eval/planning clusters kept
status: Accepted
date: 2026-07-14
tags: [skills, dedup, architecture]
related_journal: []
supersedes: []
superseded_by: []
---

# ADR-0009: Strict dedup batch 2 — no further aliases; motion/eval/planning clusters kept

## Status
**Accepted** — 2026-07-14. Closes the strict-dedup effort (USA-1 §7, C9 + C10).

## Context

USA-1 §7.3 listed ~8–10 dedup candidates. Batch 1 (C9) aliased 3 confirmed
dups (`autonomous-loops`, `diagnosing-bugs`, `root-cause-first` → canonical
winners). Batch 2 (C10) was to resolve the remaining candidates:

1. **Motion trilogy** — merge `motion-foundations` + `motion-patterns` +
   `motion-advanced` into one `motion` skill?
2. **eval-harness vs agent-eval** — same job or distinct niche?
3. **token-optimization Step 7 vs strategic-compact** — overlap to trim?
4. **code-review cluster** — `two-axis-code-review` (mattpocock) redundant?
5. **planning cluster** — `blueprint` / `plan-orchestrate` /
   `planning-and-task-breakdown` / `spec-driven-development` redundant?

The user's binding bar (USA-1 §7.1): a dup candidate must (a) do the **same
job**, (b) have a **clear winner**, (c) have **no hard references**, (d) have
**winner exists + tracked**. Strict — not aggressive.

## Decision

**No further aliases in batch 2.** All five clusters above are
**complementary-but-distinct** under the strict bar — each candidate does a
different job. Documenting the verdicts so future audits don't re-litigate.

### Motion trilogy — KEEP ALL THREE
- `motion-foundations` = base layer (tokens, springs, SSR guards). All others
  depend on it.
- `motion-patterns` = standard UI patterns (button/stagger/modal/scroll).
- `motion-advanced` = drag/gestures/SVG/text-reveal.
- **Verdict**: layered architecture with explicit dependency chain; not a dup.
  (The redundant `motion-ui` monolith was already deleted in the prior
  6-skill dedup, leaving the clean trilogy.)

### eval-harness vs agent-eval — KEEP BOTH
- `eval-harness` = capability/regression eval framework with pass@k / pass^k
  metrics + `.claude/evals/` artifacts.
- `agent-eval` = head-to-head comparison of coding agents (Claude vs Aider vs
  Codex) on YAML tasks via git-worktree isolation.
- **Verdict**: framework vs benchmark — different deliverables, both used.

### token-optimization vs strategic-compact — KEEP BOTH
- grep confirmed `token-optimization/SKILL.md` contains **no** strategic-compact
  overlap (audit cluster 5 was conservative). `token-optimization` = session
  strategy (`/compact` vs `/clear`, model tier); `strategic-compact` =
  PreToolUse hook (`suggest-compact.js`) that nudges at phase boundaries.
- **Verdict**: session-strategy skill vs compaction-timing hook — distinct layers.

### code-review cluster — KEEP
- `two-axis-code-review` (mattpocock) was **renamed** precisely to avoid
  clashing with the built-in `/code-review` slash command.
- **Verdict**: renamed-and-distinct; not a dup.

### planning cluster — KEEP ALL
- `spec-driven-development` → `planning-and-task-breakdown` are an explicit
  sequential pipeline (spec first, then decompose). They cross-reference each
  other — not duplicates.
- `blueprint` differs (multi-session/multi-agent/cold-start briefs +
  adversarial review gate).
- `plan-orchestrate` differs (a `/orchestrate` prompt emitter, not planning).
- **Verdict**: pipeline stages, not redundant.

## Consequences

### Positive
- Strict bar held — no false-positive merges that would lose specialized
  content (motion advanced patterns, eval-harness metrics, etc.).
- Audit closed: every cluster in §7.3 now has a documented verdict, so future
  audits don't re-investigate from scratch.
- Final canonical skill count stays rich enough for all domains (code/debug/
  design/ux-ui/trader/medical/business/data/engineering + extensions) per the
  user's "keep real-use" requirement.

### Negative / Trade-offs
- Skill count does not drop further from C9's 3 aliases. The user's Goal #5
  "ลดจำนวนสกิลมีลดลง ไม่เยอะจนเกินไป" is satisfied by **organization** (domain
  grouping via SKILL-INDEX.md brain, alias resolution table) rather than by
  **aggressive merging**. This matches the user's chosen "เข้มงวด" bar.

## Revisit Conditions

- If a future skill duplicates one of these clusters' exact job → revisit and
  alias per USA-1 §7.2.
- If motion trilogy maintenance burden grows (3 skills drift out of sync) →
  revisit merging into one `motion` skill with sub-sections.
- If eval-harness and agent-eval converge on the same metric set → revisit.

## References

- [`docs/architecture/universal-skill-architecture.md`](../docs/architecture/universal-skill-architecture.md) §7 — strict dedup rules.
- [ADR-0008](0008-universal-skill-architecture.md) — USA-1 spec.
- C9 commit (62daa94) — batch 1 aliased autonomous-loops, diagnosing-bugs, root-cause-first.
- `wiki/SKILL-INDEX.md` — current canonical/alias resolution table (auto-generated).
