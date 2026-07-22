# Dashboard v19 — Spec: Lucide Icons + SVG Sprite

**Direction**: Lucide เต็มระบบ (svg sprite) + imagegen brand mark + three.js Flow particles (แยก v20)
**Date**: 2026-07-22
**Predecessor**: v18 (Cmd+K palette upgrade)
**Bundle budget**: app.min.js ≤ 260 KB (เพิ่มจาก 250 → 260 ให้พอสำหรับ sprite + three.js ถ้า v20)

---

## Functional Requirements

### FR-1: SVG sprite setup
- `FR-1.1`: เพิ่ม `<svg id="icon-sprite" style="display:none">` ใน live-dashboard.html มี `<symbol id="icon-X">` สำหรับแต่ละ icon
- `FR-1.2`: สร้าง helper `icon(name, opts)` ใน JS ที่ return `<svg class="icon"><use href="#icon-X"/></svg>` markup
- `FR-1.3`: CSS `.icon { width: 1em; height: 1em; stroke: currentColor; fill: none; stroke-width: 2 }` — scale ตาม font-size
- `FR-1.4`: ทุก symbol inherit `currentColor` (ปรับ theme อัตโนมัติ)
- **Acceptance**: 1 test — sprite มี ≥ 30 symbols + `icon()` helper exists

### FR-2: Header icon replacement (8 emojis)
- `FR-2.1`: ⚙️ → `settings`, 💾 → `save`, 🔔 → `bell`, 🗑 → `trash-2`, ⌘ → (text), 💡 → `lightbulb` (theme toggle)
- `FR-2.2`: ลบ emoji ทั้งหมดออกจาก `#header` buttons
- **Acceptance**: 1 test — header ไม่มี emoji ใน buttons

### FR-3: View-tabs icon replacement (13 emojis)
- `FR-3.1`: 📊 Summary → `layout-dashboard`, 🌊 Flow → `workflow`, 🏊 Timeline → `git-commit-horizontal`, 🔗 Graph → `share-2`, 🧩 Skills → `puzzle`, 📊 Coverage → `bar-chart-3`, 📈 Analytics → `trending-up`, 🔬 Subagents → `flask-conical`, 📊 Eval → `graduation-cap`, 💰 Cost → `dollar-sign`, 🏁 Race → `flag`, 💬 Chat → `message-circle`, 🏛️ Council → `users`
- **Acceptance**: 1 test — view-toggle-bar ไม่มี emoji

### FR-4: Workflow tabs (4 emojis)
- `FR-4.1`: 🚀 Session → `rocket`, 📋 Plan → `clipboard-list`, 🧠 Swarm → `brain`, 💰 Cost → `dollar-sign` (same as view)
- **Acceptance`: 1 test — wf-tabs ไม่มี emoji

### FR-5: Palette + skill-detail + chat avatar icons
- `FR-5.1`: Replace PALETTE_ICONS geometric shapes (◆ ● ◇) → Lucide (`puzzle`/`layout`/`keyboard`)
- `FR-5.2`: Skill-detail button icons (🔗 share, ✕ close)
- `FR-5.3`: Chat msg avatar (`🤖` Hermes → `bot`, `👤` user → `user`)
- **Acceptance`: 1 test — these 3 areas ไม่มี emoji

### FR-6: Status icons (system status / notif / events)
- `FR-6.1`: ✅ → `check-circle-2`, ❌ → `x-circle`, ⚠️ → `alert-triangle`, ℹ️ → `info`
- `FR-6.2`: spawnThought tones (green/red/gold/violet) ใช้ icon แทน emoji
- `FR-6.3`: Event timeline `evIcon(type)` returns `<svg class="icon">` markup แทน emoji
- **Acceptance`: 1 test — evIcon ไม่ return emoji

### FR-7: Brand mark (imagegen skill)
- `FR-7.1`: ใช้ `imagegen` skill สร้าง "A-Wiki" wordmark + logo mark (256×256 SVG or PNG)
- `FR-7.2`: แทน `<span class="brand">A-Wiki Live</span>` ด้วย `<img class="brand-mark">` + text
- **Acceptance`: brand mark committed to repo

---

## Non-Functional

- **NFR-1**: Bundle ≤ 260 KB (sprite +30 KB budget)
- **NFR-2**: Legacy themes ใช้ได้ครบ (icons inherit currentColor → auto-adjust)
- **NFR-3**: 141 existing tests + ≥ 6 new = ≥ 147 tests pass
- **NFR-4**: Runtime 0 console errors
- **NFR-5**: No new CDN/runtime dependency — sprite is inline SVG (zero network)
- **NFR-6**: WCAG AA — icons มี `aria-label` หรือ `aria-hidden` ตาม context

---

## Out of scope (v20+)

- three.js Flow particles
- Canva MCP integration (ถ้ามีจริง)
- Coverage/analytics panel emoji-headings (9 remaining)
- Inline-style padding refactor

---

## Chunk breakdown (8 chunks + verify)

| Chunk | Focus | Files | Tests added |
|-------|-------|-------|-------------|
| **A19** | SVG sprite setup + `icon()` helper | `live-dashboard.html`, `src/app.js` (or new `src/icons.js`), `styles.css` | 1 |
| **B19** | Header icon replacement (8 emojis) | `live-dashboard.html` | 1 |
| **C19** | View-tabs icon replacement (13 emojis) | `live-dashboard.html` | 1 |
| **D19** | Workflow tabs (4 emojis) | `live-dashboard.html`, `src/app.js` | 1 |
| **E19** | Palette icons (◆●◇ → Lucide) | `src/modals.js` | 1 |
| **F19** | Status/event icons (✅❌⚠️ + evIcon) | `src/graph.js` | 1 |
| **G19** | Skill-detail + chat avatars | `src/skills.js`, `src/chat.js` | 1 |
| **H19** | imagegen brand mark | new asset + `live-dashboard.html` | 1 |
| **I19** | Verify + version bump + README + final regression | `src/app.js`, `package.json`, `README.md` | — |

## Bundle impact estimate
- 30 Lucide symbols × ~250 bytes each = ~7.5 KB sprite
- icon() helper: ~0.5 KB
- HTML edits: -2 KB (ลด emoji encoding)
- **Net: +6 KB** → app.min.js 223.2 → ~229 KB (under 260 budget)
