---
name: a-design
description: "ออกแบบ UX/UI มืออาชีพ — ผูก ui-ux-pro-max (161 palettes + 99 rules) + taste-skill (anti-AI-slop) + transitions-dev + motion trio + accessibility เข้ากับ composition/gate layer แบบ StyleSeed (8 grammars × Quality Gate 0-100). Dispatcher ล้วน ไม่มีเทคนิคของตัวเอง. Trigger: 'ออกแบบ UX', 'design system', 'wireframe', 'visual hierarchy', 'UI สวย'."
version: 1.0.0
author: A-Wiki
domain: [design, ux-ui, engineering]
lifecycle_phase: meta
category: pipeline
agents: [all]
status: canonical
invocation: manual
invocation_hint: "/A-Design"
a_phase: design
---

# A-Design — งาน UX/UI design มืออาชีพ

> **Dispatcher ล้วน** — ไม่มีเทคนิคเป็นของตัวเอง หน้าที่เดียวคือผูก 7-phase spine
> เข้ากับ canonical skills ที่แข็งแรงที่สุดในด้าน design ถ้าต้อง *อธิบายวิธีทำ*
> แปลว่ามันควรเป็น canonical skill ไม่ใช่ pack
>
> **ทำไมมี**: `a-web` ส่ง DESIGN phase ไป `frontend-design` (43 บรรทัด) + design-system
> (83 บรรทัด) — ตัวอ่อนที่สุด ในขณะที่ `ui-ux-pro-max` (690 บรรทัด + 15 CSV) +
> `taste-skill` (87KB anti-slop) ถูกข้ามไป. Pack นี้เป็น "design spine" ที่ route ไป
> ตัวจริง + เพิ่ม composition/gate layer (inspired by StyleSeed MIT)

## เมื่อไหร่ใช้

✅ ใช้:
- ออกแบบ UI ใหม่ (web/mobile/dashboard) ตั้งแต่ต้น
- ทำ design system / token architecture
- Review UI ว่า "ดู AI-generated ไหม" (Distinctiveness gate)
- เลือก palette/font/style ตามประเภท product
- วาง motion/animation ที่ production-safe

❌ ข้าม:
- แค่เปลี่ยนสี/spacing เดียว → `ui-ux-pro-max` ตรงๆ
- แค่ implement frontend มี design ครบ → `/A-Web`
- bug frontend → `/A-Debug`
- งาน content/copy → `/A-Content`

## Iron Law

> **`focus_set` ก่อนเริ่มเสมอ** — pack ครอบทั้ง chain

```
focus_set({"skill": "a-design", "goal": "<done criteria>", "phase": "design"})
```

## Composition layer (inspired by StyleSeed — MIT, bitjaru/styleseed)

ก่อนเริ่มออกแบบ ตัดสินใจ **4 แกน** (composition ไม่ใช่ fixed aesthetic):

| แกน | คำถาม | ตัวอย่างค่า |
|---|---|---|
| **Output Grammar** | หน้านี้ทำหน้าที่อะไร? attention model ยังไง? | consumer-service · operations-console · technical-instrument · editorial-reading · commerce-conversion · institutional-service · expressive-marketing · sequential-story |
| **Brand Recipe** | shape language อะไร? | calm-consumer · native-mobile · enterprise-workbench · developer-platform · commerce-operator · public-service · creative-professional · editorial-authority · expressive-brand |
| **Surface Adapter** | output เป็นอะไน? | product-ui · social-carousel · deck · document · graphic |
| **Style Profile** (optional) | aesthetic adjustment เฉพาะ? | minimal · bold · brutalist · glassmorphic · bento |

> ดู 8 grammars + 9 recipes เต็ม: `references/composition-grammars.md`
> Authority order (resolve conflict): core → grammar → adapter → domain/page → recipe → profile → lock → craft

## Quality Gate (Distinctiveness — กัน "ดู AI-generated")

หลังออกแบบเสร็จ ตรวจด้วย **8-category rubric** (inspired by StyleSeed Quality Gate):

