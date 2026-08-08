# Handoff → next session/agent (a-design ecosystem + skill cleanup)

**From:** ZCode session, A-Wiki repo, 2026-08-04 → 2026-08-08
**Subject:** a-design ecosystem shipped + 2 rounds of skill cleanup
**Action required:** none blocking. Optional extensions documented in §6.
**Read first:** `AGENTS.md` (A-Suite table updated), `wiki/A-ROUTER.md`, this doc.

---

## 1. What shipped this session (9 commits, all in main)

| Commit | What |
|---|---|
| `3f3efc21` | a-design pack (SKILL.md + 2 references) + routing fix 3 dispatchers (a-web/a-plan/lifecycle-router) + drop design-system duplicate |
| `86440b61` | Routing extend 4 more packs (a-content/a-game/a-backend/a-agent) |
| `6fbc3d04` | T1 triggers expand (5→8) + T2 Quality Gate rubric lib (`scripts/lib/a_design_gate.py` ~270 LoC) + 18 tests |
| `af98f49d` | T3 MCP `design_quality_gate` tool + schema + 11 tests |
| `dcb44ce1` | `/A-Design-Help` cheat sheet (`commands/A-Design-Help.md`) |
| `476812d6` | /init AGENTS.md A-Suite refresh (1st pass) |
| `111bc941` | Vision Gate Phase 1: Pillow screenshot extractor (`scripts/lib/a_design_extract.py` ~280 LoC) + 16 tests + 3 PNG fixtures |
| `be5888c9` | Vision Gate T4: MCP `design_quality_gate_screenshot` tool + 10 tests |
| `53c605a2` | Conservative cleanup attempt (a-rabies-report fix-forward made it; cleanup lost to auto-pull) |
| `f9570100` | /init AGENTS.md (registry state note) |
| `feafc19a` | **REDO conservative cleanup -12 (253→241)** — the one that actually stuck |

## 2. Final state (verified 2026-08-08)

| Metric | Before session | After |
|---|---|---|
| Registry skills | 451 | **241** (-210, -47%) |
| a-* packs | 15 | **22** (+7: a-design, a-agent, a-backend, a-game, a-rabies-report from other agent + restored) |
| Tests passing | — | **217** (a_suite_integrity + check_skill_registry + skills_registry) |
| Active claims | — | **0** (all released) |
| Capability loss | — | **0** (every dropped file still on disk; ECC cheatsheets served via documentation-lookup) |

### Registry cleanup history (3 rounds)
1. **Tier A** (451→252): drop 31 subagent-personas (wrong place) + 8 deprecated + 9 a-doc stubs + 168 ECC cheatsheets demoted (files stay)
2. **Conservative** (253→241): drop 5 dead aliases (hipaa, token-budget-advisor, laravel/quarkus/springboot-verification) + 4 dead/stub (continuous-learning, mysql-patterns, autoglm-browser-agent 404, project-guidelines-example) + 3 framework-testing template dups (cpp/csharp/fsharp-testing)
3. **a-design ecosystem added** (+7 packs: a-design, a-agent, a-backend, a-game, platform-ingest from prior session, + word/assessment-generator restored)

## 3. a-design ecosystem — 3-layer architecture

```
Rubric lib (deterministic)           scripts/lib/a_design_gate.py
        ↓                                     ↑
Token-based MCP tool          MCP design_quality_gate(design_tokens)
        ↓                                     ↑
Screenshot MCP tool     MCP design_quality_gate_screenshot(screenshot_path)
                                ↓
                  scripts/lib/a_design_extract.py (Pillow)
```

- **Rubric**: 8 categories, 100 pts, threshold 80 to ship. Categories: Hierarchy(15) · Typography(15) · Color(15) · Composition(15) · Motion(10) · Accessibility(15) · Distinctiveness(10) · Craft(5)
- **Composition layer** (inspired by StyleSeed MIT): 8 output grammars × 9 brand recipes × 5 adapters × profiles
- **Distinctiveness** anti-AI-tell: icon-chip cliché, all-even grid, ghost 01/02/03, AI-purple Lila Rule, pure #000 detection
- **Borrowed patterns (credited in docstrings)**: StyleSeed (composition+gate+authority order) · ui-ux-pro-max (data) · taste-skill (anti-slop)

## 4. What's deferred (NOT blocking, with reasons)

