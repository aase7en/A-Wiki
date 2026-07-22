# ADR-0011: Dashboard v19 — Lucide Icons inline SVG sprite

**Status**: proposed
**Date**: 2026-07-22
**Context**: v18 palette uses emojis + geometric shapes (◆●◇)

## Context

หลัง v18 เสร็จ user ให้ feedback ว่า emoji ดูไม่มืออาชีพ — เหมือน "AI ล้าหลังออกแบบ". ตรวจจริงพบ:
- **102 unique emojis, 578 occurrences** ทั่ว dashboard
- แสดงผลไม่เท่ากัน Apple/Windows/Android (Apple สดใส, Android ซีด)
- ไม่สามารถ stroke-width / weight adjustment
- ไม่ scale แบบ vector (crispness ต่างกันตาม resolution)

User ถามถึง:
1. **three.js / Hyperframe** — เป็น 3D/WebGL +200KB → overkill สำหรับ icon 24px
2. **Canva MCP** — ไม่มี MCP production-ready; Canva เป็น design export ไม่ใช่ icon workflow
3. **AI image gen** — AI ไม่เก่ง icon (รอบ 24px SVG crispness); เก่ง illustration/hero

## Decision

**Lucide Icons via inline SVG sprite** (ไม่ใช่ CDN ไม่ใช่ font)

### Why Lucide (ไม่ใช่ Tabler/Phosphor/FontAwesome)
| Option | Pros | Cons | Score |
|--------|------|------|-------|
| **Lucide** ⭐ | MIT, 1500+ icons, feather-icons successor, shadcn/Linear/Vercel ใช้ | path-only (no fill) | **9/10** |
| Tabler | 4000+ icons, 2 weights | +50% larger sprite, less aesthetic cohesion | 8/10 |
| Phosphor | 6 weights (thin→fill) | 6× sprite size, ซับซ้อน | 7/10 |
| FontAwesome | แบบ classic | requires font file (50KB+), ไม่ colorable via currentColor | 5/10 |
| Heroicons | Tailwind-blessed | 300 icons น้อยไป | 6/10 |

Lucide = best balance ของ aesthetic + size + ecosystem

### Why SVG sprite `<symbol>` + `<use>` (ไม่ใช่ inline path)
- **Single source of truth**: sprite 1 ที่ → update 1 ครั้ง = กระจายทั้งระบบ
- **Tiny**: ใช้ `<use href="#icon-X">` = 50 bytes/call vs inline path 250 bytes/call
- **Cacheable**: sprite อยู่ใน HTML → render ทันที ไม่มี FOUC (flash of unstyled content)
- **Theme-able**: `<use>` อ้าง currentColor → theme switch ปรับทันที
- Standard pattern: shadcn/ui, GitHub, Vercel, Linear ใช้แบบนี้ทั้งนั้น

### Why NOT CDN (lucide.dev)
- **Latency**: +1 RTT ต่อ page load
- **Privacy**: leak IP + referer to CDN
- **Reliability**: CDN down = icon หาย (Iron Law #5 config protection)
- **Iron Law #5**: dashboard ต้อง offline-capable

### Why NOT three.js / Hyperframe (สำหรับ icon)
- **Overkill**: 3D engine 200KB+ สำหรับ icon 24×24px = ไร้สาระ
- **GPU cost**: WebGL context กิน memory + battery
- **Bundle**: +200KB เกิน budget (260KB hard cap)
- **Use case ผิด**: three.js เหมาะ Flow particle bg (v20) ไม่ใช่ icon

### Why NOT Canva MCP
- **ไม่มี MCP production-ready** สำหรับ Canva (verified 2026-07)
- Canva API เป็น design-export (ต้องออกแบบ manual ใน Canva ก่อน) ไม่ใช่ programmatic icon generation
- Workflow ที่ใช้ได้: ออกแบบ brand mark ใน Canva → export SVG → commit ใน repo (FR-7)

## Constraints

- **Bundle**: app.min.js ≤ 260 KB (sprite ~7KB + ตัว icon() ~0.5KB = within budget)
- **Legacy**: themes ใช้ได้ครบ (currentColor auto-adjusts)
- **A11y**: aria-label สำหรับ icon-only buttons; aria-hidden สำหรับ decorative
- **Tests**: 141 existing + ≥ 6 new = ≥ 147 pass

## Glossary

| Term | Definition |
|------|-----------|
| **SVG sprite** | `<svg style="display:none"><symbol id="icon-X">...</symbol>...</svg>` hidden ใน DOM — เรียกใช้ผ่าน `<use href="#icon-X">` |
| **`<symbol>` vs `<defs>`** | symbol มี viewBox ของตัวเอง → scalable; defs ใช้สำหรับ gradients/filters |
| **currentColor** | CSS keyword ที่ inherit color จาก parent — icon stroke ปรับตาม text color อัตโนมัติ |
| **Lucide** | open-source icon library (fork ของ Feather Icons) 1500+ icons MIT — ใช้โดย shadcn/ui, Vercel, Linear |
| **Icon font** | เช่น FontAwesome — ใช้ `content: '\e001'` ใน CSS. Cons: กิน font file 50KB+, ไม่ colorable แบบ fine-grained, มี ligature hack |
| **AI icon gen** | AI สร้าง raster (PNG/JPG) ไม่ใช่ vector; ไม่ crisp ที่ 24px; ไม่แนะนำสำหรับ UI icon |

## Alternatives considered และทำไมไม่เลือก

| Alt | ทำไมไม่เลือก |
|-----|---------|
| Emoji เดิม | ดูไม่มืออาชีพ + inconsistent cross-OS (user feedback) |
| Tabler Icons | 4000+ icons เยอะเกินไป → sprite ใหญ่ โดยไม่จำเป็น |
| Phosphor | 6 weights ซับซ้อน → เลือก weight ผิดง่าย |
| FontAwesome / Material Icons | Font-based → กิน network + ไม่ flexible |
| three.js / WebGL | Overkill 200KB+ สำหรับ icon |
| Canva MCP | ไม่มี MCP production-ready |
| AI imagegen | AI ไม่เก่ง icon (raster ไม่ใช่ vector); ใช้สำหรับ hero/brand เท่านั้น (FR-7) |
| Hand-drawn SVG | ใช้เวลานาน ไม่ maintainable |
