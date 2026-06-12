# Cross-Agent Plan Handoff Protocol

> Purpose: make A-Wiki work resumable across Claude Code, Codex, Gemini CLI, Cursor, Windsurf, Cline, Copilot, Antigravity, Ollama/Hermes-style local agents, and any future IDE agent when a chat hits context or rate limits.

## Core Rule

When an agent opens Plan Mode, prepares an implementation plan, or is about to switch tools/agents, it must split the work into small checkpointable chunks and write the current state to `handoff.md`.

`handoff.md` is local and gitignored because it can contain live work context. The tracked source of truth for its shape is `handoff.md.example`.

## Drive-Sync Rule (Machine Portability)

**`handoff.md`, `goals.md`, and `wiki/context/session-memory.md` MUST be drive-synced symlinks** — not regular files. This ensures plans, goals, and TODOs survive machine switches (Mac ↔ Work PC ↔ WSL) without git commits.

| File | Drive target | Purpose |
|------|-------------|---------|
| `handoff.md` | `drive/personal/journal/handoff.md` | Active plan chunks (Plan Mode / task board) |
| `goals.md` | `drive/personal/journal/goals.md` | Longer-term goals that persist across sessions |
| `wiki/context/session-memory.md` | `drive/personal/journal/wiki-context-session-memory.md` | Cross-session TODOs + decisions |

**To set up symlinks on a fresh machine:**
```bash
bash scripts/setup-local.sh          # auto-links on first setup
# or, to fix existing regular files:
FORCE_SYMLINK=1 bash scripts/setup-local.sh
```

The `SessionStart` hook (`check_drive_link.py`) warns at each session start if any of these files are regular files instead of symlinks.

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

After updating the file, run the lightweight checker:

```bash
python3 scripts/check-handoff.py --path handoff.md
```

Use strict mode before relying on a handoff for a long-running or multi-device
switch:

```bash
python3 scripts/check-handoff.py --path handoff.md --strict
```

If `handoff.md` is missing, run:

```bash
cp handoff.md.example handoff.md
```

or run:

```bash
bash scripts/swarm/agent-switch.sh
```

The script bootstraps `handoff.md` from the example if needed.

## Per-Sub-Step Commit Checkpoint

When building any system, plan and design first, split into small chunks, and
**commit each completed sub-step to `main`** so the work is durable and another
agent (VS Code + Cline, Antigravity, Manus, Codex, Gemini CLI, Cursor) can
resume after a rate limit, pause, or tool switch.

Because `handoff.md` and `session-memory.md` are gitignored, the **commit log on
`origin/main` is the tracked, public-safe breadcrumb**. The next agent runs
`git log --oneline` to see exactly where to resume.

### Commit message convention

```text
chunk(<ID>): <one concrete result> [next: <ID>]
```

- `<ID>` is the stable chunk ID from the Task Board (`P1.2`, `DOC-1`, `BUG-3`).
- `[next: <ID>]` names the single next chunk, or `[next: done]` when the plan is
  complete. This is what a resuming agent reads first.
- Keep the message public-safe: chunk ID + goal only — no secrets, tokens,
  cookies, raw/private content, or machine paths (enforced by the secret-leak
  and privacy hooks).
- Use `step(<ID>): ...` as an accepted alias.

### Commit vs push cadence

| Action | When |
|---|---|
| `git commit -m "chunk(<ID>): ..."` | After **every** completed sub-step (local, cheap, no token cost) |
| `git push origin main` | At a handoff boundary: **pause, near rate limit, or switching Agent/IDE/device** |

Commit often so nothing is lost; push at handoff boundaries so a resuming agent
can pull the latest. A normal session still closes with the full
**SESSION END PROTOCOL** (`session(YYYY-MM-DD): ...` commit + `log.md` +
`session-memory.md`).

### Hook interaction

The Delegation Gate (`scripts/hooks/check_delegation_gate.py`) allows `git push`
when the commit message matches `session(...)`, `chunk(...)`, or `step(...)`. A
`chunk(...)` push does **not** require a full session-end update — that is the
point of a mid-work handoff. Still run a final `session(...)` commit at true
session end so cross-session memory stays intact.

## Resume Order For The Next Agent

1. Read platform rules: `AGENTS.md` plus the current tool file (`CLAUDE.md`, `GEMINI.md`, `.clinerules`, etc.).
2. Read `handoff.md` if present locally; otherwise run `git log --oneline -10` and read the latest `chunk(<ID>): ... [next: <ID>]` — that `[next: <ID>]` is where you resume.
3. Run `python3 scripts/check-handoff.py --path handoff.md` and treat warnings as context to repair before doing expensive work.
4. Read `## Cost Tier Snapshot` and pick the lowest sufficient tier: L1 local/search, L2 cheap summary/table, L3 low-cost scan/scout, L4 primary model only for implementation or architecture that needs it.
5. Read only the referenced canonical file, such as a project roadmap, `wiki/context/session-memory.md`, or a specific protocol.
6. Continue from `## Resume Here`; do not restart old completed chunks.
7. After finishing a chunk, update `handoff.md` before doing unrelated work.

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
- `## Failed Approaches` records what not to retry, or explicitly says `None`.
- `## Key Decisions` records locked decisions and rationale, or explicitly says `None`.
- `## Open Decisions` lists unresolved decisions before the next agent implements.
- `## Cost Tier Snapshot` tells the next agent the cheapest first command and current routing state.
- `python3 scripts/check-handoff.py --path handoff.md --strict` passes before high-risk handoff.
- `handoff.md` contains no secrets or raw/private content.
