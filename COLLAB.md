# COLLAB โ€” Multi-agent coordination (เธกเธฒเธ•เธฃเธเธฒเธ A-Wiki cross-agent-work-orders)

> Agent เธ—เธธเธเธ•เธฑเธง (Claude/Codex/Cursor/Antigravity/ZCode/Hermes/Kilo/...) เธญเนเธฒเธเนเธเธฅเนเธเธตเน
> เธเนเธญเธเน€เธฃเธดเนเธกเธเธฒเธเนเธ repo เธเธตเน ยท Protocol เน€เธ•เนเธก: A-Wiki `docs/protocols/cross-agent-work-orders.md`

## Lanes (เธเธฃเธฑเธเธ•เธฒเธก repo โ€” เธ•เธฑเธงเธญเธขเนเธฒเธ 2 เน€เธฅเธ เน€เธเธดเนเธกเนเธ”เนเธ•เธฒเธกเธเธณเธเธงเธ agent)

| Lane | เธเธตเธกเธเธฒเธ | เนเธเธฅเนเธ—เธตเนเน€เธเนเธเน€เธเนเธฒเธเธญเธ | เธซเนเธฒเธกเนเธ•เธฐ |
|---|---|---|---|
| migration | A-Wiki vNext migration (phases, work orders, review flow) | `docs/migration/**`, `refactor/*` branches | เนเธเธฅเนเธเธญเธเน€เธฅเธเธญเธทเนเธ |
| hook-engine | hooks/registry/runner/provider adapters | `scripts/hooks/**`, `scripts/hooks_runner.py`, `scripts/cline-hooks/**`, `.claude/settings.json`, `.codex/hooks.json`, `.gemini/settings.json` | เนเธเธฅเนเธเธญเธเน€เธฅเธเธญเธทเนเธ |
| governance | protocols/claims/COLLAB/continuity | `COLLAB.md`, `docs/protocols/**`, `AGENTS.md` (เนเธเนเธ•เนเธญเน€เธกเธทเนเธญเธกเธตเธชเธดเธ—เธเธดเนเธ•เธฒเธก Iron Law #5) | เนเธเธฅเนเธเธญเธเน€เธฅเธเธญเธทเนเธ |
| wiki-knowledge | wiki pages + generated surfaces | `wiki/**`, `.wiki-graph.json`, `brain-map.canvas` | `scripts/**`, `docs/migration/**` |
| infra-CI | workflows, security/health scanners, baselines | `.github/workflows/**`, `scripts/security/**`, `scripts/health/**` | เนเธเธฅเนเธเธญเธเน€เธฅเธเธญเธทเนเธ |

**Hotspot files (เนเธเนเธ—เธตเธฅเธฐ agent เธ•เธฒเธกเธ—เธตเนเธฃเธฐเธเธธ):** `AGENTS.md` ยท `skills-registry.json` ยท `.claude/settings.json` ยท `.github/workflows/ci-core.yml` ยท `scripts/security/baseline.txt` โ€” เนเธเนเนเธ”เนเน€เธเธเธฒเธฐเธเธนเนเธ–เธทเธญ claim เธ—เธตเนเธฃเธฐเธเธธเนเธเธฅเนเน€เธซเธฅเนเธฒเธเธตเนเนเธ scope

## In-progress claims (Rule 1 โ€” claim เธเนเธญเธเธ—เธณ, เธเธฅเธ”เนเธ commit เธเธญเธ chunk เน€เธญเธ)

| Chunk/WO | Agent | Claimed | Scope (files) | Branch / PR |
|---|---|---|---|---|
| โ… **MERGED 2026-08-26: WO-RFR-20260824 governance PR #26 โ’ main `f0c3a78e`** โ€” reviewer (GLM/ZCode) re-ran all claimed validation on branch HEAD (5/5 handoff tests ยท privacy clean ยท health 0 hard), added Loop-Evidence + cross-ref of Binding Loop Engineer โ” Universal Loop Contract (`fe80c1d0`), fixed pr-loop-gate head.sha checkout bug on main (`c140b0d1`, TDD), all 3 checks green at `a68d8fc5`, user-authorized merge + fetch-verified ยท **next: M1 baseline evidence โ’ Group A R-FR-002** | ChatGPT Sol (plan author) + GLM/ZCode (review/merge) | 2026-08-24 | `AGENTS.md`, `docs/migration/awiki-vnext-plan.md`, `docs/work-orders/WO-RFR-20260824.md`, `docs/protocols/cross-agent-plan-handoff.md`, `COLLAB.md` | main `f0c3a78e` |
| โ… **MERGED 2026-08-21 night-2: local rabies/domain stack (26 commits) integrated into vNext main** โ€” canonical 3260/0 green, Core CI SUCCESS at `7b1b808e`; secrets prevented from entering git (.codex/config.toml untracked + tracked secret-free template); เธฃเธ. real name scrubbed โ’ <HOSPITAL> | GLM/ZCode | 2026-08-21 | merge + repair | main `7b1b808e` |
| โ… **Fast-graph brain plan 3 slices MERGED 2026-08-21** (user-approved): S1 PR#23 bridge `search/related/hubs` (hybrid FTS+vec) + recallโ’BM25 ยท S2 PR#24 skill tier-2 description-fallback (226 triggerless skills เธซเธฒเนเธ”เนเนเธฅเนเธงเนเธ”เธขเนเธกเนเธญเนเธฒเธ index 81KB) + SKILL-INDEX search-first mandate ยท S3 symlink farm pruned เนเธ”เธข post-merge relink (323โ’94, 0 broken, surfaces no-drift) | GLM/ZCode | 2026-08-21 | done | main `992fa059` |
| โธ๏ธ **HOLD เน€เธเธช 8โ€“11 (user decision 2026-08-21):** เธซเธขเธธเธ”เธเธฒเธ migration เธเธฑเนเธเธชเธกเธญเธ เธฃเธญ A-Conductor (repo เนเธขเธ) เธชเธฃเนเธฒเธเน€เธชเธฃเนเธเธเนเธญเธ โ€” เธเธฑเนเธเธเธฑเนเธเธเธณเธฅเธฑเธเธ—เธณเธเธฒเธเน€เธเธดเนเธกเธเธฒเธเนเธเธเน€เธ”เธดเธก เธเธฅเธฑเธงเธเธเธเธฑเธ ยท agent เธ•เธฑเธงเธ–เธฑเธ”เนเธ **เธซเนเธฒเธกเน€เธฃเธดเนเธกเน€เธเธช 8+ เนเธ”เธขเนเธกเนเธกเธตเธเธณเธชเธฑเนเธเนเธซเธกเนเธเธฒเธ user** ยท เธเธฒเธเธ—เธตเนเธขเธฑเธเธ—เธณเนเธ”เน: bug fix/gates/bridge additions เธ—เธตเน A-Conductor เธฃเนเธญเธเธเธญเน€เธ—เนเธฒเธเธฑเนเธ | GLM/ZCode | 2026-08-21 | hold | โ€” |
| ๐“ **Drive layer เธเธฑเธ”เน€เธฃเธตเธขเธเนเธฅเนเธง 2026-08-21**: `L:/My Drive/A-Wiki-Data` เธกเธต `AGENTS.md` (เธเธ 3 เธเนเธญ เธชเธณเธซเธฃเธฑเธเธ—เธธเธ agent) + `LAYOUT.md` (เธซเธเธถเนเธ role = เธซเธเธถเนเธ path) + `inbox/` (เนเธกเนเธฃเธนเนเธเธฐเธงเธฒเธเนเธซเธ โ’ เธงเธฒเธเธ—เธตเนเธเธฑเนเธ เธซเนเธฒเธกเธชเธฃเนเธฒเธเนเธเธฃเธเธชเธฃเนเธฒเธเนเธซเธกเน) + `_archive/` (MANIFEST เธเธฃเธ) ยท agents เธ—เธตเนเธเธฐเน€เธเธตเธขเธเธฅเธ drive เธ•เนเธญเธเธญเนเธฒเธเธชเธญเธเนเธเธฅเนเธเธฑเนเธเธเนเธญเธ | GLM/ZCode | 2026-08-21 | done | โ€” |
| โ… FOLLOW-UPS เธเธดเธ”เธซเธกเธ” 2026-08-21 เน€เธเนเธฒ: (1) <ESTATE> dir-name scrub เนเธฅเนเธง (2) quickchart allowlist เนเธฅเนเธง (3) stash เน€เธเนเธฒ 2 เธ•เธฑเธง drop (archive เธ—เธตเน .tmp/stash-archive-20260821) (4) hospital identifier โ’ get_hospital_dir + AWIKI_HOSPITAL_DIR env โ€” เน€เธเธฃเธทเนเธญเธเธ—เธตเนเนเธเนเนเธเธฅเน€เธ”เธญเธฃเนเธเธฃเธดเธ เธ•เธฑเนเธ `AWIKI_HOSPITAL_DIR=<เธเธทเนเธญเนเธเธฅเน€เธ”เธญเธฃเน>` เนเธ shell profile | GLM/ZCode | 2026-08-21 | done | โ€” |

| โ… Phase 6 hook-engine โ€” **MERGED (PR #17)** self-review PASS_WITH_NOTES 2026-08-21 | GLM/ZCode | done | โ€” | merged |
| โ… Agent Continuity Gate โ€” **MERGED (PR #18)** | GLM/ZCode | done | โ€” | merged |
| โ… Scanner strict pattern-source โ€” **MERGED (PR #19)** | GLM/ZCode | done | โ€” | merged |
| โ… duplicate branch `phase6-hook-engine-consolidation` โ€” เธ•เธฃเธงเธเนเธฅเนเธง: docs-only เธเธเธฑเธ superseded โ’ **เธฅเธเนเธฅเนเธง** 2026-08-21 |
| WO-RFR-20260824 stale branch reconciliation evidence | ChatGPT-GPT-5.6-Sol | 2026-08-28 | COLLAB.md; docs/work-orders/WO-RFR-20260824.md | docs/wo-rfr-branch-reconciliation-20260828 |
| WO-DASH-SEC-20260828 A-Wiki Live loopback write-surface hardening | ChatGPT-GPT-5.6-Sol | 2026-08-28 | COLLAB.md; docs/work-orders/WO-DASH-SEC-20260828.md; scripts/live-dashboard/server.py; tests/test_dashboard_security.py; tests/test_dashboard_autostart.py; scripts/dashboard-ensure.sh | fix/wo-dash-sec-20260828-loopback |
| WO-DASH-SEC-20260828 CSRF and state-changing GET hardening | ChatGPT-GPT-5.6-Sol | 2026-08-28 | scripts/live-dashboard/src/graph.js; scripts/live-dashboard/fixes.html; scripts/live-dashboard/README.md; tests/test_dashboard_security.py | fix/wo-dash-sec-20260828-loopback |
| WO-DASH-SEC-20260828 dashboard shipped bundle refresh | ChatGPT-GPT-5.6-Sol | 2026-08-28 | scripts/live-dashboard/app.min.js; scripts/live-dashboard/app.min.js.map; scripts/live-dashboard/package-lock.json | fix/wo-dash-sec-20260828-loopback |

**Night-shift log 2026-08-21 (เธ•เนเธญเน€เธเธทเนเธญเธ):** PR #20 **A-Wiki Conductor v0.1.0 MERGED** (user-delegated self-review; `python -m conductor status|gate|plan` เนเธเนเนเธ”เนเธเธฃเธดเธ; Serena MIT credited) ยท Phase 6/#17/#18/#19 เธเธดเธ”เธซเธกเธ”

**Night-shift log 2026-08-20:** main เธ–เธนเธเธเนเธญเธก (revert `59ebdede` เธเธญเธ auto-commit เน€เธชเธตเธข `c343542c` โ€” เน€เธเนเธฒเธเธญเธ commit เธกเธฒเธเธฒเธ MacBook เธเธญเธเน€เธเนเธฒเธเธญเธ repo เน€เธญเธ) ยท เธ—เธธเธ PR เธเนเธฒเธ CI ยท stop-auto-commit เธ•เธดเธ” gate 2 เธเธฑเนเธเนเธฅเนเธง (noise เธฅเนเธงเธเนเธกเน push + scan เนเธกเนเธเนเธฒเธเนเธกเน push) โ€” เน€เธซเธ•เธธเธเธฒเธฃเธ“เนเนเธเธเธเธตเนเนเธกเนเธเธงเธฃเน€เธเธดเธ”เธเนเธณ

> เธเนเธญเธเธชเธฃเนเธฒเธ branch/เน€เธฃเธดเนเธกเธเธฒเธเนเธซเธกเน: เธญเนเธฒเธเธ•เธฒเธฃเธฒเธเธเธตเน + `git branch -a` เธเนเธญเธเน€เธชเธกเธญ โ€” เธเธทเนเธญเธเธฒเธเนเธเธฅเนเน€เธเธตเธขเธ = เธซเนเธฒเธกเน€เธฃเธดเนเธก เนเธซเน claim เธ•เนเธญเธเธฒเธเธเธญเธเน€เธ”เธดเธก (Rule 7)

## เธเธ•เธดเธเธฒ 8 เธเนเธญ (เธขเนเธญ โ€” เธเธเธฑเธเน€เธ•เนเธกเนเธเนเธเธฅเน protocol)

1. Claim เธเนเธญเธเธ—เธณ (commit+push เนเธ–เธง claim เธเนเธญเธเน€เธฃเธดเนเธก); เธซเนเธฒเธกเนเธ•เธฐ scope เธเธญเธ claim เธเธเธญเธทเนเธ
2. `git pull --ff-only` + build/test เธเนเธฒเธ เธเนเธญเธ push เธ—เธธเธเธเธฃเธฑเนเธ
3. Hotspot files เนเธเนเนเธ”เนเธ—เธตเธฅเธฐ agent เธ•เธฒเธกเธ•เธฒเธฃเธฒเธเธเนเธฒเธเธเธ
4. เนเธเธฅเนเน€เธ”เธตเธขเธงเธเธฑเธเธซเนเธฒเธกเธ—เธณเธเธฃเนเธญเธกเธเธฑเธ โ€” เธ”เธนเธ•เธฒเธฃเธฒเธ claim เธเนเธญเธ
5. **เธซเนเธฒเธก `git reset --hard` / `git checkout -- .` / `git clean` เนเธ shared tree** โ€” เนเธเน stash/revert; agent เธ—เธตเนเธ•เนเธญเธ reset เธเนเธญเธข โ’ agent เธญเธทเนเธเนเธขเธ git worktree + branch เนเธฅเนเธง merge เธเธฅเธฑเธ; เธซเนเธฒเธกเธฅเธ branch/worktree เธเธญเธเธเธฑเธ
6. เธ—เธธเธ chunk เธกเธต work order เนเธ `docs/work-orders/` + append Checkpoint เธ—เธธเธเธเธฃเธฑเนเธเธ—เธตเนเธซเธขเธธเธ”/เธชเนเธเธ•เนเธญ
7. Scope เธเธนเธเธเธฑเธ chunk เนเธกเนเธเธนเธเธเธฑเธ agent โ€” เนเธเธฃเธ–เธทเธญ claim เธเธเธเธฑเนเธเธ—เธณ (เธเธฅเนเธเธชเธฅเธฑเธเธกเธทเธญเธเนเธฒเธก 5-hr limit)
8. Additive-first: เธเธญเธเนเธซเธกเน = เนเธเธฅเนเนเธซเธกเน; เนเธเธฅเนเธฃเนเธงเธกเนเธเนเนเธ”เธขเธเธนเนเธ–เธทเธญ WO เน€เธ—เนเธฒเธเธฑเนเธ

## Pause โ’ Resume (เธ•เธดเธ” limit / เธชเธฅเธฑเธ agent)

เธซเธขเธธเธ”: commit เธเธฒเธเธเนเธฒเธ (build เธเธฑเธ โ’ branch `wip/<id>`) โ’ checkpoint + `โธ paused` + เธญเธฑเธเน€เธ”เธ• claim โ’ push
เธฃเธฑเธ: user เธงเธฒเธ prompt โ’ `เธญเนเธฒเธ COLLAB.md + docs/work-orders/<id>.md เธ—เธณเธ•เนเธญเธเธฒเธ Checkpoint เธฅเนเธฒเธชเธธเธ” เน€เธเธเธฒเธฐเนเธ Lane/files เธ—เธตเนเธฃเธฐเธเธธ เน€เธฃเธดเนเธกเธเธฒเธ branch เธ—เธตเนเธฃเธฐเธเธธ เน€เธชเธฃเนเธเนเธฅเนเธง merge main + set done`

