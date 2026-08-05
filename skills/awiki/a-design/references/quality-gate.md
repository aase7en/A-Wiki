# Quality Gate — 8-category rubric (Distinctiveness focus)

> Adapted from StyleSeed Quality Gate (bitjaru/styleseed, MIT 2026).
> Threshold: **≥80/100 ถึงจะ ship**. <80 → กลับไปแก้ในหมวดที่ fail.

## ทำไมต้อง Gate

"ผ่าน review ลายตา" ไม่พอ — AI generate UI ที่ "ดูใช้ได้" แต่มี AI-tell ซ่อนอยู่.
Gate บังคับให้ตรวจทุกหมวดเป็นระบบ ก่อนเสร็จงาน.

## 8 Categories (รวม 100 คะแนน)

### 1. Hierarchy (15) — focal point + visual weight

**ผ่าน (15)**:
- มี focal point ชัด 1 จุดต่อหน้า (hero KPI / hero image / headline)
- visual weight ลำดับได้: primary > secondary > tertiary > quaternary
- contrast ระหว่าง level ≥ 2 ระดับ (size OR color OR weight)

**หักคะแนน**:
- ไม่มี focal point (-5) — ทุกอย่างน้ำหนักเท่ากัน
- หน้า dashboard ทุกการ์ดเท่ากัน (-3) — ไม่มี KPI เด่น
- hierarchy ใช้แค่ color ไม่ใช้ size/weight (-2)

### 2. Typography (15) — modular scale + pairing

**ผ่าน (15)**:
- modular scale ratio ชัดเจน (minor 3:2, major 4:5, golden 1.618)
- line-height body 1.4-1.6, heading 1.0-1.2
- font pairing ทำงาน (contrast personality ไม่ใช่คล้ายกัน)
- `next/font` / `font-display: swap` สำหรับ web fonts

**หักคะแนน**:
- ไม่มี scale (size สุ่ม) (-5)
- Inter/Roboto/Arial เป็น default (-3) — ใช้ taste-skill ตรวจ
- serif default โดยไม่จำเป็น (-3) — taste-skill "Serif Discipline"
- ไม่มี `font-display: swap` (-2)

### 3. Color (15) — WCAG + semantic + anti-AI-purple

