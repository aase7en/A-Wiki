# A-Wiki Dashboard — Design System (v17)

> **Direction**: Pure Minimal · Linear-style · Neutral + Accent
> **Audit**: 5/10 (v16) → target **9/10** (v17)
> **Generated**: 2026-07-21 by `design-system` skill

---

## 🎯 Design Principles

1. **Content first** — ตัวเลข/ข้อความเด่น ไม่ใช่ gradient/decoration
2. **One accent** — ทุก interactive primary state ใช้สีเดียว (`--brand`)
3. **Borders over shadows** — card ใช้ 1px border บาง ไม่ใช้ box-shadow (ยกเว้น modal/popover)
4. **Whitespace > density** — section gap 24px, row pad 10px, ไม่เบียดกัน
5. **Motion = communication** — 3 transitions ระดับ fast/normal/slow ตาม intent
6. **Type as hierarchy** — 6 font sizes + 4 weights กำหนด order ชัดเจน

---

## 🎨 Color

### Neutral scale (Linear-style 11 steps)

| Token | Hex | Use |
|-------|-----|-----|
| `--n-0` | `#000000` | text สีดำ (light mode) |
| `--n-50` | `#0a0a0c` | app bg (dark default) |
| `--n-100` | `#121215` | surface 1 — sidebar/panels |
| `--n-200` | `#1a1a1f` | surface 2 — cards |
| `--n-300` | `#27272e` | surface 3 — hover/elevated |
| `--n-400` | `#3f3f47` | border strong |
| `--n-500` | `#52525b` | border default |
| `--n-600` | `#71717a` | text muted |
| `--n-700` | `#a1a1aa` | text secondary |
| `--n-800` | `#d4d4d8` | text primary (dark) |
| `--n-900` | `#fafafa` | text inverted |
| `--n-1000` | `#ffffff` | white |

### Accent (single hue — Linear violet)

| Token | Value | Use |
|-------|-------|-----|
| `--brand` | `#5b5bd6` | primary buttons, active tab, focus ring |
| `--brand-hover` | `#6d6dff` | hover state |
| `--brand-muted` | `rgba(91,91,214,.12)` | selected row tint, hover bg |
| `--brand-fg` | `#ffffff` | text on brand |

### Status (no gradients)

| Token | Hex | Use only |
|-------|-----|----------|
| `--success` | `#10b981` | success badge, online dot |
| `--warn` | `#f59e0b` | warn badge |
| `--danger` | `#ef4444` | error badge, destructive |
| `--info` | `#3b82f6` | info tooltip |

---

## 🔤 Typography

Fluid `clamp()` scale — **6 sizes** (was 8).

| Token | Size | Use |
|-------|------|-----|
| `--fs-caption` | `clamp(11px,1.1vw,12px)` | metadata, timestamps |
| `--fs-body` | `clamp(13px,1.4vw,14px)` | body — default |
| `--fs-h4` | `clamp(15px,1.8vw,16px)` | card titles, section labels |
| `--fs-h3` | `clamp(17px,2vw,18px)` | panel sub-titles |
| `--fs-h2` | `clamp(20px,2.5vw,22px)` | panel titles |
| `--fs-h1` | `clamp(24px,3vw,28px)` | page titles (rare) |

Font stack: `-apple-system, BlinkMacSystemFont, 'Inter var', 'Segoe UI', system-ui`
- ใช้ system font เป็นหลัก (zero network cost)
- Inter เป็น fallback (popular minimal pairing with Linear)
- **no emoji prefix** on headings — replaced with subtle dot `•` or removed

Font weights: 400 / **500 default body** / 600 headings/buttons / 700 rare emphasis

---

## 📏 Spacing

4px base — 11 steps (was arbitrary). No 7px/13px.

| Token | Value |
|-------|-------|
| `--s-1` | `2px` |
| `--s-2` | `4px` |
| `--s-3` | `6px` |
| `--s-4` | `8px` |
| `--s-5` | `12px` |
| `--s-6` | `16px` (card pad) |
| `--s-7` | `20px` |
| `--s-8` | `24px` (section gap) |
| `--s-10` | `32px` |
| `--s-12` | `48px` |

---

## 📐 Radius

**2 values only** (was 4):

