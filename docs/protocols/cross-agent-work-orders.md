# Cross-Agent Work Orders — มาตรฐานบังคับ (binding) สำหรับทุก agent ทุก repo

> **สถานะ: ข้อบังคับ** ตั้งแต่ 2026-07-18 — ทุก AI Agent/IDE/CLI ที่ใช้สมอง A-Wiki
> (Claude, Codex, Cursor, Antigravity, ZCode, Hermes, Kilo, Cline, Windsurf, OpenClaw
> และตัวใหม่ในอนาคต) ต้องทำงานร่วม/ส่งต่อข้าม agent ผ่านระบบนี้ และ **repo ใหม่ทุกตัว
> ต้อง bootstrap ระบบนี้ก่อนเริ่มงาน multi-agent** (`bash scripts/init-work-orders.sh <repo>`)
>
> พิสูจน์จริงแล้วใน `env-wastewater-webapp` (2026-07-18): Claude (Track F) ∥ ZCode
> (Track Z) ทำงานพร้อมกัน, ส่งงานข้าม 5-hr limit ได้, และรอดจากเหตุการณ์ agent หนึ่ง
> `git reset --hard` กวาด working tree 3 รอบ — ดูของจริง: `MIGRATION.md` §Two-track
> + `docs/work-orders/` ใน repo นั้น

## เสา 3 ต้นของระบบ

1. **`COLLAB.md`** (root ของ repo) — เลนของแต่ละ agent + **ตาราง claim** + hotspot files + กติกา 8 ข้อ (สำเนาจาก template ปรับตาม repo)
2. **`docs/work-orders/<id>.md`** — ทุก chunk งานเป็นไฟล์ spec ที่ agent ใดก็หยิบทำ/ทำต่อได้: `Status / Lane-files / Branch / Goal+Acceptance / Steps / Verify / Checkpoint log`
3. **Pause–Resume protocol** — ติด limit/สลับ agent: commit งานค้าง → append checkpoint → resume prompt มาตรฐาน (ดู template README)

## กติกา 8 ข้อ (Rules — สำเนาลง COLLAB.md ของทุก repo)

1. **Claim ก่อนทำ**: เพิ่มแถวในตาราง claim (chunk, agent, วันที่, scope ไฟล์) → commit+push → ค่อยเริ่ม; เสร็จแล้วปลด claim ใน commit ของ chunk นั้นเอง — ห้ามแตะไฟล์ใน scope ของ claim คนอื่น
2. **Pull ก่อน commit เสมอ** (`git pull --ff-only`; diverge → rebase commit ตัวเอง) + build/test ของ repo ต้องผ่านก่อน push
3. **Hotspot files** ประกาศไว้ใน COLLAB.md (เช่น route file, package.json, entry html) — แก้ได้ทีละ agent ตามที่ระบุ
4. **ไฟล์เดียวกันห้ามทำพร้อมกัน** — ดูตาราง claim ก่อนเริ่มเสมอ
5. **ห้าม destructive git ใน shared tree**: `git reset --hard`, `git checkout -- .`, `git clean` ทำลายงาน uncommitted ของ agent อื่น — ใช้ `git stash`/`git revert`; agent ที่ workflow ตัวเองต้อง reset บ่อย (เช่น ZCode) ให้ agent อื่นที่ทำงานพร้อมกัน**แยกไป git worktree + branch ของตัวเอง** แล้ว merge กลับ main (pattern: `git worktree add ../<repo>-<track> -b <track>`; ห้ามลบ branch/worktree ของกันและกัน)
6. **Work order ก่อนเริ่มทุก chunk** + append **Checkpoint log** ทุกครั้งที่หยุด/ส่งต่อ (ทำถึงไหน, commit hash, เหลืออะไร, กับดัก)
7. **Scope ผูกกับ chunk ไม่ผูกกับ agent** — ใครถือ claim คนนั้นแตะไฟล์ใน scope ได้ (นี่คือกลไกสลับมือ)
8. **Additive-first**: feature ใหม่ = ไฟล์ใหม่; แก้ไฟล์ร่วม (routes/config) โดยผู้ถือ WO นั้นเท่านั้น ทีละ WO

## Pause → Resume (ติด 5-hr limit / สลับ agent / สลับ IDE)

**ฝั่งหยุด**: (1) build ผ่าน → commit เข้า branch ปกติ; ไม่ผ่าน → commit เข้า `wip/<id>` — **ห้ามทิ้ง uncommitted เด็ดขาด** (2) append checkpoint + Status `⏸ paused` + อัปเดตตาราง claim → push

**ฝั่งรับ** — user วาง resume prompt มาตรฐาน (ใช้ได้กับทุก agent):

```
อ่าน COLLAB.md + docs/work-orders/<id>.md ของ repo นี้
ทำต่อจาก Checkpoint ล่าสุด เฉพาะใน Lane/files ที่ระบุ
เริ่มจาก branch ที่ work order ระบุ; เสร็จแล้ว merge เข้า main + set done
```

## Model routing (ประหยัด credit — ผูกกับ Cost-First Pyramid)

ทุก WO ประกาศ `Model tier` บนหัวไฟล์ แล้ว user dispatch ตาม tier:

- **cheap-ok** (GLM/Sonnet-tier): งาน mechanical ที่ WO ให้ `Reference pattern`
  (ไฟล์+สิ่งที่ copy) ครบ — conformance, icon swap, CRUD UI ตาม golden reference
- **mid** (Opus-tier): reasoning ปานกลาง spec ปิดช่องแล้ว (mapping/สูตรอยู่ใน WO)
- **primary-only** (frontier model): design ใหม่, security, cross-system, แก้ protocol
  — และทำหน้าที่ **เขียน WO + ตรวจ diff งาน tier ล่าง** (Senior Critic ตาม Swarm Protocol)

WO ระดับ cheap-ok/mid ต้องมี `Reference pattern` + `Forbidden` (หยุด+checkpoint
เมื่อเจอนอก spec — ห้ามเดา) + `Verify commands` แบบ copy-paste — เกณฑ์ผ่าน
"junior test": อ่านแล้วทำได้โดยไม่ต้องถามเพิ่ม. ดูตัวจริง:
`env-wastewater-webapp/docs/work-orders/F4-page-conformance.md`.
เลือกรุ่นตามสด: `model-cost-switching` skill + `docs/protocols/model-switching.md`

## Bootstrap repo ใหม่ (หรือ repo เก่าที่ยังไม่มี)

```bash
bash scripts/init-work-orders.sh /path/to/repo   # จาก A-Wiki root — idempotent
```

ได้: `COLLAB.md` + `docs/work-orders/{README.md,WO-TEMPLATE.md}` + pointer ใน
AGENTS.md/CLAUDE.md ของ repo นั้น (ถ้ามี) — จากนั้นเติมชื่อเลน/hotspots ให้ตรง repo

## ความสัมพันธ์กับ protocol เดิม

- `cross-agent-plan-handoff.md` (handoff.md local) = ส่งต่อ **แผน/สถานะ session เดียว** — ยังใช้ตามเดิม
- **ไฟล์นี้** = ประสานงาน **หลาย agent ระดับ repo** (ทำพร้อมกัน + ส่งมือข้าม limit) — ใช้คู่กันได้: checkpoint ใน work order คือ handoff ฉบับผูกกับ chunk

*Skill: `cross-agent-work-orders` (registry) · Template: `templates/work-orders/` · ผ่าน Brain Improvement Gate: เบา (docs+script), cross-platform, public-safe, reusable, ทำให้ agent ทุกตัวทำงานร่วมกันได้จริง*
