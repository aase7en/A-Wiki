# A-Wiki Brain Prompt Fragment

## Session Start Protocol
Every session MUST begin with these steps:
1. Run `/awiki-session-start` (emits dashboard event, ensures server)
2. Read `AGENTS.md` — master universal brain config
3. Read `wiki/context/wiki-overview.md` — wiki structure + stats + synthesis
4. Read `wiki/context/session-memory.md` — cross-session decisions + TODOs
5. Read this file (`agent-skills/awiki-brain-prompt.md`) — brain fragment

## Iron Laws (UNBREACHABLE)
1. NO production code without a failing test first
2. NO bug fixing without root cause investigation first (debug-mantra 4-step)
3. If parallel model violates #1 or #2 → DISCARD and REWRITE
4. `raw/` is immutable — never edit or delete
5. Config files (AGENTS.md, CLAUDE.md) must not be edited without explicit permission
6. External-editor source-of-truth protection (USERSCRIPT_SYNC_OK check)
7. Source provenance — save to `raw/<slug>.<ext>` BEFORE creating `wiki/sources/`
8. Bot trading client is MOCK/visualization-only — no secrets, signed requests, or order execution
9. Drive decision rule: personal/secret/machine-specific → `drive/` (gitignored); reusable knowledge → repo

## Cost-First Decision Pyramid
Start at the lowest level. Move up only when lower cannot do the job:
- **Level -1**: Local FTS5 / knowledge-graph (free + offline)
- **Level 0**: Hook (SessionStart / PreToolUse) + Context Compaction (free)
- **Level 1**: `free-current` dynamic roster (free)
- **Level 2**: `cheap-capable` runtime route (very cheap)
- **Level 3**: `platform-low-scout` / low-cost CLI agent (cheap)
- **Level 4**: `platform-primary` current model (normal — only after scout says lower tiers insufficient)

## Swarm Intelligence Protocol
SCOUT → ALLOCATE → VALIDATE
- **Architect**: OpenRouter free reasoning — planning, root cause, design
- **Executioner**: Free flash/coder — code writing, tests, refactoring
- **Senior Critic**: Primary agent (YOU) — validate ALL outputs (NOT delegatable)

## Core Rules
- wiki/ managed by AI agents — kebab-case English filenames
- Confidence markers required: `[training]` / `[verified YYYY-MM-DD]` / `[wiki]` / `[notebooklm YYYY-MM-DD]`
- Plan before implementing (if >3 files affected: specify "will edit [files] — doing X in each")
- Commit directly to main only — NO branch, NO PR, NO worktree
- 3-layer output: (1) durable knowledge = Markdown, (2) machine data = compact (CSV/TSV > JSONL > JSON, never HTML), (3) human review = JSON → render-html → gitignored leaf in `exports/html/`
- Prompts sent outside: use English (saves ~30% tokens)
- Cross-agent handoff: chunk plans into resumable units, checkpoint in local `handoff.md`, push at boundaries

## Brain Improvement Gate
Before changing A-Wiki brain capabilities, agent instructions, skills, hooks, scripts, or sync:
- Clear gain: makes A-Wiki smarter/safer/searchable/reusable
- Lightweight: prefer hook/skill/plugin/script/symlink over heavy always-loaded context
- Cost-first: local/search/free routes before expensive work
- Cross-platform: no hardcoded personal paths
- Public-safe: secrets/raw/private stay in gitignored `drive/`
- Package when reusable: make it an installable unit, not a one-off reminder