| Item | Why deferred |
|---|---|
| Framework matrix collapse (-40+ possible) |django/laravel/quarkus/springboot × {patterns,tdd,security,verification} = 30+ skills. Risk: breaks imports without redirect layer. Needs design. |
| Playwright DOM extraction (Phase 2 vision gate) | Would let pixel analysis reach typography scale / ARIA / touch targets. Needs Playwright install (heavy dep, not in requirements.txt today). |
| a-router ← awiki-lifecycle-router merge | Touches SessionStart hook config — risk of breaking session boot. |
| 3-pipeline merge (finance/medical/research) | Working subagent chains in active use — risk of breaking flows. |
| Registry regen for ~200 skills on disk but unregistered | scan.py skips `_upstream/`; debt flagged in AGENTS.md. Regenerating would surface them as canonical — but many are duplicates of registered ones. |
| YAML folded-scalar parser bug in scan.py | 8 skills have description showing `>-` or `>` in registry (blueprint, claude-api, hook-suggest, pharmacy-order-lookup, prompt-optimizer, frontend-a11y). Real description exists in SKILL.md but scan.py regex doesn't handle multi-line folded values. Fix: use real YAML parser. |
| word-generator + assessment-generator frontmatter fix | Both lack YAML frontmatter entirely (audit flagged as stubs but bodies are real Thai gov/excel generators). Add frontmatter to keep them clean. |
| Hermes linking for a-design | a-design symlink exists in 5/7 agents (zcode/claude/codex/cline/gemini). Hermes uses manifest not symlinks — run linker if needed. |

## 5. Hard lessons (Iron Law #2 root-causes worth remembering)

1. **Auto-pull SessionStart hook silently rebases away local commits** — `git pull --rebase` with remote ahead of local cherry-picks remote-only, leaving local commits dangling. Fix: `git cherry-pick <SHA>` to recover. Mitigation: commit each chunk immediately.
2. **Auto-pull can swallow STAGED changes** — even after `git add`, auto-pull between `add` and `commit` can reset the working tree so the staged content is gone. Lesson (commit `feafc19a`): capture+stage+commit in a single script run, no pauses.
3. **Bash heredoc escapes break Python backslashes** — Windows path separators in Python scripts via `python << 'EOF'` get mangled. Workaround: write to `.tmp/script.py` then `python .tmp/script.py`.
4. **feedparser was mis-classified as a hard dependency** — TDD revealed stdlib xml.etree handles Reddit Atom feeds fine; gating on feedparser being installed was wrong design.
5. **Demote-before-create ordering trap** — demoting ECC skills as "no real dep" was correct at the time, but creating packs that reference those skills turned them back into real deps. Order matters: create packs first, then demote.
6. **AI-purple detection must scan ALL palette roles** — extractor classified header-band #6366F1 as `fg` not `accent` because it's the darkest color in the header. Fix: scan every palette value, not just accent role.
7. **Pure-black detection needs full resolution** — downsampling 200x150 → 400x300 destroys 1-3px text pixels (anti-aliasing averages them into bg). Scan at full resolution (capped 800x600) with near-black tolerance ≤8 to catch anti-aliased #000 text edges without matching refined #2A2A2A=42.
8. **Trigger collision catch** — a-backend 'database schema' clashed with a-plan → changed to 'orm pattern'. Always run test_a_suite_integrity after adding triggers.
9. **Policy conflict: deprecated = drop vs flag** — Tier A policy "drop deprecated from registry" conflicts with old hook test "deprecated should warn". Fix: replace test with positive policy assertion (`test_registry_has_no_deprecated_entries`).

## 6. Resume entry points (if continuing)

- **Start here**: this doc + `AGENTS.md` A-Suite table + `wiki/A-ROUTER.md`
- **To extend vision gate**: implement Playwright DOM extractor (Phase 2) — wire `scripts/lib/a_design_extract_dom.py` that complements the Pillow pixel extractor
- **To do framework collapse**: design redirect layer first, then parameterize patterns/tdd/security/verification per framework
- **To fix YAML parser bug**: swap `parse_frontmatter` regex in `scripts/skills_registry/scan.py` for `yaml.safe_load`
- **State files**: `.tmp/task-board.json`, `.tmp/memory-ledger.jsonl`, `.tmp/agent-claims.json` (all gitignored, survive compact)

## 7. If you disagree with anything

Don't silently revert. Post to blackboard:
```
bb_post(frm="next-agent", to="zcode", type="proposal",
        body="disagree with <X> because <reason>")
bb_read(to_filter="next-agent")
```
That's what the channel is for.
