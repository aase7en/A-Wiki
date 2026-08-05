# Composition Grammars — 8 output grammars × 9 brand recipes

> Adapted from StyleSeed (bitjaru/styleseed, MIT 2026). Re-implemented to A-Wiki
> conventions — no JS compiler dependency, agent reads this as decision table.

## Why grammars (not "styles")

"Style" (minimalism, glassmorphism) เป็น **aesthetic** — บอกว่าหน้านี้ "ดูยังไง"
แต่ไม่ได้บอกว่าหน้านี้ **ทำหน้าที่อะไร**. Grammar แก้ปัญหานี้:

> **Output grammar = job-to-be-done → attention/composition contract**

หน้า dashboard กับหน้า landing ใช้ grammar ต่างกัน ถึงแม้จะ "style" เดียวกัน

## 8 Output Grammars

| Grammar | ใช้เมื่อ | Attention model | Reference family |
|---|---|---|---|
| **`consumer-service`** | fintech, health, benefits, onboarding | reassurance + next useful action | Toss, Wise, Chime |
| **`operations-console`** | B2B SaaS, admin, analytics | scan + compare + act | Stripe, Shopify, Polar, Mixpanel |
| **`technical-instrument`** | observability, infrastructure, monitoring | live state + diagnosis | Sentry, Better Stack, LogRocket |
| **`editorial-reading`** | journalism, reports, long-form | comprehension + reading rhythm | FT, Boston Globe, USWDS content |
| **`commerce-conversion`** | e-commerce, marketplace | trust + product evaluation + checkout | Shopify stores, Allbirds |
| **`institutional-service`** | government, regulated forms, healthcare portal | certainty + accessibility + completion | GOV.UK, USWDS |
| **`expressive-marketing`** | landing pages, brand campaigns | hook + emotion + CTA | Awwwards, premium brand sites |
| **`sequential-story`** | social carousels, visual explainers, decks | hook + progression + retention | editorial carousel systems |

### 12-axis contract ของแต่ละ grammar

ทุก grammar กำหนด 12 แกน (agent ตัดสินใจครบทุกแกน ไม่ใช่เลือกแค่สี):

1. **User job** — ผู้ใช้มาทำอะไร?
2. **Attention model** — สายตาไปที่ไหนก่อน? (F-pattern, Z-pattern, focal-point, scan-and-compare)
3. **Composition** — grid type (12-col, bento, asymmetric, single-column)
4. **Density** — spacious/balanced/dense (mapping ไป spacing scale)
5. **Typography** — scale ratio (minor 3:2, major 4:5, golden), body size range
6. **Color** — semantic palette (bg/fg/card/border/accent/destructive)
7. **Surfaces** — card/elevation/radius strategy
8. **Imagery & data** — illustration vs photo vs chart vs none
9. **Navigation & action** — top-nav/bottom-nav/sidebar/tabs/floating-action
10. **States & motion** — duration/easing presets, loading patterns
11. **Responsive** — breakpoints, mobile-first vs desktop-first
12. **Tells & anti-patterns** — อะไรที่ grammar นี้ห้ามทำเด็ดขาด

## 9 Brand Recipes (shape language morphology)

Recipe คือ **กฎรูปทรง** (radius, border, elevation, containment, control shape) — ไม่ใช่ "สีของแบรนด์"

| Recipe | Radius | Border | Elevation | Containment | Use for |
|---|---|---|---|---|---|
| **`calm-consumer`** | 12-16px | 1px subtle | low, soft shadow | card-based | consumer fintech, health |
| **`native-mobile`** | platform default | hairline | none (platform) | full-bleed sections | iOS/Android apps |
| **`enterprise-workbench`** | 4-8px | 1px solid | medium | dense tables, panels | admin, B2B SaaS |
| **`developer-platform`** | 6-8px | 1px, mono accents | low | code blocks, terminals | dev tools, docs |
| **`commerce-operator`** | 8-12px | 1px | medium | product cards, grids | e-commerce |
| **`public-service`** | 0-4px | 2px solid | none | high-contrast panels | government, regulated |
| **`creative-professional`** | mixed | experimental | bold | asymmetric | portfolio, agency |
| **`editorial-authority`** | 0 | rules, column-based | none | typographic columns | journalism, reports |
| **`expressive-brand`** | varies | bold | dramatic | full-bleed hero | brand campaigns |

### Anti-cloning boundary (critical)

> **"Build at least one screen not shown in the references."**
> Recipe ไม่ใช่ clone ของ Stripe/Linear/Vercel — มันคือ shape language ที่ implement
> จริง. ถ้า output ก๊อปปี้ layout ของ reference ทั้งหมด → grammar failed abstraction.

## Authority order (resolve conflicts)

เมื่อ grammar กับ recipe ขัดแย้งกัน (เช่น grammar บอก "dense" แต่ recipe บอก "spacious"):

```
core (a11y, contrast)  >  grammar  >  adapter  >  domain/page
                                                ↓
                                              recipe  >  profile  >  lock  >  craft
```

**A11y always wins.** ถ้า recipe สั่ง radius 0 แตะ target 44pt ต้องการ padding ก็ตาม
padding ชนะ (a11y non-negotiable).

## How to use (agent workflow)

1. อ่าน user brief → เลือก **grammar** ตาม "หน้านี้ทำอะไร"
2. เลือก **recipe** ตาม shape language ที่ product อยากจะ (ดู brand, audience)
3. เลือก **adapter** (product-ui / social / deck / doc / graphic)
4. (optional) เลือก **profile** (minimal/bold/brutalist) ถ้า aesthetic สำคัญ
5. Resolve conflict ตาม authority order
6. Output = 12-axis decision (ไม่ใช่แค่ palette + font)
7. บันทึก decision ลง `.design/MASTER.md` ของ project

## ตัวอย่าง

**"ออกแบบหน้า dashboard สำหรับ fintech app"**
- Grammar: `operations-console` (scan + compare + act)
- Recipe: `calm-consumer` (fintech → reassurance)
- Adapter: `product-ui`
- 12-axis output: dense grid, 8px radius, semantic palette with trust colors,
  focal-point attention on KPI cards, scan-and-compare layout, 200ms motion

**"ออกแบบ landing page campaign สำหรับแบรนด์ใหม่"**
- Grammar: `expressive-marketing` (hook + emotion + CTA)
- Recipe: `expressive-brand` (dramatic, full-bleed)
- Adapter: `product-ui` (web)
- Profile: `bold` (เพิ่ม aesthetic layer)
- 12-axis output: asymmetric grid, mixed radius, bold elevation, single CTA
