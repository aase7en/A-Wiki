---
name: a-route
description: "Intent classifier → category bundle → chain. Auto-router ที่รับ user request, classify ประเภทงาน, suggest category + chain ที่เหมาะสม (รอ user confirm). Trigger: '/A', '/A-Route', natural language (no slash). Cross-agent via invocation_hint. Phase 1: 12 categories mapped (1 active = a-web, 2 existing = a-doc/a-plan, 9 stubbed for Phase 2)."
version: 1.0.0
author: A-Wiki
domain: [engineering, code]
lifecycle_phase: meta
category: pipeline
agents: [all, hermes]
invocation: manual
invocation_hint: "/A-Route"
# 2026-07-26: Phase 1 — 1 active bundle (a-web) + reuse a-doc/a-plan/a-debug/a-business.
# Phase 2: clone pattern ไป 8 categories อื่น (a-design/a-content/a-marketing/a-game/
# a-audit/a-arch/a-research/a-analyze/a-health/a-invest).
---

# A-Route — Intent → Category → Chain (auto-router)

> Entry point ของ A-Wiki Pro Workflow — รับ user request, classify intent, suggest
> category + chain. **SUGGEST + CONFIRM** (ไม่ auto-execute) — กัน misclassify.

## เมื่อไหร่ใช้

✅ ใช้:
- User พิมพ์ `/A` หรือของานที่ไม่รู้จัก skill ที่ตรงปุ๊ป
- อยาก auto-pick skill chain ตาม intent
- เริ่ม task non-trivial ที่อยาก pipeline

❌ ข้าม:
- User เรียก skill ตรงๆ (`/A-Debug`, `/A-Plan`, `/A-Doc` ...)
- Trivial: typo, lookup, 1-file edit

## Flow

```
user request
    │
    ▼
┌──────────────────────────┐
│ 1. KEYWORD MATCH         │  ← regex on Thai + English keywords
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│ 2. SCORE top-3 categories│  ← weighted match
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│ 3. SUGGEST + EXPLAIN     │  ← "น่าจะเป็น a-web เพราะ ..."
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│ 4. USER CONFIRMS         │  ← 1 question (or user พิมพ์เลือกเอง)
└────────────┬─────────────┘
             ▼
   dispatch → category bundle (a-web / a-doc / a-plan / ...)
              │
              ▼
        category จะสั่ง a-flow ด้วย chain variant ที่เหมาะสม
```

## Dispatch table (Phase 1)

| Category | Status | Trigger keywords (sample) | Chain variant |
|---|---|---|---|
| **a-web** | ✅ Active | เว็บ, web, frontend, landing, portfolio, react, vue, gsap, threejs, webgl, motion, animation | full 7-stage (a-flow) |
| a-doc | ✅ Existing | หนังสือ, ราชการ, docx, คำสั่ง, บันทึก, ประกาศ, โครงการ, JD, WI, SP | a-doc chain (8 types) |
| a-plan | ✅ Existing | ออกแบบ, design, UX, UI, database schema, architecture | a-plan chain |
| a-debug | ✅ Existing | แก้บั๊ก, error, crash, fail, broken, ไม่ทำงาน | a-debug chain |
| a-business | ⚠️ Stub | ธุรกิจ, business, finance, invoice, billing | stub → finance-pipeline |
| a-design | 🚧 Phase 2 | UX, UI design system, brand identity, logo | — |
| a-content | 🚧 Phase 2 | content, blog, article, เนื้อหา, SEO | — |
| a-marketing | 🚧 Phase 2 | ตลาด, marketing, campaign, social, ads | — |
| a-game | 🚧 Phase 2 | เกม, game, threejs, phaser, pixijs, blender | — |
| a-audit | 🚧 Phase 2 | ตรวจ, audit, review, security scan | — |
| a-arch | 🚧 Phase 2 | system architecture, refactor, microservices | — |
| a-research | 🚧 Phase 2 | วิจัย, research, literature, survey | — |
| a-analyze | 🚧 Phase 2 | วิเคราะห์, analyze, data, statistics, monte-carlo | — |
| a-health | 🚧 Phase 2 | สุขภาพ, medical, pharmacy, clinical, CDSS | — |
| a-invest | 🚧 Phase 2 | ลงทุน, invest, trading, portfolio, DeFi | — |
| **(default)** | ✅ Fallback | (no match) | full 7-stage a-flow generic |

