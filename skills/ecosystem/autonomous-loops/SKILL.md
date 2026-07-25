---
name: autonomous-loops
description: "DEPRECATED — use continuous-agent-loop instead. Retained as a redirect pointer only; all 611 lines of pattern content have been ported to continuous-agent-loop v2.0.0 (cross-agent: Claude Code / Gemini CLI / Codex / Aider / Hermes). Trigger: 'autonomous loop', 'agent loop'."
version: 1.9.0
author: A-Wiki
origin: ECC
domain: [engineering, automation]
lifecycle_phase: build
category: pipeline
agents: [all]
invocation: manual
status: deprecated
migrated_to: continuous-agent-loop
# 2026-07-25: slimmed to redirect pointer. All content (6 patterns, headless CLI
# cheat-sheet, cross-agent gotchas) ported to continuous-agent-loop v2.0.0.
# This file remains so existing scripts/imports don't break, but no new content
# should be authored here. See skills-registry.json (status: deprecated).
---

# Autonomous Loops → continuous-agent-loop

> **DEPRECATED (2026-07-25).** This skill is retained only as a redirect pointer.
>
> **Use `continuous-agent-loop` instead** — it contains the same 6 patterns
> (sequential pipeline, NanoClaw REPL, infinite agentic loop, continuous-PR loop,
> de-sloppify, RFC-driven DAG) plus a cross-agent headless CLI cheat-sheet
> (Claude Code / Gemini CLI / Codex / Aider / Hermes) and cross-agent gotchas.

## Why deprecated

The original `autonomous-loops` was Claude-only (`claude -p` everywhere). A-Wiki runs multiple agents side-by-side, so a single-vendor loop pattern blocked cost-routing and swarm allocation. All content has been ported to `continuous-agent-loop` and generalized to be agent-agnostic.

## Where to go now

| Want to… | Go to |
|---------|-------|
| Read the patterns | `skills/ecosystem/continuous-agent-loop/SKILL.md` |
| See headless CLI flags per agent | §0 of `continuous-agent-loop` |
| Choose a pattern | §Decision Matrix of `continuous-agent-loop` |
| Avoid common mistakes | §Anti-Patterns of `continuous-agent-loop` |

## If you have scripts calling this skill

They continue to work — this file still exists. But any new loop work should reference `continuous-agent-loop` directly. To migrate, replace:

```diff
- skill: autonomous-loops
+ skill: continuous-agent-loop
```

No behavioral change; same patterns, more agents supported.

## Migration history

| Version | Date | Change |
|---------|------|--------|
| 1.x | (ECC origin) | Full 611-line Claude-only reference |
| 1.8.0 | 2026-07-14 | Marked deprecated in skills-registry.json; `continuous-agent-loop` introduced as canonical name (47-line stub) |
| **1.9.0** | **2026-07-25** | **Slimmed to redirect pointer. Content fully ported to `continuous-agent-loop` v2.0.0 (cross-agent).** |
