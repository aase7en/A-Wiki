# A-Wiki — GitHub Copilot Instructions

> Full brain specification: see **`AGENTS.md`** in the repo root.
> This file provides a quick summary — AGENTS.md has the complete context.
> Start-of-session safety check: run `python scripts/agent-preflight.py`.

---

## About This Project

**A-Wiki** = Hybrid swarm intelligence + knowledge wiki brain.
Core directories: `wiki/` (knowledge) · `raw/` (immutable sources) · `agent-skills/` (swarm protocol) · `scripts/` (automation)

---

## Iron Laws (UNBREACHABLE)

1. NO production code without a failing test first
2. NO bug fixing without root cause investigation first
3. If a parallel model violates #1 or #2 → DISCARD and REWRITE
4. `raw/` is immutable — never edit or delete
5. Config files must not be edited without explicit permission

---

## Wiki Conventions

- Filenames: kebab-case English (e.g. `mqtt-broker.md`)
- Confidence markers required: `[training]` / `[verified YYYY-MM-DD]` / `[wiki]`
- Update `log.md` and `wiki/context/` after every significant change
- Plan before implementing if change affects >3 files

---

## Model Selection — Dynamic Only

Never hard-code model names. Check current free models:

```bash
cat wiki/context/model-roster.conf
bash scripts/update-model-roster.sh
bash scripts/swarm/delegate.sh "query"
```

---

## Cost Pyramid

Start at Level -1, move up only when necessary:

- **-1**: `python scripts/wiki/search-wiki.py "query"` (free, offline)
- **1**: `bash scripts/swarm/delegate.sh "query"` (free API)
- **4**: Current AI — complex reasoning only

---

## Commit Rules

- Commit directly to `main` — NO branch, NO PR, NO worktree
- Format: `type(scope): description`
- Example: `wiki(ai-tools): add Gemini CLI entity`

---

*A-Wiki GitHub Copilot Edition — 2026-05-25*
