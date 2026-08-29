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
| ✅ **MERGED 2026-08-26: WO-RFR-20260824 governance PR #26 → main `f0c3a78e`** — reviewer (GLM/ZCode) re-ran all claimed validation on branch HEAD (5/5 handoff tests · privacy clean · health 0 hard), added Loop-Evidence + cross-ref of Binding Loop Engineer ↔ Universal Loop Contract (`fe80c1d0`), fixed pr-loop-gate head.sha checkout bug on main (`c140b0d1`, TDD), all 3 checks green at `a68d8fc5`, user-authorized merge + fetch-verified · **next: M1 baseline evidence → Group A R-FR-002** | ChatGPT Sol (plan author) + GLM/ZCode (review/merge) | 2026-08-24 | `AGENTS.md`, `docs/migration/awiki-vnext-plan.md`, `docs/work-orders/WO-RFR-20260824.md`, `docs/protocols/cross-agent-plan-handoff.md`, `COLLAB.md` | main `f0c3a78e` |
| ✅ **MERGED 2026-08-21 night-2: local rabies/domain stack (26 commits) integrated into vNext main** — canonical 3260/0 green, Core CI SUCCESS at `7b1b808e`; secrets prevented from entering git (.codex/config.toml untracked + tracked secret-free template); รพ. real name scrubbed → <HOSPITAL> | GLM/ZCode | 2026-08-21 | merge + repair | main `7b1b808e` |
| ✅ **Fast-graph brain plan 3 slices MERGED 2026-08-21** (user-approved): S1 PR#23 bridge `search/related/hubs` (hybrid FTS+vec) + recall→BM25 · S2 PR#24 skill tier-2 description-fallback (226 triggerless skills หาได้แล้วโดยไม่อ่าน index 81KB) + SKILL-INDEX search-first mandate · S3 symlink farm pruned โดย post-merge relink (323→94, 0 broken, surfaces no-drift) | GLM/ZCode | 2026-08-21 | done | main `992fa059` |
| ⏸️ **HOLD เฟส 8–11 (user decision 2026-08-21):** หยุดงาน migration ฝั่งสมอง รอ A-Conductor (repo แยก) สร้างเสร็จก่อน — ฝั่งนั้นกำลังทำงานเพิ่มจากแผนเดิม กลัวชนกัน · agent ตัวถัดไป **ห้ามเริ่มเฟส 8+ โดยไม่มีคำสั่งใหม่จาก user** · งานที่ยังทำได้: bug fix/gates/bridge additions ที่ A-Conductor ร้องขอเท่านั้น | GLM/ZCode | 2026-08-21 | hold | — |
| 📂 **Drive layer จัดเรียงแล้ว 2026-08-21**: `L:/My Drive/A-Wiki-Data` มี `AGENTS.md` (กฎ 3 ข้อ สำหรับทุก agent) + `LAYOUT.md` (หนึ่ง role = หนึ่ง path) + `inbox/` (ไม่รู้จะวางไหน → วางที่นั่น ห้ามสร้างโครงสร้างใหม่) + `_archive/` (MANIFEST ครบ) · agents ที่จะเขียนลง drive ต้องอ่านสองไฟล์นั้นก่อน | GLM/ZCode | 2026-08-21 | done | — |
| ✅ FOLLOW-UPS ปิดหมด 2026-08-21 เช้า: (1) <ESTATE> dir-name scrub แล้ว (2) quickchart allowlist แล้ว (3) stash เก่า 2 ตัว drop (archive ที่ .tmp/stash-archive-20260821) (4) hospital identifier → get_hospital_dir + AWIKI_HOSPITAL_DIR env — เครื่องที่ใช้โฟลเดอร์จริง ตั้ง `AWIKI_HOSPITAL_DIR=<ชื่อโฟลเดอร์>` ใน shell profile | GLM/ZCode | 2026-08-21 | done | — |