| Token | Value | Use |
|-------|-------|-----|
| `--r-sm` | `6px` | buttons, inputs, badges |
| `--r-md` | `10px` | cards, panels, modals |

---

## 🌑 Shadow

**4 shadows** (was 32). Cards use **border-only** — no shadow.

| Token | Value | Use |
|-------|-------|-----|
| `--shadow-none` | `none` | cards default |
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,.06)` | hover |
| `--shadow-md` | `0 4px 12px rgba(0,0,0,.08)` | popover/dropdown |
| `--shadow-lg` | `0 16px 40px rgba(0,0,0,.12)` | modal |

---

## ⚡ Motion

3 transitions (was 30), single easing curve:

```css
--ease: cubic-bezier(0.2, 0, 0, 1);
--t-fast: 120ms var(--ease);    /* hover, focus */
--t-normal: 200ms var(--ease);  /* toggle, expand */
--t-slow: 320ms var(--ease);    /* modal, view switch */
```

**Removed**: bouncy easings, parallax, particle spins (kept particle bg in Flow view only — that's content).

---

## 🚫 Slop Patterns Removed (audit findings)

| Was | Now | Rationale |
|-----|-----|-----------|
| 20 `linear-gradient` | 0 decorative | gradient = AI-tell; flat color communicates clearly |
| 7 `backdrop-filter:blur` (glass) | 1 (modal only) | glass on cards = no hierarchy; modal needs separation |
| 32 `box-shadow` | 4 | shadows everywhere = nothing stands out |
| 30 transitions | 3 | bouncy easings = unprofessional |
| emoji-prefix headings (12/12) | removed or subtle `•` | emoji = noise; type should lead |
| 8 font sizes | 6 | tighter hierarchy |
| 4 radii | 2 | consistency |

---

## 📐 Component Patterns

### Button
```css
.btn {
  background: var(--n-200);
  color: var(--n-800);
  border: 1px solid var(--n-500);
  padding: 8px 14px;
  border-radius: var(--r-sm);
  font-weight: 500;
  transition: var(--t-fast);
}
.btn:hover { background: var(--n-300); }
.btn-primary {
  background: var(--brand);
  color: var(--brand-fg);
  border-color: transparent;
}
.btn-primary:hover { background: var(--brand-hover); }
```

### Card
```css
.card {
  background: var(--n-100);
  border: 1px solid var(--n-400);
  border-radius: var(--r-md);
  padding: var(--s-6);
  /* no shadow, no glass, no gradient */
}
.card:hover {
  border-color: var(--n-500);
  box-shadow: var(--shadow-sm);
}
```

### Tab (active)
```css
.tab { color: var(--n-700); }
.tab:hover { color: var(--n-800); background: var(--n-300); }
.tab.active {
  color: var(--n-900);
  background: var(--brand-muted);
  border-bottom: 2px solid var(--brand);
  /* no gradient, no box-shadow glow */
}
```

### Heading
```css
h2 { font-size: var(--fs-h2); font-weight: 600; color: var(--n-900); }
/* no background-clip:text gradient, no emoji prefix */
```

---

## 🌗 Theme Variants

| Mode | Background | Surface | Text |
|------|-----------|---------|------|
| **dark (default)** | `--n-50` | `--n-100`/`--n-200` | `--n-800` |
| light | `--n-900` | `--n-1000`/`--n-900` | `--n-100` |

Both use same accent (`--brand`). No "green-white" variant — that was emerald-palette specific. Replaced with neutral+accent.

---

## 📊 Audit Score Target

| Dimension | v16 | v17 target | How |
|-----------|-----|------------|-----|
| Color consistency | 6 | **9** | single accent, no decorative gradients |
| Typography | 8 | **9** | 6 sizes, no emoji headings |
| Spacing | 7 | **9** | strict 4px scale |
| Component consistency | 5 | **9** | unified .card/.btn patterns |
| Responsive | 7 | **8** | clamp() kept |
| Dark mode | 6 | **9** | dark is default |
| Animation | 5 | **9** | 3 transitions only |
| Accessibility | 7 | **9** | contrast up (no glass blur) |
| Density | 5 | **8** | section gaps enforced |
| Polish | 6 | **9** | unified hover/focus |
| **Average** | **6.0** | **8.8** | |