| Category | Max | ตรวจอะไร |
|---|---|---|
| Hierarchy | 15 | focal point ชัด? visual weight สมดุล? |
| Typography | 15 | modular scale? line-height? font pairing ทำงาน? |
| Color | 15 | WCAG contrast? semantic tokens? ไม่ใช่ AI-purple default? |
| Composition | 15 | grid/alignment? density เหมาะกับ grammar? |
| Motion | 10 | duration/easing? prefers-reduced-motion? ไม่ GC-churn? |
| Accessibility | 15 | WCAG 2.2 AA? touch target 44pt+? focus states? |
| **Distinctiveness** | 10 | **icon-chip cliché? all-even grid? escape-hatch-as-new-uniform? ghost 01/02/03?** |
| Craft | 5 | number ratio 2:1? refined black #2A2A2A? low-opacity shadow? |

> **Threshold: ≥80/100 ถึงจะ ship**. <80 → กลับไปแก้ในหมวดที่ fail
> ดู rubric เต็ม: `references/quality-gate.md`

## Phase → skill

| Phase | ใช้ | ทำอะไร |
|-------|-----|--------|
| ASK | `a-think` · `grill-with-docs` | นิยาม job-to-be-done + audience + done-criteria |
| **DESIGN** | **`ui-ux-pro-max`** (data: 161 palettes, 74 fonts, 99 rules) · **`taste-skill`** (anti-slop methodology) · use ui-ux-pro-max `--design-system` flag for tokens | เลือก grammar→recipe→tokens, กัน AI-slop defaults |
| PLAN | `a-plan` | แตกเป็น slice (token → component → page) |
| IMPLEMENT | `transitions-dev` (21 CSS transitions) · `motion-foundations` + `motion-patterns` + `motion-advanced` (React motion system) | สร้างจริง |
| REVIEW | **Quality Gate (8-cat rubric)** + `accessibility` (WCAG 2.2 AA) · `a-council` | ตรวจ hierarchy + a11y + distinctiveness |
| DEBUG | `a-debug` | repro → root cause |
| TEST | `e2e-testing` + `browser-qa` + reduced-motion test | smoke + a11y automated |

> เดิน phase ด้วย `focus_advance` · จบงาน `focus_clear`
> สำหรับ mobile: เพิ่ม `ui-ux-pro-max --stack {swiftui|flutter|react-native|jetpack-compose}` + ใช้ pre-delivery checklist (`ui-ux-pro-max/references/pro-rules.md`)

## Rationalization table

| ข้ออ้าง | คำตอบโต้ |
|---|---|
| "ใช้ frontend-design ตรงๆ ก็ได้" | ไม่ — `frontend-design` 43 บรรทัด, mindset ลอยๆ; `ui-ux-pro-max` + `taste-skill` แข็งกว่า 10 เท่า |
| "design-system skill ก็พอ" | ไม่ — 83 บรรทัด bullet principles; ใช้ `ui-ux-pro-max --design-system` แทน (มี data จริง) |
| "ไม่ต้อง Quality Gate ก่อน ship" | ผิด — ต่ำกว่า 80 = มี AI-tell หรือ a11y พัง; ship แล้ว user เห็น "ดู AI-generated" ทันที |
| "composition 4 แกน ยุ่งยาก" | ไม่ — กัน fixed aesthetic; หน้า dashboard ≠ หน้า landing ต้องใช้ grammar ต่างกัน |
| "Distinctiveness คืออะไร" | หมวดที่ตรวจ "ดู AI-generated ไหม" — icon-chip cliché, all-even grid, ghost 01/02/03, escape-hatch-as-new-uniform (เลียนแบบ style ใหม่จนกลายเป็น default ซ้ำ) |

## Patterns borrowed (MIT, credited)

- **StyleSeed** (bitjaru/styleseed, MIT 2026) — composition layer (grammar × recipe × adapter × profile), Quality Gate 0-100 with Distinctiveness category, authority-order conflict resolution
- **ui-ux-pro-max** (nextlevelbuilder, MIT 2025) — already vendored at `skills/ui-ux-pro-max/`; data layer (CSV-backed) + design dials + WCAG luminance coherence
- **taste-skill** (Leonxlnx, MIT) — already vendored at `skills/taste-skill/`; anti-AI-slop rules (Lila Rule, Premium-Consumer Palette Ban, Serif Discipline)

## Invocation

```
/A-Design "<งาน>"
```