| ✅ Phase 6 hook-engine — **MERGED (PR #17)** self-review PASS_WITH_NOTES 2026-08-21 | GLM/ZCode | done | — | merged |
| ✅ Agent Continuity Gate — **MERGED (PR #18)** | GLM/ZCode | done | — | merged |
| ✅ Scanner strict pattern-source — **MERGED (PR #19)** | GLM/ZCode | done | — | merged |
| ✅ duplicate branch `phase6-hook-engine-consolidation` — ตรวจแล้ว: docs-only ฉบับ superseded → **ลบแล้ว** 2026-08-21 |
| WO-RFR-20260824 stale branch reconciliation evidence | ChatGPT-GPT-5.6-Sol | 2026-08-28 | COLLAB.md; docs/work-orders/WO-RFR-20260824.md | docs/wo-rfr-branch-reconciliation-20260828 |
| WO-RFR-20260824 Y1 prompt producer restoration | ChatGPT-GPT-5.6-Sol | 2026-08-29 | COLLAB.md; docs/work-orders/WO-RFR-20260824.md; scripts/hooks/log_subagent_result.py; tests/test_log_subagent_result.py | fix/wo-rfr-y1-prompt-producer |
| WO-DASH-SEC-20260828 A-Wiki Live loopback write-surface hardening | ChatGPT-GPT-5.6-Sol | 2026-08-28 | COLLAB.md; docs/work-orders/WO-DASH-SEC-20260828.md; scripts/live-dashboard/server.py; tests/test_dashboard_security.py; tests/test_dashboard_autostart.py; scripts/dashboard-ensure.sh | fix/wo-dash-sec-20260828-loopback |
| WO-DASH-SEC-20260828 CSRF and state-changing GET hardening | ChatGPT-GPT-5.6-Sol | 2026-08-28 | scripts/live-dashboard/src/graph.js; scripts/live-dashboard/fixes.html; scripts/live-dashboard/README.md; tests/test_dashboard_security.py | fix/wo-dash-sec-20260828-loopback |
| WO-DASH-SEC-20260828 dashboard shipped bundle refresh | ChatGPT-GPT-5.6-Sol | 2026-08-28 | scripts/live-dashboard/app.min.js; scripts/live-dashboard/app.min.js.map; scripts/live-dashboard/package-lock.json | fix/wo-dash-sec-20260828-loopback |

**Night-shift log 2026-08-21 (ต่อเนื่อง):** PR #20 **A-Wiki Conductor v0.1.0 MERGED** (user-delegated self-review; `python -m conductor status|gate|plan` ใช้ได้จริง; Serena MIT credited) · Phase 6/#17/#18/#19 ปิดหมด

**Night-shift log 2026-08-20:** main ถูกซ่อม (revert `59ebdede` ของ auto-commit เสีย `c343542c` — เจ้าของ commit มาจาก MacBook ของเจ้าของ repo เอง) · ทุก PR ผ่าน CI · stop-auto-commit ติด gate 2 ชั้นแล้ว (noise ล้วนไม่ push + scan ไม่ผ่านไม่ push) — เหตุการณ์แบบนี้ไม่ควรเกิดซ้ำ

> ก่อนสร้าง branch/เริ่มงานใหม่: อ่านตารางนี้ + `git branch -a` ก่อนเสมอ — ชื่องานใกล้เคียง = ห้ามเริ่ม ให้ claim ต่อจากของเดิม (Rule 7)

## กติกา 8 ข้อ (ย่อ — ฉบับเต็มในไฟล์ protocol)

1. Claim ก่อนทำ (commit+push แถว claim ก่อนเริ่ม); ห้ามแตะ scope ของ claim คนอื่น
2. `git pull --ff-only` + build/test ผ่าน ก่อน push ทุกครั้ง
3. Hotspot files แก้ได้ทีละ agent ตามตารางข้างบน
4. ไฟล์เดียวกันห้ามทำพร้อมกัน — ดูตาราง claim ก่อน
5. **ห้าม `git reset --hard` / `git checkout -- .` / `git clean` ใน shared tree** — ใช้ stash/revert; agent ที่ต้อง reset บ่อย → agent อื่นแยก git worktree + branch แล้ว merge กลับ; ห้ามลบ branch/worktree ของกัน
6. ทุก chunk มี work order ใน `docs/work-orders/` + append Checkpoint ทุกครั้งที่หยุด/ส่งต่อ
7. Scope ผูกกับ chunk ไม่ผูกกับ agent — ใครถือ claim คนนั้นทำ (กลไกสลับมือข้าม 5-hr limit)
8. Additive-first: ของใหม่ = ไฟล์ใหม่; ไฟล์ร่วมแก้โดยผู้ถือ WO เท่านั้น

## Pause → Resume (ติด limit / สลับ agent)

หยุด: commit งานค้าง (build พัง → branch `wip/<id>`) → checkpoint + `⏸ paused` + อัปเดต claim → push
รับ: user วาง prompt → `อ่าน COLLAB.md + docs/work-orders/<id>.md ทำต่อจาก Checkpoint ล่าสุด เฉพาะใน Lane/files ที่ระบุ เริ่มจาก branch ที่ระบุ เสร็จแล้ว merge main + set done`
