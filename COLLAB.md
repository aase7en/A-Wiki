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
