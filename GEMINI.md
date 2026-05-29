# A-Wiki — Gemini CLI Agent Config

> **FIRST ACTION: Read `AGENTS.md`** — full A-Wiki brain (Iron Laws, Cost Pyramid, Swarm, Wiki rules)
>
> This file adds Gemini-specific context on top of the universal brain in `AGENTS.md`.

---

## First Action Every Session

1. Read `AGENTS.md` — Universal A-Wiki brain (Iron Laws, Cost Pyramid, Directory, Scripts)
2. Read `wiki/context/wiki-overview.md` — wiki stats + synthesis + pointers
3. Read `wiki/context/session-memory.md` — cross-session decisions + TODOs
4. Run `python scripts/agent-preflight.py` — portable safety check when Gemini hooks are unavailable
5. *(optional)* Check `wiki/context/model-roster.conf` — current free model availability

---

## Model Selection (Dynamic — never hard-code!)

Model availability changes daily — free models become paid, new ones appear, old ones get deprecated.

```bash
cat wiki/context/model-roster.conf        # see current free model roster
bash scripts/update-model-roster.sh       # refresh roster from OpenRouter API
bash scripts/swarm/delegate.sh "query"    # delegate to best available free model
```

> **Iron Law from model-scouter.md**: "Never hardcode model names. Always scout dynamically."
> See `agent-skills/swarm-intelligence/model-scouter.md` for full scouting protocol.

---

## Gemini CLI Config

- Config dir: `.gemini/`
- Settings: `.gemini/settings.json` (model config, temperature, hooks runner)
- Hooks: `scripts/hooks_runner.py` (Python — same hooks as all platforms)

---

## Key Rules (full version in AGENTS.md)

**Iron Laws (UNBREACHABLE):**

1. NO production code without a failing test first
2. NO bug fixing without root cause investigation first
3. If parallel model violates #1 or #2 → DISCARD and REWRITE
4. `raw/` is immutable — never edit or delete
5. Config files must not be edited without explicit permission

**Wiki conventions:**

- `wiki/` filenames: kebab-case English only
- Confidence markers required: `[training]` / `[verified YYYY-MM-DD]` / `[wiki]`
- Update `log.md` and `wiki/context/` after every significant edit

**Commit rules:**

- Commit directly to `main` — NO branch, NO PR, NO worktree
- Format: `type(scope): description`

---

## Cost Pyramid (start at Level -1)

| Level | Channel | Use for |
|-------|---------|---------|
| **-1** | Local FTS5 | `python scripts/wiki/search-wiki.py "query"` |
| **1** | Free API (dynamic roster) | `bash scripts/swarm/delegate.sh "query"` |
| **4** | Current AI | Complex reasoning only |

---

## Do NOT Delegate (Primary Agent ONLY)

- Deep reasoning / decision making
- Writing new wiki pages
- Editing AGENTS.md or GEMINI.md
- Senior Critic validation

---

*A-Wiki Gemini CLI Edition — 2026-05-25*
