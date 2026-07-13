---
tags: [ai-tools, claude-skills, skill-collections, design-web, game, x-post]
type: source
title: "Charlie Hills — I turned Claude into an entire company (42-skill org chart)"
slug: charliejhills-claude-skills-org-chart-2026
date_ingested: 2026-07-13
original_file: raw/charliejhills-claude-skills-org-chart-2026.md
---

# Charlie Hills — "I turned Claude into an entire company" (42-skill org chart)

**ประเภท**: social-post (X/Twitter thread + org-chart infographic)
**วันที่**: 2026-07-12 (08:25 UTC — ถอดจาก tweet snowflake ID `2076221471375122811`)
**ผู้เขียน**: Charlie Hills — X: @charliejhills, GitHub: `charlie947`, Substack: charliehills.substack.com

> ที่มา: x.com เข้าจาก ingest session ไม่ได้ (proxy 403) — ingest จากสกรีนช็อต 5 ภาพของผู้ใช้; URL ที่ถูกตัดท้ายในภาพถูก reconstruct แล้ว verify ทีละตัว [verified 2026-07-13]
> หมายเหตุ routing: เขียนโดย primary agent (tier 00) — harness route ไม่ได้ใน remote session นี้ (drive/.secrets ไม่มี, credential bridge ถูก block) — บันทึก emergency ตาม docs/protocols/universal-routing.md ใน session-memory แล้ว

## ประเด็นหลัก

1. โพสต์เสนอ mental model "Claude = ทั้งบริษัท" โดยจัด skills เป็น org chart 7 แผนก มี `claude-code` เป็น CEO/"The Operating System"
2. ทุกลิงก์เป็น collection ที่ติดตั้งได้จริง — ผสม official (Anthropic repo + claude.com/plugins) กับ community repos
3. รายการเต็ม (URL verified ทุกตัว 2026-07-13):

| แผนก | รายการในโพสต์ | Repo/URL (เต็ม) | สถานะ |
|---|---|---|---|
| Developers | Superpowers | github.com/obra/superpowers | 253k★ [verified 2026-07-13] |
| Developers | Context7 | github.com/upstash/context7 | 59k★ [verified 2026-07-13] |
| Developers | Skill Creator / MCP Builder / Webapp Testing | github.com/anthropics/skills | 161k★ official [verified 2026-07-13] |
| Developers | Claude-Mem | github.com/thedotmack/claude-mem | 87k★ Apache-2.0 [verified 2026-07-13] |
| Designers | UI UX Pro Max | github.com/nextlevelbuilder/ui-ux-pro-max-skill | [verified 2026-07-13] |
| Designers | Taste + Frontend Design | github.com/Leonxlnx/taste-skill | 59.4k★ [verified 2026-07-13] |
| Designers | Transitions | github.com/Jakubantalik/transitions.dev | [verified 2026-07-13] |
| Designers | Web Artifacts / Brand Guidelines | github.com/anthropics/skills | (repo เดียวกับข้างบน) |
| Marketing | 45 skills | github.com/coreyhaines31/marketingskills | [verified 2026-07-13] |
| Social Media | 17 skills | github.com/charlie947/social-media-skills | repo ของผู้โพสต์เอง [verified 2026-07-13] |
| Finance | 8 skills | claude.com/plugins/finance | official Anthropic [verified 2026-07-13 ผ่าน search — claude.com ถูก proxy บล็อก] |
| Small Business | 31 skills | claude.com/plugins/small-business | official [verified 2026-07-13 ผ่าน search] |
| Legal | 9 skills | claude.com/plugins/legal | official [verified 2026-07-13 ผ่าน search] |

## ข้อมูลที่น่าสนใจ / สถิติ

- Star counts ณ วันที่ verify: superpowers 253k★, anthropics/skills 161k★, claude-mem 87k★, context7 59k★, taste-skill 59.4k★ (+347% vs มี.ค. 2026)
- taste-skill = suite 11 variants + 3 image-gen skills, install name คงที่ `design-taste-frontend` (v2 experimental เป็น default)
- ui-ux-pro-max = searchable local DB: 50+ styles, 161 palettes, 57 font pairings, 99 UX guidelines, 25 chart types ครอบคลุม 10 stacks
- transitions.dev = 18 CSS transitions + คำสั่ง `transitions reveal/review/apply` + เครื่องมือ Refine tuning
- claude.com/plugins (Finance/Small Business/Legal) คือ official Anthropic plugin directory — Legal ใช้ระบบ GREEN/YELLOW/RED clause flagging
- claude-mem: capture ทุกอย่างที่ agent ทำ → compress ด้วย AI → inject กลับ session ถัดไป (SQLite + vector search, lifecycle hooks)

## ข้อโต้แย้งหรือความขัดแย้ง

- **เลข "42 skills" ไม่ตรงผลรวมจริง** — collections ที่ลิงก์รวมกัน >150 skills (45 marketing + 17 social + 8 finance + 31 small-biz + 9 legal + ฝั่ง dev/design) — 42 น่าจะนับเฉพาะการ์ดบน infographic
- **Conflict of interest เบา ๆ**: แผนก Social Media ลิงก์ repo ของ Charlie เอง (`charlie947/social-media-skills`) — A-Wiki มี [[entities/ai-tools/social-media-skills]] อยู่แล้วและเคยประเมิน upstream นี้ (rejected "Charlie Hills voice" style)
- **ฝั่ง official ไม่มีอะไรใหม่สำหรับ A-Wiki**: 5 skills จาก anthropics/skills ที่โพสต์ไฮไลต์ (skill-creator, mcp-builder, webapp-testing, web-artifacts-builder, brand-guidelines) vendor ไว้ที่ `skills/anthropic-skills/` ครบแล้ว — ดู [[entities/ai-tools/anthropic-skills]]
- **ไม่มีแผนก game เลย**: org chart ไม่ครอบคลุม game dev — gap analysis ของ A-Wiki: [[synthesis/claude-skills-gap-web-game-2026]]

## หน้า Wiki ที่ได้รับการอัปเดต

- [[synthesis/claude-skills-gap-web-game-2026]] — gap analysis จากโพสต์นี้ (สร้างใหม่)
- [[entities/ai-tools/taste-skill]] / [[entities/ai-tools/ui-ux-pro-max]] / [[entities/ai-tools/transitions-dev]] — design candidates (สร้างใหม่)
- [[entities/ai-tools/claude-mem]] / [[entities/ai-tools/superpowers]] / [[entities/ai-tools/context7]] — dev/memory candidates (สร้างใหม่)
- [[entities/ai-tools/anthropic-skills]] — bump last_verified + star count
- [[entities/ai-tools/social-media-skills]] — เพิ่ม source ref
- [[synthesis/design-web-capability-hub]] / [[synthesis/game-lightweight-highend-capability-hub]] — เพิ่มแถว candidates
