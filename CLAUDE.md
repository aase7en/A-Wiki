# A-Wiki — Autonomous AI Agent Swarm Repository — Session Rules

> **IRON LAWS ENFORCED.** The Primary Agent MUST read `agent-skills/README.md` before any execution.
> Skills in `agent-skills/engineering/` embed unbreachable boundaries. Do NOT skip them.

## 🚨 First action every session

1. Run `bash agent-skills/automations/run-task.sh pre-flight` — validates git, main branch, Iron Laws.
2. Read `agent-skills/README.md` — understand the Iron Laws and swarm architecture.
3. Read `core-knowledge/README.md` — understand what was safeguarded.
4. Read `.local/profile.md` — owner info (GDrive sync).
5. Read `.local/session-memory.md` — cross-device session continuity (GDrive sync).

## 🔒 Iron Laws (UNBREACHABLE)

1. **NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST.**
2. **NO BUG FIXING WITHOUT ROOT CAUSE INVESTIGATION FIRST.**
   - Use debug-mantra 4-step: Reproduce → Trace → Falsify → Cross-reference.
3. **If a parallel model violates these → DISCARD and REWRITE.**

## 🧠 Swarm Intelligence Protocol

When executing background parallel work:

1. **SCOUT** → Query `agent-skills/swarm-intelligence/model-scouter.md` for free models.
2. **ALLOCATE** → Route Architecht tasks to reasoning model, Executioner to coder model.
3. **VALIDATE** → Primary Agent (Senior Critic) checks ALL outputs against Iron Laws.

## � Directory Structure

```
A-Wiki/
├── agent-skills/          ← ACTIVE LAYER (Iron Laws + Swarm)
│   ├── engineering/       ← debug-mantra, scrutinize, post-mortem
│   ├── productivity/      ← management-talk
│   ├── swarm-intelligence/← model-scouter, agile-swarm
│   ├── infrastructure/    ← git-safety
│   ├── automations/       ← hooks.py, run-task.sh
│   └── extensibility/     ← symlink-connector
├── core-knowledge/        ← SAFEGUARDED ORIGINAL CONTENT
│   ├── wiki/              ← concepts, entities, synthesis, sources
│   ├── docs/              ← protocols, architecture, guides
│   ├── decisions/         ← ADRs
│   ├── journal/           ← daily journals
│   ├── raw/               ← [GDrive] source documents
│   └── exports/           ← [GDrive] NotebookLM bundles
├── skills/                ← Legacy skills (backward compat)
├── scripts/               ← Utility scripts
├── tools/                 ← Prompts
└── .local/                ← [GDrive] profile, sessions, secrets
```

## ✅ Rules

1. **core-knowledge/ is read-only** — do not modify. All new content goes in `agent-skills/`.
2. **agent-skills/engineering/ skills MUST be read before any code execution.**
3. **agent-skills/swarm-intelligence/ MUST be consulted for parallel work.**
4. **Use `scripts/link-my-skills.sh`** to symlink agent-skills into global agent environments.
5. **Session summaries MUST be written to `.local/session-memory.md`** for cross-device carry-over.
6. **Commit directly to main only** — no branches, no PRs.

*Schema v2.0 — Autonomous AI Agent Swarm Repository — 2026-05-22*
