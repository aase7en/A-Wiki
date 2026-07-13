---
type: entity
title: Social Media Skills — Creator Workflow Source
category: tool
tags: [claude-skills, content-system, creator-layer, social-media, second-brain, public-safe]
sources: [github-social-media-skills, charliejhills-claude-skills-org-chart-2026]
created: 2026-05-30
updated: 2026-05-30
last_verified: 2026-05-30
verify_tool: git-clone
---

# Social Media Skills — Creator Workflow Source

> TL;DR: A-Wiki รับเฉพาะ workflow ที่คุ้มจาก `social-media-skills` มาทำเป็น Creator Layer แบบ Thai-first, private-first, และ Cost-first โดยเก็บ voice/analytics/drafts ไว้ใน `drive/personal/creator/`.

**ประเภท**: Claude Skills collection for social/content workflows  
**สถานะใน A-Wiki**: adopted as a lightweight A-Wiki Creator Layer at `skills/claude-code/awiki-creator-layer/`  
**License**: MIT  
**Upstream**: https://github.com/charlie947/social-media-skills  
**Snapshot checked**: `94f72ea2ece388fa30ef49a26fb2e6fd2109e0b1`

## ภาพรวม

`charlie947/social-media-skills` เป็น repo รวม 17 skills สำหรับระบบ content creator: voice profile, newsletter voice, LinkedIn posts, content matrix, analytics, niche research, image prompts, Reels, และ YouTube thumbnail. ตัว repo เบามากและเป็น Markdown workflow เป็นหลัก จึงเหมาะเอาแนวคิดมาใช้กับ A-Wiki โดยไม่เพิ่ม runtime หนัก.

## สิ่งที่ A-Wiki รับมา

| Upstream idea | A-Wiki implementation |
|---|---|
| `voice-builder` | สร้าง `about-me.md` + `voice.md` แต่เก็บใน `drive/personal/creator/` |
| `newsletter-voice` | เพิ่ม newsletter layer โดยไม่ duplicate voice profile |
| `content-matrix` | แปลง wiki domains/topic pillars เป็น idea grid |
| `post-writer` / `post-formatter` | แปลง wiki/source เป็น draft ที่มี evidence และ confidence marker |
| `hook-generator` | สร้าง hook หลายแบบแต่ตัด clickbait/engagement bait |
| `post-scorer` | score draft แบบ cached-first; paid scraping ต้องขออนุมัติ |
| `analytics-dashboard` | ใช้เฉพาะกับ private export ใน `drive/personal/creator/analytics/` |
| `niche-research` | ใช้แนว verified date/link; ถ้า ingest เข้า wiki ต้อง raw-first |

## สิ่งที่ไม่รับมาเป็น default

| Item | เหตุผล |
|---|---|
| Charlie Hills voice | เป็น personal style ของ upstream ไม่ใช่ A-Wiki voice |
| British English default | A-Wiki ใช้ Thai-first และเลือกภาษาเป็นรายงาน |
| LinkedIn-first assumptions | A-Wiki ต้องรองรับ Facebook, LINE, X, newsletter, blog, และ internal notes |
| Apify scraping by default | มี cost + privacy risk; ต้อง cached-first และ user approval |
| Root `about-me.md` / `voice.md` | เสี่ยงทำ repo public แล้วหลุด personal fingerprint |
| Fake trend scan | ขัด A-Wiki source provenance; ต้องมี date/link จริง |

## A-Wiki Fit

| Criterion | Assessment |
|---|---|
| Cost-first | ดีมาก: skill เป็น Markdown, ใช้ local wiki search ก่อน |
| Cross-platform | ดี: ไม่มี dependency บังคับ, ทำงานได้บน Mac/Windows/WSL ถ้า `drive/` พร้อม |
| Cross-device | ดี: personal files อยู่ Google Drive external data layer |
| Public-safe repo | ดีเมื่อใช้ `drive/personal/creator/` และไม่ commit analytics/drafts |
| Second brain | ชัดเจน: แปลงความรู้ใน wiki เป็น public communication layer |

## Security / Privacy Guardrails

- ข้อมูลส่วนตัว, writing samples, social analytics, draft ที่ยังไม่ sanitize ต้องอยู่ใน `drive/personal/creator/`.
- API keys ต้องผ่าน `drive/.secrets` และ local settings เท่านั้น.
- ห้ามใช้ paid scraping หรือ browser session ที่ล็อกอินโดยไม่แจ้ง cost/privacy impact.
- Output สาธารณะต้องผ่าน private-data check ก่อนส่ง.
- ถ้า source เป็น URL ใหม่และจะบันทึกลง wiki ให้ใช้ `ingest-source` เพื่อเก็บ raw provenance ก่อน.

## ความสัมพันธ์

- ใช้ร่วมกับ: [[ecc]] `content-engine`, `brand-voice`, `crosspost`
- ใช้ร่วมกับ: [[concepts/ai-tools/hooks-skills-plugins]] skill system
- เสริม: [[dual-ai-workflow]] และ [[openrouter-agent-routing]] สำหรับ Cost-first delegation

## แหล่งข้อมูล

- GitHub: https://github.com/charlie947/social-media-skills
- License: MIT
- [verified 2026-05-30] `git clone --depth 1`, `validate-skills.sh` ผ่าน 17 skills, repo size ประมาณ 356K
- [[sources/charliejhills-claude-skills-org-chart-2026]] — Charlie Hills ชู repo นี้เองในโพสต์ 42-skill org chart (แผนก Social Media) [verified 2026-07-13]
