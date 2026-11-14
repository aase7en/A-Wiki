# COLLAB — Multi-agent coordination (มาตรฐาน A-Wiki cross-agent-work-orders)

> Agent ทุกตัว (Claude/Codex/Cursor/Antigravity/ZCode/Hermes/Kilo/...) อ่านไฟล์นี้
> ก่อนเริ่มงานใน repo นี้ · Protocol เต็ม: A-Wiki `docs/protocols/cross-agent-work-orders.md`

## Lanes (ปรับตาม repo — ตัวอย่าง 2 เลน เพิ่มได้ตามจำนวน agent)

| Lane | ธีมงาน | ไฟล์ที่เป็นเจ้าของ | ห้ามแตะ |
|---|---|---|---|
| migration | A-Wiki vNext migration (phases, work orders, review flow) | `docs/migration/**`, `refactor/*` branches | ไฟล์ของเลนอื่น |
| hook-engine | hooks/registry/runner/provider adapters | `scripts/hooks/**`, `scripts/hooks_runner.py`, `scripts/cline-hooks/**`, `.claude/settings.json`, `.codex/hooks.json`, `.gemini/settings.json` | ไฟล์ของเลนอื่น |
| governance | protocols/claims/COLLAB/continuity | `COLLAB.md`, `docs/protocols/**`, `AGENTS.md` (แก้ต่อเมื่อมีสิทธิ์ตาม Iron Law #5) | ไฟล์ของเลนอื่น |
| wiki-knowledge | wiki pages + generated surfaces | `wiki/**`, `.wiki-graph.json`, `brain-map.canvas` | `scripts/**`, `docs/migration/**` |
| infra-CI | workflows, security/health scanners, baselines | `.github/workflows/**`, `scripts/security/**`, `scripts/health/**` | ไฟล์ของเลนอื่น |

**Hotspot files (แก้ทีละ agent ตามที่ระบุ):** `AGENTS.md` · `skills-registry.json` · `.claude/settings.json` · `.github/workflows/ci-core.yml` · `scripts/security/baseline.txt` — แก้ได้เฉพาะผู้ถือ claim ที่ระบุไฟล์เหล่านี้ใน scope

## In-progress claims (Rule 1 — claim ก่อนทำ, ปลดใน commit ของ chunk เอง)

| Chunk/WO | Agent | Claimed | Scope (files) | Branch / PR |
|---|---|---|---|---|
| ✅ **DONE 2026-09-04: G6FA592 gh-pages-sync evidence closure** — blob `f25656b3` identical (main = origin/gh-pages = origin/main = worktree = live site); deploy `e2ad9c63` 2026-07-17, workflow `pages-deploy.yml` run `29948330150` last success; duplicate `deploy-awiki-live.yml` already retired `8ff7d8fd` 2026-08-17 (nothing to delete); session-memory TODOs closed. Evidence-only — no tracked-file mutation beyond this row. | GLM/ZCode | 2026-09-04 | done | main |
| ✅ **DONE 2026-09-04: TD6088B wiki conflict-marker corruption fix** — resolved nested stash-conflict blocks in 6 nested CLAUDE.md (-10 lines each, clean date line kept); new guard `tests/test_no_conflict_markers.py` (RED→GREEN); full-tree `git grep '^<<<<<<< '` clean. Origin traced to c343542c era broken auto-commit. | GLM/ZCode | 2026-09-04 | done | main |
| Issue #58 claim authority convergence | chatgpt-sol | 2026-09-27 | COLLAB.md; docs/work-orders/WO-ISSUE-58-CLAIM-CONVERGENCE.md; conductor/bridge.py; conductor/gate.py; conductor/state.py; conductor/cli.py; scripts/lib/agent_claims.py; scripts/hooks/check_agent_claim.py; scripts/hooks/release_agent_claims.py; tests/test_agent_claims.py; tests/test_agent_claims_hook.py; tests/test_check_agent_claim_hook.py; tests/test_release_agent_claims_hook.py; tests/test_conductor.py; scripts/hooks_runner.py; tests/test_repo_root_seam.py; scripts/lib/neural_spine_mcp.py; tests/test_neural_spine_mcp.py; skills/awiki/a-claim/SKILL.md; skills-registry.json; scripts/skills_registry/generated/**; wiki/SKILL-INDEX.md; wiki/A-ROUTER.md; AGENTS.md; BRAIN-ENTRY.md; docs/protocols/cross-agent-work-orders.md; docs/protocols/agent-continuity-gate.md; tests/test_hook_engine.py; commands/A-Claim.md; conductor/README.md | fix/issue-58-claim-convergence |
| ✅ DONE 2026-11-11: WO-AWIKI-76-01 Compact Skill Cards — merged PR #77 as `f17ec316`; independent review + CI PASS; claim released | ChatGPT A-Conductor | 2026-11-09 | NEW scripts/skills_registry/skill_cards.py; NEW scripts/skill-cards.py; NEW tests/test_skill_cards.py; NEW docs/work-orders/WO-AWIKI-76-01-skill-cards.md; COLLAB.md claim row only | feat/76-compact-skill-cards |
| ✅ DONE 2026-11-11: WO-AWIKI-PIPE-01 — merged PR #79 as `fe1484fa`; review BLOCK→repair×2→APPROVE; post-main CI success; claim released | GLM (Kilo) | 2026-11-11 | NEW conductor/pipeline.py; conductor/cli.py pipeline wiring; NEW tests/test_conductor_pipeline.py; NEW docs/work-orders/WO-AWIKI-PIPE-01-conductor-pipeline-status.md; COLLAB.md claim row + WO-AWIKI-76-01 done marker | feat/conductor-pipeline-status |
| ✅ DONE 2026-11-12: WO-AWIKI-DEFUDDLE-01 — merged PR #80 as `7d5304dd`; review reproduce-and-verify + metric correction cycle; post-main CI success; claim released | GLM (Kilo) | 2026-11-11 | NEW tests/fixtures/defuddle/*.html (3 fixtures); NEW docs/work-orders/WO-AWIKI-DEFUDDLE-01-defuddle-evaluation.md; COLLAB.md claim row + WO-AWIKI-PIPE-01 done marker | feat/defuddle-evaluation |
| ✅ DONE 2026-11-12: WO-AWIKI-DEFUDDLE-02 — merged PR #81 as `0ab8790b`; review BLOCK(3×P2)→repair→APPROVE; CI 3/3; claim released | GLM (Kilo) | 2026-11-12 | scripts/wiki/scrape-advanced.py (additive defuddle tier+adapter only); NEW tests/test_scrape_defuddle.py; NEW docs/work-orders/WO-AWIKI-DEFUDDLE-02-defuddle-integration.md; COLLAB.md claim row + WO-AWIKI-DEFUDDLE-01 done marker | feat/defuddle-integration |
| ✅ DONE 2026-11-12: WO-AWIKI-INGEST-03 — merged PR #82 as `95074b38`; dual-engine review (GLM 4 findings + Terra 2 findings) all repaired; post-main CI success; claim released | GLM (Kilo) | 2026-11-12 | scripts/wiki/ingest-source.py additive hash+source_url+dedup+dry-run; tests/test_ingest_source.py additive class; NEW docs/work-orders/WO-AWIKI-INGEST-03-hash-dedup-dryrun.md; COLLAB.md claim row | feat/ingest-hash-dedup |
| ✅ DONE 2026-11-13: WO-AWIKI-INGEST-04 — merged PR #83 as `29dc5852`; terra 4-round review to APPROVE; post-main CI success; claim released | GLM (Kilo) | 2026-11-13 | scripts/wiki/scrape-advanced.py additive sidecar-original-html when defuddle wins; tests/test_scrape_defuddle.py additive class; NEW docs/work-orders/WO-AWIKI-INGEST-04-extraction-sidecar.md; COLLAB.md claim row + WO-AWIKI-INGEST-03 done marker | feat/defuddle-sidecar |
| ✅ DONE 2026-11-13: WO-AWIKI-SCRAPE-05 — merged PR #84 as `debe6653`; terra 4-round review (BLOCK×3→APPROVE) incl. pollution purge; CI 3/3; claim released | GLM (Kilo) | 2026-11-13 | scripts/wiki/scrape-advanced.py fix dead save-raw flag via path-override semantics; tests/test_scrape_advanced.py additive class; NEW docs/work-orders/WO-AWIKI-SCRAPE-05-save-raw-flag.md; COLLAB.md claim row + WO-AWIKI-INGEST-04 done marker | feat/save-raw-fix |
| ✅ DONE 2026-11-13: WO-AWIKI-TITLE-06 — merged PR #85 as `05931fbf`; terra 6-round review to APPROVE; CI 3/3; post-main CI success; claim released | GLM (Kilo) | 2026-11-13 | ingest-source binary refuse-hard + filename-stem title; tests; WO doc; SCRAPE-05 done marker | feat/markitdown-refuse |
| ✅ DONE 2026-11-13: WO-AWIKI-HYGIENE-07 — merged PR #86 as `efa80a72`; terra 7-round review to APPROVE; CI 3/3; post-main CI success; claim released | GLM (Kilo) | 2026-11-13 | test-pollution fixes: skills_service byte-restore; user_journey regen guard; hygiene guard test; WO doc; TITLE-06 done marker | feat/suite-hygiene |
| ✅ DONE 2026-11-13: WO-AWIKI-KILOSURF-08 — merged PR #87 as `efdce5c5`; terra 8-round review to APPROVE; CI 3/3; post-main CI success; claim released | GLM (Kilo) | 2026-11-13 | kilo runtime surface: regen syncs .kilo/kilo.jsonc skills.paths from registry; generator + RED test; WO doc; HYGIENE-07 done marker | feat/kilo-runtime-surface |
| ✅ DONE 2026-11-13: WO-AWIKI-KILOTPL-09 — merged PR #88 as `abff292a`; terra 5-round review to APPROVE; CI 3/3; post-main CI success; runbook executed (Mac render verified, Windows pulled via safe backup); claim released | GLM (Kilo) | 2026-11-13 | kilo template de-hardcode: __SKILLS_PATHS__ token rendered from generated kilo.skills-paths.json; render fail-loud without generated; tests; WO doc; KILOSURF-08 done marker | feat/kilo-template-registry |
| WO-DRIVE-LAYOUT-20260930 | GPT-5.6-Sol | 2026-09-30 | drive/LAYOUT.md;drive/personal-tools/userscripts/**;drive/backups/waste-ocr/**;drive/<HOSPITAL>/waste-ocr/**;drive/<HOSPITAL>/ocr-feedback/**;drive/ocr-feedback/**;docs/work-orders/WO-DRIVE-LAYOUT-20260930.md;scripts/drive_path.py;scripts/setup-cloud-link.sh;scripts/agent-preflight.py;scripts/health_external_data.py;scripts/hooks/check_drive_link.py;.github/workflows/ci-core.yml;wiki/context/ocr-learning-log.md;wiki/synthesis/waste-form-automation.md;tests/** | chore/drive-layout-cleanup-20260930 |
| A-SECURITY-CLOUDFLARE-UPSTREAM-20260921 | GPT-5.6-Sol | 2026-09-21 | COLLAB.md; docs/work-orders/WO-A-SECURITY-CLOUDFLARE-20260921.md; skills-registry.json; skills/awiki/a-security/**; scripts/refresh-cloudflare-security-audit.py; tests/test_refresh_cloudflare_security_audit.py; skills/_upstream/cloudflare-security-audit/**; generated skill surfaces from regen-skill-surfaces.py | feat/a-security-cloudflare-upstream |


Issue #54 ReviewBus release 2026-09-07: accepted head `905ee476d8622eb9e1426f03a5cdad6fda286ba7` merged via PR #56 as `967e063cb9dc2e5b43b48a00deb575235f125a94`; post-main Core CI `34133420008` SUCCESS. Q25/GLM1 implementation claim is released; durable evidence remains in `docs/work-orders/WO-REVIEW-BUS-ADDRESSED-BLOCKER-20260907.md`, Issue #54, PR #56 and Git history.

Target-repo primary repair release 2026-09-03: GPT trust-boundary repair is frozen for independent exact-SHA rereview; focused 73/73, related rerun 112/112, broad 203/203, privacy/stale/secret/wiki-health gates pass. No active GPT repair claim remains.

RFR continuity release 2026-09-01: M1-M8 are merge/post-merge verified and R-FR-001..011 is complete. No active R-FR claim remains. Historical MERGED/DONE/HOLD rows were removed from the active claim table; durable evidence remains in `docs/work-orders/WO-RFR-20260824.md` and Git history.

**Night-shift log 2026-08-21 (ต่อเนื่อง):** PR #20 **A-Wiki Conductor v0.1.0 MERGED** (user-delegated self-review; `python -m conductor status|gate|plan` ใช้ได้จริง; Serena MIT credited) · Phase 6/#17/#18/#19 ปิดหมด

**Night-shift log 2026-08-20:** main ถูกซ่อม (revert `59ebdede` ของ auto-commit เสีย `c343542c` — เจ้าของ commit มาจาก MacBook ของเจ้าของ repo เอง) · ทุก PR ผ่าน CI · stop-auto-commit ติด gate 2 ชั้นแล้ว (noise ล้วนไม่ push + scan ไม่ผ่านไม่ push) — เหตุการณ์แบบนี้ไม่ควรเกิดซ้ำ

> ก่อนสร้าง branch/เริ่มงานใหม่: อ่านตารางนี้ + `git branch -a` ก่อนเสมอ — ชื่องานใกล้เคียง = ห้ามเริ่ม ให้ claim ต่อจากของเดิม (Rule 7)

## กติกา 8 ข้อ (ย่อ — ฉบับเต็มในไฟล์ protocol)

1. Claim before mutation via `python -m conductor claim ...` as the primary COLLAB row writer; if it succeeds, do not add a duplicate row manually. Commit+push the claim before touching the claimed scope; never touch another live claim scope.
2. `git pull --ff-only` + build/test ผ่าน ก่อน push ทุกครั้ง
3. Hotspot files แก้ได้ทีละ agent ตามตารางข้างบน
4. ไฟล์เดียวกันห้ามทำพร้อมกัน — ดูตาราง claim ก่อน
5. **ห้าม `git reset --hard` / `git checkout -- .` / `git clean` ใน shared tree** — ใช้ stash/revert; agent ที่ต้อง reset บ่อย → agent อื่นแยก git worktree + branch แล้ว merge กลับ; ห้ามลบ branch/worktree ของกัน
6. ทุก chunk มี work order ใน `docs/work-orders/` + append Checkpoint ทุกครั้งที่หยุด/ส่งต่อ
7. Scope ผูกกับ chunk ไม่ผูกกับ agent — ใครถือ claim คนนั้นทำ (กลไกสลับมือข้าม 5-hr limit)
8. Additive-first: ของใหม่ = ไฟล์ใหม่; ไฟล์ร่วมแก้โดยผู้ถือ WO เท่านั้น

## Pause → Resume (ติด limit / สลับ agent)

หยุด: commit งานค้าง (build พัง → branch `wip/<id>`) → checkpoint + `⏸ paused` + อัปเดต claim → push
Receive: fetch origin -> read `BRAIN-ENTRY.md` -> `COLLAB.md` -> the SAME WO/checkpoint -> branch/PR. If direct invocation is unavailable, human relays only the WO-ID pointer; receiver resumes the assigned READY lane and does not ask the human to relay detailed results.
