---
description: Emit session start event to Live Dashboard, ensure server is running, and load A-Wiki brain context
---

## Session Start Protocol
Call this at the beginning of EVERY A-Wiki session. It ensures the Live Dashboard
server is running on port 7790, emits a `session_start` event, and loads the
required A-Wiki brain context files.

## Dashboard Setup
`bash scripts/live-dashboard/awiki-live-init.sh kilo`

## Brain Context Loading
After dashboard setup, read these files to establish A-Wiki brain awareness:

1. `AGENTS.md` — Universal brain config: Iron Laws, Cost-First Pyramid, Swarm Protocol, Core Rules
2. `wiki/context/wiki-overview.md` — Wiki structure, stats, synthesis pointers
3. `wiki/context/session-memory.md` — Cross-session decisions, TODOs, unresolved items
4. `agent-skills/awiki-brain-prompt.md` — A-Wiki Brain fragment (Iron Laws summary, Cost-First levels, Swarm flow)

If `session-memory.md` is missing, use `wiki/context/session-memory.md.example` as fallback.
Always follow the Iron Laws and Cost-First Decision Pyramid defined in AGENTS.md.
