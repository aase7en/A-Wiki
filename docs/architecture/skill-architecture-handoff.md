# Cross-Agent Handoff — Universal Skill Architecture

> **Resume marker:** `chunk(registry)` DONE (pending commit) · next: `chunk(dedup)`
> **Last session:** 2026-07-01 (ZCode, builtin:zai-coding-plan/GLM-5.2)
> **Full design doc:** `docs/architecture/skill-architecture-plan.md` (READ FIRST)
> **To resume:** `git pull origin main` → read this file → read the plan → continue from Chunk 2.

This is the public-safe, git-tracked handoff doc. The private `handoff.md`
symlink (→ drive/personal/journal/) is for session-local scratch only and is
gitignored (Chunk 4 will formalize this). Keep THIS file in sync at chunk boundaries.

---

## 📊 Progress Tracker

| Chunk | ID | Status | Tests | Key files |
|-------|----|--------|-------|-----------|
| **1 — registry** | `chunk(registry)` | ✅ DONE | 34/34 | `skills-registry.json`, `scripts/skills_registry/`, `scripts/regen-skill-surfaces.py`, `tests/test_skills_registry.py` |
| **2 — dedup** | `chunk(dedup)` | ⬜ NEXT | — | alias/deprecate ~30 skills + `dedup.py` + `docs/protocols/skill-consolidation.md` |
| **3 — enforce** | `chunk(enforce)` | ⬜ | — | `scripts/hooks/check_skill_registry.py` + pre-commit + CI + Iron Law #9 (needs approval) |
| **4 — harden** | `chunk(harden)` | ⬜ | — | `.gitignore` + `drive/.agents/` + `drive_path.py` |
| **5 — verify** | `chunk(verify)` | ⬜ | — | `scripts/verify-skill-surfaces.py` + `test_cross_agent_visibility.py` + docs |

---

## ✅ Chunk 1 — DONE

**Built:** 5-layer contract foundation — registry (single source of truth) + generators + drift detection + 34 green tests. See plan §Chunk 1.

**Verify state:**
```bash
python -m pytest tests/test_skills_registry.py -q        # 34 passed
python scripts/regen-skill-surfaces.py --validate        # ✅ valid
python scripts/regen-skill-surfaces.py --check           # ✅ no drift
grep -rc "aase7en\|C:.Users" skills-registry.json scripts/skills_registry/generated/ | grep -v ':0' || echo CLEAN
```

**Facts:** 331 skills (302 repo, 25 external-installed, 4 external-system). "code" domain = 178. All external paths use `~/...` portable form.

---

## ⬜ Chunk 2 — dedup (NEXT) — Moderate level

**Goal:** Reduce skill surface ~30% by collapsing true duplicates and aliasing near-duplicates. Keep all distinct skills. See plan §Chunk 2 for full action matrix.

**Order:**
1. `grep` all references before deleting anything
2. DELETE `skill-creator` ×3 → keep `skills/anthropic-skills/skill-creator` only
3. ALIAS 11 claude-code mirrors (don't delete yet — verify no runtime break first)
4. Formalize thin-stub frontmatter (hipaa→phi, token-budget→context-budget, root-cause→debug-mantra)
5. NEAR-DUP alias (keep content): verification ×4, browser/e2e ×4, ito-* ×4, guards ×2
6. New files: `scripts/skills_registry/dedup.py`, `docs/protocols/skill-consolidation.md`
7. Extend `test_skills_registry.py` — no orphan aliases, every alias → existing canonical, no cycles

**Commit:** `chunk(dedup): collapse true dups + alias near-dups [next: enforce]`

---

## ⬜ Chunk 3 — enforce

**Pattern:** copy `scripts/hooks/check_harness_routing.py` skeleton (stdin JSON, `_emit`, grandfather, HOOK_SKIP, exit 2).

- `scripts/hooks/check_skill_registry.py` — block Write of unregistered SKILL.md; block deprecated invoke; warn on missing domain/lifecycle
- `scripts/hooks/pre_commit_skill_surfaces.sh` — regen on SKILL.md change, block if drift
- CI: `regen --check` on push
- `docs/protocols/skill-frontmatter-schema.md`
- Wire into `.claude/settings.json`, `.codex/hooks.json`, agent-preflight.py
- **Iron Law #9** — propose wording, get user approval, THEN edit AGENTS.md

**Commit:** `chunk(enforce): check_skill_registry hook + frontmatter schema [next: harden]`

---

## ⬜ Chunk 4 — harden

- `.gitignore`: `.zcode/` `.hermes/` `.kilo/plans/` `.kilo/worktrees/` `.agents/`
- `git rm --cached` log.md, handoff.md, .gemini/settings.json (**surface to user first**)
- `drive/.agents/{zcode,claude,codex,hermes,kilo}/` + README + .example
- `scripts/drive_path.py` — `resolve_agent_dir(agent)`
- `scripts/setup-local.sh` — step [9/9]
- Verify: `security-and-hardening` + `check-privacy.py` + `security-scan` skills

**Commit:** `chunk(harden): gitignore leaks + drive/.agents/ convention [next: verify]`

---

## ⬜ Chunk 5 — verify

- `scripts/verify-skill-surfaces.py` — per-agent coverage matrix
- `tests/test_cross_agent_visibility.py`
- `wiki/entities/ai-tools/a-wiki-skill-architecture.md`
- Docs (need user approval): AGENTS.md §Universal Skill Registry, CLAUDE.md, GEMINI.md, skills/README.md, awiki-lifecycle-router

**Commit:** `chunk(verify): cross-agent smoke test + docs [architecture complete]`

---

## 🔑 Iron Laws & Constraints (must follow when resuming)

1. NO code without failing test first (Iron Law #1)
2. NO bug fix without root cause (Iron Law #2)
3. AGENTS.md / CLAUDE.md edits need explicit user approval (Iron Law #5)
4. raw/ is immutable (Iron Law #4)
5. No personal paths in public repo — use `~/...` portable form or `drive/`
6. Commit directly to main — no branches/PRs (Core Rule #6)
7. Commit format: `chunk(<ID>): <goal> [next: <ID>]` + push at each boundary
8. `regen-skill-surfaces.py --check` must be green before any commit touching skills

---

## 📂 Key File Map

| File | Purpose | Edit when |
|------|---------|-----------|
| `skills-registry.json` | Single source of truth | Adding/changing/aliasing a skill |
| `scripts/skills_registry/__init__.py` | Schema + Registry + validate | Changing taxonomy or schema |
| `scripts/skills_registry/scan.py` | Scanner + heuristics | Refining classification |
| `scripts/skills_registry/generators/*.py` | Per-agent surfaces | Adding a NEW agent surface |
| `scripts/regen-skill-surfaces.py` | Orchestrator | Never edit generated surfaces — regen |
| `scripts/skills_registry/generated/` | Generated surfaces (DO NOT hand-edit) | Never — always regen |
| `tests/test_skills_registry.py` | Contract tests | Before changing registry behavior |
| `docs/architecture/skill-architecture-plan.md` | Full design doc | Read first when resuming |

---

*Generated 2026-07-01 · Resumable via git pull + this file + the plan doc*