## Keyword scoring

Score = `Σ(keyword_weight × match_count)` — top-3 categories เสนอ

```python
# Pseudocode (lib จริงอยู่ใน references/scorer.md หรือ Phase 2 lib)
CATEGORIES = {
    "a-web": {"เว็บ": 3, "web": 3, "frontend": 3, "react": 2, "vue": 2,
              "gsap": 3, "threejs": 2, "webgl": 3, "landing": 2, "portfolio": 2},
    "a-doc": {"หนังสือ": 3, "ราชการ": 3, "docx": 3, "คำสั่ง": 3, ...},
    ...
}
```

## Suggest + confirm pattern

```
A-Route: จาก "ทำ landing page สวยๆ มี animation scroll" น่าจะเป็น:
  1. a-web (score 12) — frontend + animation + landing ✅
  2. a-design (score 4) — อาจจะ
  3. a-content (score 2) — copy อาจเกี่ยว

เลือก category? (1/2/3 หรือพิมพ์ชื่ออื่น)
```

User confirm → A-Route เรียก category bundle → bundle สั่ง a-flow

## Category bundle interface (contract)

ทุก category bundle ต้องมี:
- `SKILL.md` — recipe: stages ที่ใช้ + skills เฉพาะ + defaults
- `references/stack-defaults.md` — stack/framework defaults (ถ้ามี)
- `references/skills-by-stage.md` — mapping stage → skills

A-Route เรียก:
```python
# Pseudocode
def dispatch(category, task):
    bundle = load_skill(f"a-{category}")
    chain = bundle.recipe.chain  # อาจจะ full 7 หรือ subset
    a_flow.start(goal=task, category=category, chain=chain)
```

## Cross-agent parity

- `agents: [all, hermes]` — visible ทุก agent
- `invocation_hint: "/A-Route"` + `aliases: ["/a", "/a-route", "aroute"]`
- `/A` ไม่ใช่ true slash command — LLM pattern-match (verified by explore agent)
- ถ้า agent รู้ MCP (Claude/Cursor) — Phase 3 จะมี `a_route` MCP tool

## Files

| File | Purpose |
|---|---|
| `SKILL.md` | This router (~140 lines) |
| `references/scorer.md` | Keyword scoring algorithm detail (Phase 2) |
| `references/dispatch-protocol.md` | Bundle interface contract (Phase 2) |

## Phase 2 roadmap

- Clone pattern จาก a-web → สร้าง 8 categories ที่เหลือ (design/content/marketing/game/audit/arch/research/analyze/health/invest)
- เพิ่ม keyword dictionaries (Thai + English + domain jargon)
- Scorer lib เป็น python module (`scripts/lib/a_route_scorer.py`)
- Telegram `/A <task>` command (Hermes gateway)

## Examples

**Web task**:
```
/A "ทำ portfolio site มี 3D hero + scroll animation"
→ A-Route: score a-web=15 (portfolio+3D+scroll)
→ suggest a-web
→ user confirm
→ a-web bundle starts a-flow with chain: ASK→DESIGN→PLAN→IMPLEMENT→REVIEW→TEST
  (skip DEBUG ถ้าไม่มี bug; DESIGN ใช้ gsap + webgl-3d-object + threejs)
```

**Doc task**:
```
/A "ทำประกาศนโยบายพลังงาน รพ."
→ A-Route: score a-doc=9 (ประกาศ+นโยบาย+พลังงาน)
→ suggest a-doc
→ user confirm
→ a-doc chain (format grill + dispatch types/announce/)
```

**Ambiguous**:
```
/A "วางแผนโครงสร้างทีม"
→ A-Route: a-plan=6 (วางแผน+โครงสร้าง), a-business=4 (ทีม)
→ suggest ทั้ง 2 + ให้ user เลือก
```
