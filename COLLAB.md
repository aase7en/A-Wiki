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
| WO-PORTABILITY-BASELINE-20260902 GPT Primary integration repair | ChatGPT-GPT-5.6-Sol | 2026-09-02 | COLLAB.md; docs/work-orders/WO-PORTABILITY-BASELINE-20260902.md; conductor/__main__.py; scripts/awiki-doctor.py; scripts/awiki-guide.py; scripts/check-graph-yaml.py; scripts/check_pr_loop.py; scripts/hooks/check_machine_path.py; scripts/hospital/verify_regression.py; scripts/mcp-wiki-server.py; tests/test_console_pipe_safety.py; tests/test_link_agent_configs.py; tests/test_link_my_skills.py; tests/test_rabies_regression.py | fix/wo-portability-primary-integration |


RFR continuity release 2026-09-01: M1-M8 are merge/post-merge verified and R-FR-001..011 is complete. No active R-FR claim remains. Historical MERGED/DONE/HOLD rows were removed from the active claim table; durable evidence remains in `docs/work-orders/WO-RFR-20260824.md` and Git history.

**Night-shift log 2026-08-21 (เธ•เนเธญเน€เธเธทเนเธญเธ):** PR #20 **A-Wiki Conductor v0.1.0 MERGED** (user-delegated self-review; `python -m conductor status|gate|plan` เนเธเนเนเธ”เนเธเธฃเธดเธ; Serena MIT credited) ยท Phase 6/#17/#18/#19 เธเธดเธ”เธซเธกเธ”

**Night-shift log 2026-08-20:** main เธ–เธนเธเธเนเธญเธก (revert `59ebdede` เธเธญเธ auto-commit เน€เธชเธตเธข `c343542c` โ€” เน€เธเนเธฒเธเธญเธ commit เธกเธฒเธเธฒเธ MacBook เธเธญเธเน€เธเนเธฒเธเธญเธ repo เน€เธญเธ) ยท เธ—เธธเธ PR เธเนเธฒเธ CI ยท stop-auto-commit เธ•เธดเธ” gate 2 เธเธฑเนเธเนเธฅเนเธง (noise เธฅเนเธงเธเนเธกเน push + scan เนเธกเนเธเนเธฒเธเนเธกเน push) โ€” เน€เธซเธ•เธธเธเธฒเธฃเธ“เนเนเธเธเธเธตเนเนเธกเนเธเธงเธฃเน€เธเธดเธ”เธเนเธณ

> เธเนเธญเธเธชเธฃเนเธฒเธ branch/เน€เธฃเธดเนเธกเธเธฒเธเนเธซเธกเน: เธญเนเธฒเธเธ•เธฒเธฃเธฒเธเธเธตเน + `git branch -a` เธเนเธญเธเน€เธชเธกเธญ โ€” เธเธทเนเธญเธเธฒเธเนเธเธฅเนเน€เธเธตเธขเธ = เธซเนเธฒเธกเน€เธฃเธดเนเธก เนเธซเน claim เธ•เนเธญเธเธฒเธเธเธญเธเน€เธ”เธดเธก (Rule 7)

## เธเธ•เธดเธเธฒ 8 เธเนเธญ (เธขเนเธญ โ€” เธเธเธฑเธเน€เธ•เนเธกเนเธเนเธเธฅเน protocol)

1. Claim before mutation via `python -m conductor claim ...` as the primary COLLAB row writer; if it succeeds, do not add a duplicate row manually. Commit+push the claim before touching the claimed scope; never touch another live claim scope.
2. `git pull --ff-only` + build/test เธเนเธฒเธ เธเนเธญเธ push เธ—เธธเธเธเธฃเธฑเนเธ
3. Hotspot files เนเธเนเนเธ”เนเธ—เธตเธฅเธฐ agent เธ•เธฒเธกเธ•เธฒเธฃเธฒเธเธเนเธฒเธเธเธ
4. เนเธเธฅเนเน€เธ”เธตเธขเธงเธเธฑเธเธซเนเธฒเธกเธ—เธณเธเธฃเนเธญเธกเธเธฑเธ โ€” เธ”เธนเธ•เธฒเธฃเธฒเธ claim เธเนเธญเธ
5. **เธซเนเธฒเธก `git reset --hard` / `git checkout -- .` / `git clean` เนเธ shared tree** โ€” เนเธเน stash/revert; agent เธ—เธตเนเธ•เนเธญเธ reset เธเนเธญเธข โ’ agent เธญเธทเนเธเนเธขเธ git worktree + branch เนเธฅเนเธง merge เธเธฅเธฑเธ; เธซเนเธฒเธกเธฅเธ branch/worktree เธเธญเธเธเธฑเธ
6. เธ—เธธเธ chunk เธกเธต work order เนเธ `docs/work-orders/` + append Checkpoint เธ—เธธเธเธเธฃเธฑเนเธเธ—เธตเนเธซเธขเธธเธ”/เธชเนเธเธ•เนเธญ
7. Scope เธเธนเธเธเธฑเธ chunk เนเธกเนเธเธนเธเธเธฑเธ agent โ€” เนเธเธฃเธ–เธทเธญ claim เธเธเธเธฑเนเธเธ—เธณ (เธเธฅเนเธเธชเธฅเธฑเธเธกเธทเธญเธเนเธฒเธก 5-hr limit)
8. Additive-first: เธเธญเธเนเธซเธกเน = เนเธเธฅเนเนเธซเธกเน; เนเธเธฅเนเธฃเนเธงเธกเนเธเนเนเธ”เธขเธเธนเนเธ–เธทเธญ WO เน€เธ—เนเธฒเธเธฑเนเธ

## Pause โ’ Resume (เธ•เธดเธ” limit / เธชเธฅเธฑเธ agent)

เธซเธขเธธเธ”: commit เธเธฒเธเธเนเธฒเธ (build เธเธฑเธ โ’ branch `wip/<id>`) โ’ checkpoint + `โธ paused` + เธญเธฑเธเน€เธ”เธ• claim โ’ push
Receive: fetch origin -> read `BRAIN-ENTRY.md` -> `COLLAB.md` -> the SAME WO/checkpoint -> branch/PR. If direct invocation is unavailable, human relays only the WO-ID pointer; receiver resumes the assigned READY lane and does not ask the human to relay detailed results.

