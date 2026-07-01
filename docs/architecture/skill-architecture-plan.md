# A-Wiki Universal Skill Architecture — Design Plan

> **Status:** ✅ Chunk 1 DONE · ⬜ Chunks 2-5 pending
> **Last update:** 2026-07-01 (ZCode session)
> **Resume marker:** `chunk(registry)` DONE · next: `chunk(dedup)`
> **To resume:** read this file + `handoff.md` (private) → continue from Chunk 2.

This is the durable design doc (Layer 1 knowledge). The live progress tracker
is `handoff.md` (private, gitignored). Both must stay in sync at chunk boundaries.

---

## 1. Root Cause Analysis (from 3-agent deep audit)

| # | Root cause | Impact | Goal |
|---|-----------|--------|------|
| R1 | **No contract layer** — skill content (SKILL.md) and agent discovery (kilo.jsonc, gemini skills, ~/.claude symlinks) linked by symlink scripts that drift freely | agents see different skills; adding an agent needs manual multi-file edits | G1, G4 |
| R2 | **Two discovery paradigms mixed** — explicit manifest (Kilo/Gemini/Hermes) vs recursive auto-discover (Claude/ZCode/Codex) with no sync layer | skill missing from one agent but present in another silently | G1 |
| R3 | **Frontmatter has no metadata fields** — no `aliases`/`category`/`domain`/`lifecycle_phase`; deprecation is scattered prose | dedup can't be structural; aliases don't resolve | G5 |
| R4 | **`.zcode/`, `.hermes/`, `.kilo/`, `.agents/` not ignored** — and `log.md`/`handoff.md`/`.gemini/settings.json` tracked before rules existed, defeating the rules | private state leaks into public repo | G3 |
| R5 | **No `.~[agentName]` per-agent private convention** — drive/ only has private-tools/ (shared) | multiple agents overwrite each other; not portable | G2 |
| R6 | **Secret detection regex-only, CI-only** — no pre-commit gate for registry/skill drift | leaks caught late; drift accumulates | G3, G4 |

---

## 2. Design — 5-Layer Contract Architecture

```
LAYER 0 (existing): SKILL.md files — skills/ · agent-skills/ · ~/.claude/ · ~/.kilo/ · ~/.codex/
                     ↓ scan + parse frontmatter
LAYER 1 (Chunk 1):  skills-registry.json  ← SINGLE SOURCE OF TRUTH
                     ↓ 1 command: regen-skill-surfaces.py
LAYER 2 (Chunk 1):  Generators → per-agent surfaces (.kilo, .gemini, hermes, AGENTS.md)
                     ↓ agents load natively
LAYER 3 (existing): Agents (Codex·Claude·ZCode·Hermes·Kilo·Cline·Windsurf·OpenClaw·future)
                     ↓ gate every change
LAYER 4 (Chunk 3):  Enforcement (PreToolUse hook + pre-commit + CI)
```

**Principle:** Edit registry → run `python scripts/regen-skill-surfaces.py` → commit.
Agents never edit generated surfaces by hand. **Adding a NEW agent = add one
generator module + one line in the `GENERATORS` dict.** Nothing else changes.

---

## 3. Execution — 5 Phased Chunks (commit + push each)

Each chunk passes the Brain Improvement Gate, has a failing test first (Iron
Law #1), commits to main with `chunk(<ID>): <goal> [next: <ID>]` (cross-agent
handoff rule #8), and pushes at the boundary.

### Chunk 1 (registry): ✅ DONE — `skills-registry.json` + generators + bootstrap scan

- `skills-registry.json` — 331 skills, schema-validated, privacy-clean
- `scripts/skills_registry/__init__.py` — schema (SCHEMA_VERSION=1), Registry, validate_registry
- `scripts/skills_registry/scan.py` — bootstrap scanner (6 surfaces), frontmatter parser, heuristics
- `scripts/skills_registry/drift.py` — drift detection
- `scripts/skills_registry/generators/` — gen_kilo, gen_gemini, gen_agents_md (idempotent)
- `scripts/regen-skill-surfaces.py` — orchestrator (`--bootstrap` `--validate` `--check` default=regen)
- `tests/test_skills_registry.py` — 34 tests green
- Domain taxonomy: `code | debug | design | ux-ui | trader | medical | business | data | engineering | security | ai-ops | productivity | wiki | iot | env | pharmacy | thai | logistics | network | media | document | sre`

### Chunk 2 (dedup): ⬜ PENDING — collapse true dups + alias near-dups (Moderate)

**Action matrix (from deep audit):**
- DELETE true dups: `skill-creator` ×3 → keep `skills/anthropic-skills/skill-creator`
- ALIAS claude-code mirrors ×11 (crew-dispatch, ingest-source, lint-wiki, etc.)
- THIN STUB re-route: `hipaa-compliance` → `healthcare-phi-compliance`; `token-budget-advisor` → `context-budget`; `root-cause-first` → `debug-mantra`
- NEAR-DUP alias (keep content): `*-verification` ×4; browser/e2e testing ×4; `ito-*` ×4; `gateguard`/`safety-guard`
- KEEP distinct: 8 language-testing, 12 Thai, 6 trading-security micro-skills
- New files: `scripts/skills_registry/dedup.py`, `docs/protocols/skill-consolidation.md`

### Chunk 3 (enforce): ⬜ PENDING — `check_skill_registry.py` hook + schema gate

- `scripts/hooks/check_skill_registry.py` — PreToolUse gate (pattern = check_harness_routing.py)
- `scripts/hooks/pre_commit_skill_surfaces.sh` — pre-commit regen
- `.github/workflows/scripts/registry-consistency.yml` — CI `regen --check`
- `docs/protocols/skill-frontmatter-schema.md`
- Wire into `.claude/settings.json`, `.codex/hooks.json`, agent-preflight.py
- **AGENTS.md Iron Law #9** ⚠️ needs explicit user approval (Iron Law #5)

### Chunk 4 (harden): ⬜ PENDING — gitignore leaks + drive/.agents/ convention

- `.gitignore`: add `.zcode/` `.hermes/` `.kilo/plans/` `.kilo/worktrees/` `.agents/`
- `git rm --cached`: `log.md`, `handoff.md`, `.gemini/settings.json` (surface to user first)
- `drive/.agents/{zcode,claude,codex,hermes,kilo}/` convention
- `scripts/drive_path.py` — add `resolve_agent_dir()`
- `scripts/setup-local.sh` — add step [9/9]

### Chunk 5 (verify): ⬜ PENDING — cross-agent smoke test + docs

- `scripts/verify-skill-surfaces.py` — per-agent coverage matrix
- `tests/test_cross_agent_visibility.py`
- `wiki/entities/ai-tools/a-wiki-skill-architecture.md` — durable knowledge page
- Docs updates (AGENTS.md, CLAUDE.md, GEMINI.md — need user approval)

---

## 4. Verification (Definition of Done)

- [x] `skills-registry.json` exists, schema-validated, covers all 6 surfaces
- [x] `python scripts/regen-skill-surfaces.py --check` exits 0 (no drift)
- [x] `pytest tests/test_skills_registry.py` green (34 tests)
- [ ] Skill count on each agent surface equal (cross-agent visibility matrix) — Chunk 5
- [ ] `git check-ignore .zcode/ .hermes/ .kilo/plans/ .agents/` all match — Chunk 4
- [ ] `check-privacy.py` clean, `agent-preflight.py` passes — ongoing
- [ ] Docs updated (AGENTS.md/CLAUDE.md with user approval) — Chunk 5

---

*Architecture v1.0 — 2026-07-01 · Resumable via `git pull` + this file + handoff.md*
