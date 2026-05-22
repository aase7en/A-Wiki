# Project Instructions — All AI Agents

## Autonomous AI Agent Swarm Repository

> **MISSION:** Execute with the uncompromising discipline of a Senior Engineer backed by a dynamic, cost-efficient AI swarm.

## 🚫 Solo Wiki — No Branch, No PR

> **commit ตรงลง `main` เท่านั้น** — ห้ามสร้าง branch, ห้ามเปิด PR, ห้ามใช้ worktree isolation

## 🚨 First action every session (Streamlined for Token Saving)
1. Read `CLAUDE.md` — Active Rules.
2. Run `bash agent-skills/automations/run-task.sh pre-flight` (Iron Law validation).
*Note: Do not load legacy or unrelated skills until explicitly invoked.*

## 🛡️ Iron Laws (Applied IMMEDIATELY)

| Law | Rule | Enforcement |
|-----|------|-------------|
| #1 | NO production code without a **failing test first** | scrutinize SKILL.md |
| #2 | NO bug fixing without **root cause investigation first** | debug-mantra 4-step process |
| #3 | If parallel model violates #1 or #2 → **DISCARD + REWRITE** | Primary Agent as Senior Critic |

## 🧠 Swarm Roles

| Role | Model Selection | Responsibility |
|------|----------------|----------------|
| **Architect** | OpenRouter free reasoning/CoT model | Planning, root cause, design |
| **Executioner** | OpenRouter free flash/coder model | Code writing, tests, refactoring |
| **Senior Critic** | Primary Agent (you) — NOT delegatable | Validate ALL outputs against Iron Laws |

## 📁 Path conventions per agent

| Concept | Claude Code | Codex / OpenAI |
|---------|-------------|----------------|
| Config dir | `.claude/` | `.codex/` |
| Skills (legacy) | `.claude/skills/` (via link-skills.sh) | `.agents/skills/` |
| **Swarm Skills (NEW)** | `.claude/skills/` (via link-my-skills.sh) | `.codex/skills/` (via link-my-skills.sh) |

## Core Knowledge (safeguarded archive)

All original wiki content, docs, decisions, and journals are in `core-knowledge/`.
This is a **read-only archive**. New content lives in `agent-skills/`.
