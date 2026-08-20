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
| ✅ **MERGED 2026-08-21 night-2: local rabies/domain stack (26 commits) integrated into vNext main** — canonical 3260/0 green, Core CI SUCCESS at `7b1b808e`; secrets prevented from entering git (.codex/config.toml untracked + tracked secret-free template); รพ. real name scrubbed → <HOSPITAL> | GLM/ZCode | 2026-08-21 | merge + repair | main `7b1b808e` |
| 📌 FOLLOW-UPS (จดไว้ให้ user): (1) sunday-estate dir-name → placeholder design (P0 pre-exists on origin) (2) quickchart support email allowlist (3) git stash เก่า 2 ตัว (C3-7 / ci-sim) ตรวจแล้ว **ไม่มี secret** แต่เป็นงานค้างยุคเก่า ให้ตัดสิน merge หรือทิ้ง (4) identifier "uthai" ใน drive_path/get_hospital_uthai_dir — rename เป็น <HOSPITAL> theme รอบถัดไป | GLM/ZCode | 2026-08-21 | audit | — |

| ✅ Phase 6 hook-engine — **MERGED (PR #17)** self-review PASS_WITH_NOTES 2026-08-21 | GLM/ZCode | done | — | merged |
| ✅ Agent Continuity Gate — **MERGED (PR #18)** | GLM/ZCode | done | — | merged |
| ✅ Scanner strict pattern-source — **MERGED (PR #19)** | GLM/ZCode | done | — | merged |
| ✅ duplicate branch `phase6-hook-engine-consolidation` — ตรวจแล้ว: docs-only ฉบับ superseded → **ลบแล้ว** 2026-08-21 |

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
