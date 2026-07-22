# ADR-0010: Dashboard v18 — Cmd+K palette + Polish 2 จุด

**Status**: proposed
**Date**: 2026-07-22
**Context**: A-Wiki Dashboard v17 (Pure Minimal redesign, design score 8.4/10)

## Context

v17 ปิด slop patterns ครบ (gradient/glass/teal-rgba) แต่เหลือ backlog 3 จุด บวก feature wishlist จาก user ที่ใช้ dashboard ทุกวัน:

**Backlog (from D17 commit + session-memory):**
1. 9/12 emoji-prefix headings ใน JS-rendered panels (coverage/analytics)
2. inline-style padding ใน HTML (87 border-radius count ส่วนใหญ์มาจาก inline)
3. transition count 30 ที่ยังไม่ได้ใช้ `--t-fast/normal/slow` token ทั้งหมด

**Feature wishlist:**
- Cmd+K command palette (jump view / search skill / run command)
- PWA offline (service worker)
- palette expansion
- subagent drill-down (fan-out tree)
- cost-projection What-if

## Decision

**A4 Mixed** approach: Polish 2 จุด + Cmd+K palette.

### Why mixed (not polish-only or feature-only)
- Polish-only (A1): user เบื่อเพราะไม่มี feature ใหม่ — polish คนเดียวไม่สร้าง excitement
- Feature-only: backlog ค้าง → design score ไม่ถึง 9.3+
- Mixed: ได้ทั้ง design score + DX ที่ user ใช้จริงทุกวัน

### Why Cmd+K (not PWA)
- **Usage frequency**: user เปิด dashboard ทุก session → Cmd+K ใช้ทุกครั้ง vs PWA ใช้ตอนเน็ตหลุด (นานๆ ครั้ง)
- **Effort**: Cmd+K ~4 chunks vs PWA ~6 chunks (service worker + cache invalidation)
- **Linear/Vercel/Stripe parity**: ทุก minimal app มี Cmd+K — it's the hallmark of modern UX

### Runtime discovery (2026-07-22)
ตรวจ runtime จริงก่อนเขียน spec พบว่า:
- **Cmd+K ถูก wire แล้ว** (modals.js:465 ตั้งแต่ CHUNK EE)
- **Palette DOM ครบ** (palette-backdrop, palette-modal, palette-input)
- **ทำงานได้**: กด Ctrl+k → palette โผล่ + 10 rows + input focused
- **fuzzy search + arrow nav + Enter**: ครบ

ดังนั้น v18 scope เปลี่ยนจาก "เพิ่ม Cmd+K" → **"อัปเกรด Cmd+K ให้ minimal + discoverable + smart"**:
1. **Visual minimal**: palette-row ใช้ emojis (🧩🌊📊⌨️) → เปลี่ยนเป็น dot indicator สไตล์ Linear
2. **Discoverability**: ไม่มี hint ว่า Cmd+K อยู่ → เพิ่ม hint badge "⌘K" ใน header
3. **Smart ranking**: ปัจจุบัน alphabetical/fuzzy score → เพิ่ม recency weighting (เหมือน Linear)
4. **Recent commands**: ยังไม่มี → เพิ่ม last 5 used commands at top
5. **CSS minimal**: palette-modal ยังมี `backdrop-filter:blur(3px)` (slop) → flat

### Why polish 2 จุด (not all 3)
- 2 จุด high-impact: emoji-headings (visual) + transition tokens (motion)
- inline-style padding ต้อง refactor HTML ทั้งหมด → risk สูง → ทิ้งไว้ v19+
- Iron Law #1: failing test ก่อนทุก chunk

## Constraints (binding)

| Constraint | Value | Source |
|------------|-------|--------|
| Legacy themes | dark/light/green-white ต้องใช้ได้ | user |
| Existing tests | 134 tests ต้องผ่านต่อ | user |
| Iron Laws | ทุกข้อ โดยเฉพาะ #1 (failing test first) | AGENTS.md |
| Bundle size | app.min.js ≤ 250 KB (ปัจจุบัน 219.6 KB, เหลือ 30 KB) | user |

## Success criteria

- **Visual audit**: design score 8.4 → **9.3+** (10-dimension)
- **Runtime**: 0 console errors (Playwright runtime_audit.py)
- **Feature**: กด Cmd+K (หรือ Ctrl+K) → palette โผล่ → พิมพ์ → เลือก → ใช้งานได้ใน 1 keystroke
- **Tests**: ทุก chunk มี failing test ก่อน + pass หลังแก้

## Glossary

| Term | Definition |
|------|-----------|
| **Cmd+K palette** | Command palette overlay (เหมือน Linear/Vercel/Stripe/Raycast) ที่ popup ตอนกด Cmd+K หรือ Ctrl+K — มี search box + arrow navigation + Enter เพื่อ execute |
| **`_paletteIndex`** | Existing array (src/modals.js CHUNK EE) เก็บ skill/view/shortcut items สำหรับ palette — ต้อง wire เข้า Cmd+K |
| **Emoji-prefix heading** | Heading ที่ขึ้นต้นด้วย emoji เช่น `📡 รอ Dashboard` — DESIGN.md v17 ตัดออกเพราะ noise |
| **Transition token** | `--t-fast/normal/slow` CSS vars ที่ v17 นิยามไว้ แต่ rules เก่ายังใช้ `.2s ease-out` กระจัดกระจาย |
| **Design score** | Visual audit 10-dimension score จาก design-system skill (Color/Typography/Spacing/Component/Responsive/Dark/Animation/A11y/Density/Polish) |
| **Polish chunk** | Chunk ที่ไม่เพิ่ม feature แต่ยกระดับ quality ของสิ่งที่มี |

## Alternatives considered

| Alt | ทำไมไม่เลือก |
|-----|---------|
| **A1 Polish-only** | ไม่มี feature ใหม่ user เบื่อ |
| **A3 PWA** | effort สูง + ใช้น้อย (เน็ตหลุด นานๆ ครั้ง) |
| **A2 Cmd+K เต็ม** | backlog ค้าง design score ไม่ถึง 9.3+ |
| **Performance/bundle** | ไม่จำเป็นตอนนี้ — dashboard โหลด <2s แล้ว |
