---
name: cross-agent-work-orders
description: "Binding multi-agent coordination standard: work orders + claim table + lanes + pause/resume so any agent works a repo in parallel and hands off mid-chunk across 5-hr limits"
version: 1.0.0
author: A-Wiki (proven in env-wastewater-webapp, 2026-07-18)
tags: [awiki, multi-agent, collaboration, handoff, work-orders, git]
domain: [code]
lifecycle_phase: plan
---

# Cross-Agent Work Orders — ทำงานร่วม/ส่งต่อข้าม agent ทุกตัว

**ข้อบังคับ**: ทุก agent ที่ใช้สมอง A-Wiki (Claude, Codex, Cursor, Antigravity,
ZCode, Hermes, Kilo, Cline, Windsurf, ...) + ทุก repo ใหม่ ต้องใช้มาตรฐานนี้
เมื่อมีงาน multi-agent — protocol เต็ม: `docs/protocols/cross-agent-work-orders.md`

## ใช้เมื่อไหร่

- เริ่ม repo ใหม่ / เริ่มให้ ≥2 agent ทำ repo เดียวกัน
- agent ติด 5-hr limit กลาง chunk → ส่งต่อให้ตัวอื่นทำต่อ
- agent ชนกันใน working tree (งาน uncommitted โดนกวาด)

## Quick start

```bash
# ครั้งเดียวต่อ repo (จาก A-Wiki root; idempotent)
bash scripts/init-work-orders.sh /path/to/repo
# แล้วเติมเลน + hotspot files ใน COLLAB.md ของ repo นั้น
```

ทำงาน: สร้าง WO จาก `docs/work-orders/WO-TEMPLATE.md` → **claim** ในตาราง
`COLLAB.md` (commit+push ก่อนเริ่ม) → ทำตามกติกา 8 ข้อ → เสร็จ = ปลด claim
ใน commit ของ chunk เอง

## หัวใจกติกา (ฉบับย่อ — เต็มใน COLLAB.md)

- Claim ก่อนทำ · pull --ff-only + build ผ่านก่อน push · hotspot แก้ทีละ agent
- **ห้าม `git reset --hard`/`clean` ใน shared tree** — agent ที่ reset บ่อย
  (เช่น ZCode) ให้ตัวอื่นแยก `git worktree` + branch แล้ว merge กลับ main
- Scope ผูกกับ chunk ไม่ผูกกับ agent → ใครถือ claim คนนั้นทำ = สลับมือได้

## Pause → Resume

หยุด: commit งานค้าง (build พัง → `wip/<id>`) + append Checkpoint + `⏸ paused` + push
รับ: วาง prompt — *"อ่าน COLLAB.md + docs/work-orders/<id>.md ทำต่อจาก
Checkpoint ล่าสุด เฉพาะใน Lane/files ที่ระบุ เริ่มจาก branch ที่ระบุ
เสร็จแล้ว merge main + set done"*

## Reference implementation

`env-wastewater-webapp` — MIGRATION.md §Two-track F/Z + `docs/work-orders/`:
Claude ∥ ZCode คู่ขนานจริง, handoff จริง, รอดเหตุ reset --hard 3 รอบ
