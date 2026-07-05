---
type: entity
category: tool
tags: [claude-skills, engineering, productivity, upstream-tracked, typescript]
sources: []
created: 2026-07-05
updated: 2026-07-05
last_verified: 2026-07-05
verify_tool: WebFetch
---

# mattpocock/skills

**ประเภท**: Upstream source ของ engineering+productivity Claude Code skills
**สถานะ**: tracked via remote+refresh script at `skills/_upstream/mattpocock/` (working copies at `skills/mattpocock/`, used as-is — no local fork/modification)
**License**: MIT

## ภาพรวม

repo จาก **Matt Pocock** (AI Hero / Total TypeScript) — ชุด Claude Code skills เน้นลด "vibe coding" ด้วยการถาม requirement ให้ชัดก่อนเขียนโค้ด (grilling), บังคับ TDD, และรักษาสถาปัตยกรรมโค้ดให้ deep-module แทน shallow [verified 2026-07-05]

## Skills ที่ A-Wiki ใช้ (25 — ทุก engineering+productivity+misc skill ยกเว้น personal/in-progress/deprecated)

| Category | Skill | Purpose |
|----------|-------|---------|
| engineering | **ask-matt** | Router — ถามว่า skill ไหนเหมาะกับสถานการณ์ |
| engineering | **two-axis-code-review** *(เดิมชื่อ `code-review`)* | Review diff 2 แกน — Standards + Spec — ผ่าน parallel sub-agents |
| engineering | **codebase-design** | คำศัพท์ร่วมสำหรับออกแบบ deep module |
| engineering | **diagnosing-bugs** | Diagnosis loop สำหรับบัคยากและ performance regression |
| engineering | **domain-modeling** | สร้าง/ลับ domain model, ADR, glossary |
| engineering | **grill-with-docs** | สัมภาษณ์เค้นแผน + สร้าง ADR/glossary ไปพร้อมกัน (เรียก `/grilling`) |
| engineering | **implement** | Implement งานจาก PRD/issues ด้วย TDD |
| engineering | **improve-codebase-architecture** | สแกนหา deepening opportunities → HTML report → grill |
| engineering | **prototype** | Throwaway prototype ตอบคำถามการออกแบบ |
| engineering | **research** | Background agent ค้น primary source แล้วบันทึกเป็น .md |
| engineering | **resolving-merge-conflicts** | Resolve merge/rebase conflict ตาม intent เดิม ห้าม `--abort` |
| engineering | **setup-matt-pocock-skills** | ตั้งค่า issue tracker/labels ครั้งแรก |
| engineering | **tdd** | Red-green-refactor loop |
| engineering | **to-issues** | แตก plan เป็น issues แบบ tracer-bullet |
| engineering | **to-prd** | สรุปบทสนทนาเป็น PRD (ไม่สัมภาษณ์ซ้ำ) |
| engineering | **triage** | State machine คัดกรอง issues/PR |
| productivity | **grill-me** | สัมภาษณ์เค้นแผน (เรียก `/grilling`) — ตัวอย่างหลักที่ user ขอ |
| productivity | **grilling** | Engine เบื้องหลัง grill-me/grill-with-docs — ถามทีละข้อ พร้อมคำแนะนำ |
| productivity | **handoff** | สรุปบทสนทนาเป็น handoff doc ให้ agent ถัดไป |
| productivity | **teach** | สอน user เรื่องใหม่ข้ามหลาย session |
| productivity | **writing-great-skills** | หลักการเขียน skill ให้ predictable |
| misc | **git-guardrails-claude-code** | Hook บล็อก git command อันตราย (คล้าย A-Wiki's `check_bash_destructive_git.py` เดิม) |
| misc | **migrate-to-shoehorn** | Migrate `as` assertion → `@total-typescript/shoehorn` (TypeScript-specific) |
| misc | **scaffold-exercises** | สร้างโครง exercise directory |
| misc | **setup-pre-commit** | ตั้งค่า Husky pre-commit + lint-staged |

## Setup & refresh

```bash
bash scripts/refresh-mattpocock.sh
```

Script ทำ:
1. `git remote add mattpocock https://github.com/mattpocock/skills.git` (idempotent)
2. `git fetch mattpocock main`
3. Extract latest tree → `skills/_upstream/mattpocock/` via `git archive | tar -x` (no merge, no clean-tree requirement)

**A-Wiki ใช้ snapshot-only tracking (เหมือน ECC), ไม่ fork-and-modify (ต่างจาก 9arm-skills)**:

| Path | Role |
|------|------|
| `skills/_upstream/mattpocock/` | **read-only mirror** ของ upstream — refresh ทับได้ |
| `skills/mattpocock/<skill>/` | **A-Wiki working copy** — ใช้ตามต้นฉบับ ไม่แก้เนื้อหา (ยกเว้นเปลี่ยนชื่อ `code-review` → `two-axis-code-review`) |

หลัง refresh → ใช้ `diff` เพื่อดู upstream changes แล้ว cherry-pick skill ใหม่:
```bash
diff -ruN skills/mattpocock/tdd/ skills/_upstream/mattpocock/skills/engineering/tdd/
```

## Registration + cross-agent distribution

Skill ทั้ง 25 ตัวลงทะเบียนใน **`skills-registry.json`** (single source of truth, category `mattpocock`, `agents: ["all"]`) — ตาม 5-layer contract ที่ `docs/architecture/skill-architecture-plan.md` อธิบาย:

```bash
python scripts/regen-skill-surfaces.py   # regen kilo/gemini/cline/antigravity/hermes/AGENTS.md surfaces
bash scripts/link-my-skills.sh           # symlink farm → ~/.claude/skills/, ~/.codex/skills/, ~/.cline/skills/
```

Hermes (Telegram bot) ได้รับ skill ผ่าน `scripts/hermes/awiki-init-pi5.sh` Step 4b (`$HERMES_SKILLS/awiki/mattpocock/`) — ต้อง re-run sync script บน Pi5 เพื่อให้มีผลจริงบนเครื่องนั้น

**`.kilo/skills/grill-me`** (สำเนา manual เดิมก่อน integration นี้) ตอนนี้เป็น symlink ชี้กลับไปที่ `skills/mattpocock/grill-me/` — ไม่มีเนื้อหาซ้ำสองที่แล้ว

## ทำไมเปลี่ยนชื่อ `code-review` → `two-axis-code-review`

A-Wiki มี built-in Claude Code skill ชื่อ `code-review` อยู่แล้ว (review diff หา correctness bugs + simplification) — ชื่อชนกันตรงๆ กับ skill ของ Matt Pocock (review diff 2 แกน Standards+Spec) แม้ scope จะต่างกัน จึงเปลี่ยนชื่อไฟล์/registry entry เป็น `two-axis-code-review` (มี alias `code-review-mattpocock`) เพื่อไม่ให้ทับ/บดบัง built-in command

## ข้อดี / ข้อเสีย

| ข้อดี | ข้อเสีย |
|-------|---------|
| Track upstream อัตโนมัติ — ได้ skill ใหม่/แก้ไขจาก Matt Pocock ทันทีที่ refresh | บาง skill (migrate-to-shoehorn, scaffold-exercises) เฉพาะเจาะจงกับ TypeScript/Matt Pocock's own courses — ไม่ตรงกับ A-Wiki stack |
| MIT — ใช้ commercial ได้ | Active มาก (v1.0.1 มิถุนายน 2026) — diff ต้อง review บ่อยกว่า 9arm |
| grill-me/grilling คุณภาพสูง เค้นสัมภาษณ์ทีละข้อพร้อมคำแนะนำ | ชื่อ `code-review` ชนกับ built-in — ต้อง rename (แก้แล้ว) |
| ผูกกับ registry ใหม่ — ครอบคลุมทุก agent surface (Kilo/Gemini/Cline/Antigravity/Hermes) ไม่ใช่แค่ symlink farm เดิม | |

## ความสัมพันธ์

- ใช้ร่วมกับ: [[9arm-skills]] — engineering skills คนละชุด scope ต่างกัน (9arm = debug/review discipline, mattpocock = requirements+TDD+architecture)
- ใช้ร่วมกับ: [[ecc]] — ECC มี skills คล้ายกันบ้าง (code-review, tdd) แต่ mattpocock เน้นความลึกของ interview/grilling มากกว่า
- Aligned กับ: A-Wiki's Iron Law #1 "no production code without failing test first" — `tdd` skill สอดคล้องโดยตรง

## แหล่งข้อมูล

- GitHub: https://github.com/mattpocock/skills
- Author: Matt Pocock (AI Hero / Total TypeScript)
- [verified 2026-07-05] WebFetch + `git fetch` ตรง — MIT, v1.0.1, active
