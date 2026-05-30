---
name: awiki-creator-layer
description: Turn A-Wiki notes, wiki pages, source summaries, and personal voice files into public-safe Thai-first posts, newsletters, content matrices, hooks, and publishing drafts. Use when the user asks to build a personal content system, learn their voice, turn wiki knowledge into social/newsletter content, score a draft, create a content calendar, or repurpose A-Wiki as a second-brain publishing engine.
origin: adapted from charlie947/social-media-skills commit 94f72ea2ece388fa30ef49a26fb2e6fd2109e0b1
license: MIT upstream; A-Wiki adaptation
---

# A-Wiki Creator Layer

เป้าหมาย: แปลง second brain ใน A-Wiki เป็น output สาธารณะที่อ่านง่าย โดยยังรักษา Cost-first, cross-device, public-safe repo, และภาษาไทยเป็นหลัก.

## Hard Rules

1. **Private-first**: ห้ามเขียน voice profile, writing samples, LinkedIn exports, analytics, social cache, หรือ draft ส่วนตัวลง tracked repo. ใช้ `drive/personal/creator/` เท่านั้น.
2. **Repo-safe output**: tracked repo เก็บได้เฉพาะ skill, template, protocol, และ wiki metadata ที่ไม่มีข้อมูลส่วนตัว.
3. **A-Wiki voice, not Charlie voice**: ห้าม default เป็น Charlie Hills, British English, LinkedIn guru cadence, forced clickbait, หรือ engagement bait.
4. **Thai-first**: ตอบ/ร่างเป็นไทยก่อน ยกเว้น user ขออังกฤษ หรือ platform ต้องการอังกฤษ. Technical term ใช้ทับศัพท์ได้พร้อมคำอธิบายเมื่อจำเป็น.
5. **Source-first**: เริ่มจาก wiki/source จริงเสมอ. ถ้าเป็น trend/latest ต้อง verify web พร้อมวันที่และ link จริง. ถ้าจะ ingest เข้า wiki ให้ทำ raw-first ตาม `ingest-source`.
6. **Cost-first**: เริ่ม Level -1 local wiki search ก่อน. ใช้ free/cheap delegate เฉพาะงาน search/research/compare. ห้ามเรียก paid scraping หรือ API โดยไม่บอก cost และรออนุมัติ.

## Private Layout

ใช้ path นี้เป็นมาตรฐานข้ามเครื่อง:

```text
drive/personal/creator/
├── about-me.md
├── voice.md
├── newsletter-voice.md
├── drafts/
├── analytics/
└── social-cache/
```

ถ้า `drive/` ไม่พร้อม ให้หยุดและบอก user ให้รัน `bash scripts/setup-local.sh` หรือ `bash scripts/setup-cloud-link.sh --status`. อย่าสร้าง fallback ใน repo root.

## Workflow

### 1. Load Context Cheaply

ใช้เท่าที่จำเป็น:

```bash
python3 scripts/wiki/search-wiki.py "<topic>"
```

ถ้ารู้ไฟล์แล้วอ่านตรง. ถ้าต้อง synthesize หลายหน้าใน domain เดียว ใช้ `ask-notebooklm` หรือ delegate ตาม Cost Pyramid.

### 2. Build Or Refresh Voice

ถ้าไม่มี `drive/personal/creator/voice.md`:

1. ถามสั้นๆ: เจ้าของเสียงคือใคร, เขียนให้ใคร, 3-5 topic pillars, จุดยืนที่ต่างจากคนอื่น, สิ่งที่ห้ามเขียน.
2. ขอ writing samples 3-5 ชิ้น. ถ้าเป็น private ให้เก็บไว้ใน `drive/personal/creator/`.
3. เขียน `about-me.md` ไม่เกิน 300 คำ และ `voice.md` ไม่เกิน 500 คำ.
4. บันทึกเฉพาะ pattern ที่ evidence มีจริง: rhythm, tone, hook, closing, banned words, absence patterns.

ถ้ามีอยู่แล้ว ให้อ่านและใช้เป็น source of truth. อย่าสร้าง voice profile ซ้ำ.

### 3. Pick Output Mode

| User asks for | Output |
|---|---|
| post ideas / calendar | Content matrix: 3-5 pillars x 8 formats |
| post / caption | One platform-native draft, source table, quality gate |
| newsletter | Outline first, then issue draft using `newsletter-voice.md` |
| hook | 6 hooks: practical, analytical, contrarian, story, list, question-free |
| score/review draft | Scorecard against voice + cached analytics if available |
| trending/niche research | Verified table with source/date/link; no padding |

### 4. Draft With Evidence

Every public draft should include:

- source basis: wiki path, raw/source link, or user-provided sample
- confidence marker: `[wiki]`, `[verified YYYY-MM-DD]`, or `[training]`
- private-data check: no addresses, phone numbers, customer names, secrets, account paths, or internal-only details
- platform fit: LinkedIn, Facebook, LINE, X, newsletter, or blog

### 5. Content Matrix

Use 3-5 pillars. Columns:

1. Actionable
2. Motivational
3. Analytical
4. Contrarian
5. Observation
6. X vs Y
7. Present vs Future
8. Listicle

Every cell must be a concrete headline, not a generic theme. For A-Wiki, prefer pillars from `about-me.md`, `wiki/context/wiki-overview.md`, and active project domains.

### 6. Score Drafts

Cached-first:

1. Read `voice.md`.
2. Look for `drive/personal/creator/analytics/` or `social-cache/`.
3. If no analytics, score against voice + platform basics and label it `generic baseline`.
4. If user wants scraping/API, state cost, provider, data stored path, then wait for approval.

Score 1-10:

| Criterion | Meaning |
|---|---|
| Hook clarity | first line has a concrete claim or tension |
| Voice match | matches `voice.md` and avoids banned patterns |
| Value density | teaches, compares, warns, or gives usable insight |
| Evidence | cites wiki/source or verified external link |
| Publish safety | no private leak, no fake metric, no unsupported claim |

## Quality Gate

Before final output:

- Remove Charlie-specific style, British spelling defaults, and "repost/comment below" bait.
- Keep Thai natural, not translated-English stiff.
- Do not invent metrics, dates, links, or personal stories.
- For time-sensitive claims, browse/verify or say data is insufficient.
- If publishing could expose private/business data, warn clearly and provide a sanitized alternative.

## Upstream Attribution

Adapted from the useful workflow ideas in `charlie947/social-media-skills`: voice-builder, newsletter-voice, content-matrix, post-writer, post-formatter, hook-generator, post-scorer, analytics-dashboard, and niche-research. Full upstream notice is in `references/upstream-social-media-skills.md`.
