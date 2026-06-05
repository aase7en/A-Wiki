# Cross-Agent Plan Handoff Protocol

> Purpose: make A-Wiki work resumable across Claude Code, Codex, Gemini CLI, Cursor, Windsurf, Cline, Copilot, Antigravity, Ollama/Hermes-style local agents, and any future IDE agent when a chat hits context or rate limits.

## Core Rule

When an agent opens Plan Mode, prepares an implementation plan, or is about to switch tools/agents, it must split the work into small checkpointable chunks and write the current state to `handoff.md`.

`handoff.md` is local and gitignored because it can contain live work context. The tracked source of truth for its shape is `handoff.md.example`.

## Required Plan Shape

Every plan must use chunks small enough for another agent to resume without reading the whole previous conversation.

| Field | Required content |
|---|---|
| ID | Stable chunk ID such as `P1.1`, `P1.2`, `BUG-1`, or `DOC-1` |
| Status | `todo`, `doing`, `done`, `blocked`, or `skipped` |
| Goal | One concrete result, not a broad phase name |
| Files | Exact files expected to change or be inspected |
| Verify | Command, test, visual check, or review evidence |
| Handoff note | What the next agent must know before continuing |

Recommended chunk size: one focused behavior, one wiki page, one protocol update, or up to 3 closely related files. If a chunk grows beyond that, split it before coding.

## When To Update `handoff.md`

Update `handoff.md` at these checkpoints:

| Trigger | Required update |
|---|---|
| Plan approved or summarized | Add task board with chunk IDs, files, and verify commands |
| Chunk completed | Mark chunk `done` and add evidence |
| Work is paused, blocked, or limit is near | Fill `Resume Here`, `Blocked`, and `Next Command` |
| Switching Agent/IDE/device | Run `bash scripts/swarm/agent-switch.sh` or update manually |
| Session end after significant work | Mirror durable summary to `wiki/context/session-memory.md` and `log.md` |

If `handoff.md` is missing, run:

```bash
cp handoff.md.example handoff.md
```

or run:

```bash
bash scripts/swarm/agent-switch.sh
```

The script bootstraps `handoff.md` from the example if needed.

## Resume Order For The Next Agent

1. Read platform rules: `AGENTS.md` plus the current tool file (`CLAUDE.md`, `GEMINI.md`, `.clinerules`, etc.).
2. Read `handoff.md`.
3. Read only the referenced canonical file, such as a project roadmap, `wiki/context/session-memory.md`, or a specific protocol.
4. Continue from `## Resume Here`; do not restart old completed chunks.
5. After finishing a chunk, update `handoff.md` before doing unrelated work.

## State Hierarchy

| File | Role | Git policy |
|---|---|---|
| `handoff.md` | Live local checkpoint for current cross-agent work | ignored |
| `handoff.md.example` | Public-safe template and schema | tracked |
| `wiki/context/session-memory.md` | Local/private rolling cross-session TODOs and decisions | ignored |
| `log.md` | Local/private session history | ignored |
| Project roadmap/HANDOFF | Durable project-specific source when explicitly tracked | case-by-case |

If a project has its own roadmap or `HANDOFF.md`, that file is canonical for product details. Root `handoff.md` should point to it and say exactly where to resume.

## Public-Safe Boundary

Never put these in `handoff.md.example`, tracked docs, or chat:

- API keys, tokens, credentials, cookies, or `.env` values
- raw/private file contents
- customer data, analytics, personal notes, or private journal text
- machine-specific secret paths

For private details, write a pointer such as `see drive/personal/... locally` without copying the content.

## Agent Compatibility

| Agent/IDE | Expected behavior |
|---|---|
| Claude Code | Use hooks and `scripts/swarm/agent-switch.sh`; keep `handoff.md` fresh before `/compact`, `/clear`, or limit risk |
| Codex | Read `handoff.md`, continue only the next incomplete chunk, then update the file and verification notes |
| Gemini CLI | Best for search/synthesis; return markdown or commands and record what was suggested |
| Cursor/Windsurf/Cline/Copilot | No reliable hooks; manually update `handoff.md` before closing the IDE |
| Antigravity | Subagents must receive only one chunk at a time and return evidence for the handoff |
| Ollama/Hermes/local LLM | Treat as read-only planner unless explicitly given file access; output patch-ready steps and update notes through the primary agent |

## Done Criteria

A cross-agent plan is ready only when:

- Each chunk has an ID, status, files, and verify command.
- `## Resume Here` names exactly one next action.
- Completed chunks include evidence, not just "done".
- Blockers include the missing input or failed command.
- `handoff.md` contains no secrets or raw/private content.