**ผ่าน (15)**:
- contrast ผ่าน WCAG AA (4.5:1 body, 3:1 large)
- semantic tokens (bg/fg/card/border/accent/destructive ไม่ใช่ ad-hoc hex)
- dark mode contrast ตรวจอิสระ (ไม่ assume จาก light mode)
- refined black (#2A2A2A, ไม่ใช่ #000) สำหรับ body text

**หักคะแนน**:
- AI-purple default (#6366F1 / #8B5CF6 โดยไม่คิด) (-5) — taste-skill "Lila Rule"
- Premium-consumer palette (warm-beige + brass + espresso) (-4)
- contrast ไม่ผ่าน WCAG (-5, critical)
- ใช้ #000 body text (-2) — หนักไป

### 4. Composition (15) — grid + density + alignment

**ผ่าน (15)**:
- grid system ชัด (12-col, bento, asymmetric — เลือกตาม grammar)
- alignment สม่ำเสมอ (ไม่มี off-by-1px drift)
- density เหมาะกับ grammar (consumer-service ≠ operations-console)
- whitespace เป็น design element ไม่ใช่ "ที่ว่าง"

**หักคะแนน**:
- ไม่มี grid (-5)
- alignment drift (-3)
- density ผิด grammar (landing แน่นเกิน / dashboard ห่างเกิน) (-3)

### 5. Motion (10) — duration + easing + reduced-motion

**ผ่าน (10)**:
- duration tokens (instant 100ms / fast 150ms / normal 250ms / slow 400ms)
- easing presets (snappy/gentle/bouncy — ไม่ใช่ default `ease` ทุกที่)
- `prefers-reduced-motion` ทำงาน
- exit faster than enter (60-70% of enter duration)
- ไม่มี GC-churn (GSAP `quickTo` สำหรับ hover lists 20+ items)

**หักคะแนน**:
- ไม่มี reduced-motion (-5, critical)
- ทุกอย่างใช้ `ease` default (-2)
- exit ช้ากว่า enter (-2)
- bounce หลายเกิน (animate-bounce 5+ elements) (-3)

### 6. Accessibility (15) — WCAG 2.2 AA

**ผ่าน (15)**:
- touch target ≥ 44pt (iOS) / 48dp (Android)
- focus states ชัด (2px outline สีตัดกับ bg)
- focus trap ใน modal
- ARIA semantic (ไม่ใช่ div + onClick)
- color ไม่ได้เป็น state indicator เดียว (เพิ่ม icon/text)
- alt text สำหรับ image ที่มีข้อมูล

**หักคะแนน**:
- touch target เล็กกว่า 44pt (-5, critical)
- ไม่มี focus visible (-5, critical)
- ARIA ผิด (role mismatch) (-3)
- color-only state (-2)

### 7. Distinctiveness (10) — anti-AI-tell

> **หมวดนี้คือหัวใจ** — กัน output "ดู AI-generated"

**ผ่าน (10)**:
- ไม่มี icon-chip cliché (Lucide icon ใน tinted rounded-square เหมือนกันทุก feature)
- ไม่ใช่ all-even grid (การ์ดเท่ากันหมด ไม่มี focal)
- ไม่มี ghost 01/02/03 index numbers บนทุก section
- ไม่ copy StyleSeed/ui-ux-pro-max demo layout verbatim
- hero มี product-specific visual (ไม่ใช่ stock placeholder)
- "escape hatch as new uniform" — เลียนแบบ style ใหม่จนกลายเป็น default ซ้ำ

**หักคะแนน**:
- icon-chip cliché (-4) — Lucide ในทุก feature box
- demo layout copied verbatim (-4) — hero+chat / 3-step / feature-grid / pricing
- no focal point (all-even grid) (-3)
- stock/placeholder visual ใน hero (-3)
- ghost 01/02/03 ทุก section (-2)
- distinct-but-dated (trend ที่กำลังตาย) (-2)

### 8. Craft (5) — numerical details

**ผ่าน (5)**:
- number ratio 2:1 (metric 48px / unit 24px) — `DESIGN-LANGUAGE.md`
- refined black #2A2A2A ไม่ใช่ #000
- low-opacity shadows (rgba 0.04-0.08, ไม่ใช่ 0.5)
- single-accent law (1 accent color, semantic ที่เหลือ)
- eyebrow restraint (max 1 eyebrow per 3 sections)

**หักคะแนน**:
- number ratio ผิด (-1)
- #000 body (-1)
- heavy shadow (-1)
- multi-accent chaos (-1)
- eyebrow spam (-1)

## วิธีใช้

```python
# หลังออกแบบเสร็จ
score = {
    "hierarchy": 12,        # /15
    "typography": 13,       # /15
    "color": 14,            # /15
    "composition": 12,      # /15
    "motion": 8,            # /10
    "accessibility": 15,    # /15
    "distinctiveness": 7,   # /10
    "craft": 4,             # /5
}
total = sum(score.values())  # 85/100 → ผ่าน (≥80)

if total < 80:
    failing = [k for k, v in score.items() if v < max_for[k] * 0.7]
    print(f"BLOCK: แก้ {failing} ก่อน ship")
```

## Anti-evasion

- อย่า "ทำให้ผ่าน" โดยไม่คิด — ทุกหมวดต้องมี evidence (screenshot, code snippet, contrast ratio)
- ถ้าได้ 80-85 → likely ยังมี tells; กลับไปดู Distinctiveness อีกรอบ
- 95+ → น่าสงสัย (over-fit เกณฑ์ ไม่ใช่ design ดีจริง) — ขอคนที่ไม่เกี่ยวข้องรีวิว
