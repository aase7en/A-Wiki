# Dashboard v18 — Spec

**ADR**: 0010-dashboard-v18-cmdk-palette-polish
**Date**: 2026-07-22
**Status**: approved (after Stage 2 grill)
**Direction**: A4 Mixed — Polish 2 จุด + Cmd+K palette upgrade

---

## Functional Requirements (testable)

### Polish 1: emoji-headings removal (FR-1)
- **FR-1.1**: ลบ emoji prefix ออกจาก 8 h5 headings ใน src/skills.js detail panel
- **FR-1.2**: แทนที่ด้วย subtle separator "•" หรือ plain text (no emoji)
- **FR-1.3**: heading ยังอ่านออก + accessible (screen reader ไม่อ่าน "memo emoji")
- **Acceptance**: `pytest -k emoji_headings` ผ่าน

### Polish 2: transition token migration (FR-2)
- **FR-2.1**: 23 hardcoded `transition: X .Ys ...` ใน styles.css → migrate ไปใช้ `--t-fast` (120ms) / `--t-normal` (200ms) / `--t-slow` (320ms) + `--ease`
- **FR-2.2**: Mapping rule:
  - `.1s`–`.15s` → `--t-fast`
  - `.2s`–`.25s` → `--t-normal`
  - `.3s+` → `--t-slow`
- **FR-2.3**: Animations (keyframes) ไม่ migrate (different concern)
- **Acceptance**: `pytest -k transition_tokens` ผ่าน (hardcoded count ≤ 3 — allow for unavoidable cases)

### Feature: Cmd+K palette upgrade (FR-3)
- **FR-3.1**: เปลี่ยน emoji indicators (🧩🌊📊⌨️) เป็น dot style:
  - skill → `◆` brand color
  - view → `●` neutral color
  - shortcut → `◇` muted color
- **FR-3.2**: เพิ่ม `⌘K` hint badge ใน header (header ขวา ข้าง theme toggle)
  - Win/Linux: แสดง `Ctrl K`
  - Mac: แสดง `⌘ K`
- **FR-3.3**: ลบ `backdrop-filter:blur(3px)` ใน palette-backdrop (slop pattern)
- **FR-3.4**: palette-row hover ใช้ `--brand-muted` + `--t-fast`
- **FR-3.5**: Recent commands — บันทึก last 5 used ใน `awiki-palette-recent` localStorage + แสดง at top เมื่อ query ว่าง
- **FR-3.6**: Arrow navigation คงทำงาน + Esc ปิด (existing)
- **Acceptance**: `pytest -k cmdk_palette` ผ่าน + Playwright runtime check palette opens + arrow nav works

---

## Non-Functional Requirements

### NFR-1: Legacy theme compat
- `[data-theme="dark"]` (default), `[data-theme="light"]`, `[data-theme="green-white"]` ต้องใช้ได้ครบ
- Palette ใช้ var() tokens เท่านั้น ไม่ hardcode hex
- **Test**: เปิด 3 themes ใน Playwright + screenshot diff

### NFR-2: Bundle size
- `app.min.js` ≤ 250 KB (ปัจจุบัน 219.6 KB, budget 30 KB)
- `styles.css` ≤ 50 KB (ปัจจุบัน ~45 KB)
- **Test**: `npm run size`

### NFR-3: Test regression
- 134 tests ที่มีอยู่ต้องผ่านต่อ
- เพิ่ม ≥ 5 tests ใหม่สำหรับ v18 (emoji/transition/cmdk)
- **Test**: `pytest tests/test_live_dashboard_html.py`

### NFR-4: Runtime clean
- 0 console errors / 0 pageerrors / 0 request failures (Playwright runtime_audit.py)
- **Test**: existing audit harness

### NFR-5: Design score
- Visual audit 10-dimension: 8.4 → **9.3+** average
- มีผลกระทบโดยตรง: Typography (emoji removal) + Animation (transition tokens) + Polish (palette upgrade)
- **Test**: `python tests-browser/visual_audit_extract.py` + manual re-score

### NFR-6: Accessibility
- Cmd+K hint ต้องมี `aria-label` สำหรับ screen reader
- palette-modal ใช้ existing `_openModalTrap` (focus trap) — คงไว้
- Color contrast ≥ AA (4.5:1) สำหรับทุก text+bg combination ใน palette
- **Test**: axe-core check (ถ้ามี) หรือ manual WCAG review

---

## Acceptance Criteria

**v18 สำเร็จเมื่อ**:
1. ✅ FR-1, FR-2, FR-3 ทั้งหมดผ่าน (tests + runtime)
2. ✅ NFR-1 ถึง NFR-6 ผ่าน
3. ✅ design score ≥ 9.3 (visual audit)
4. ✅ user พิมพ์ Cmd+K แล้ว palette โผล่ + ใช้งานได้ใน 1 keystroke
5. ✅ DASHBOARD_VERSION = 'v18.0.0'
6. ✅ README v18 section + session-memory entry

---

## Out of scope (v19+)

- inline-style padding refactor (87 border-radius count)
- PWA service worker
- subagent drill-down (fan-out tree)
- cost-projection What-if
- palette expansion (more accent hues)
- Lighthouse ≥95 (separate perf wave)

---

## Risks

| Risk | Mitigation |
|------|-----------|
| ถอน emoji ออกแล้ว heading ดู "จืด" | ใช้ subtle separator + bold พอ |
| transition migration ทำให้ motion เปลี่ยน | ใช้ mapping rule ตรงตัว + ทดสอบทุก page |
| palette recent commands localStorage quota | จำกัด 5 items × ~30 chars = 150 bytes (negligible) |
| Cmd+K conflict กับ browser/extension | ใช้ `e.preventDefault()` ที่มีอยู่แล้ว + ทดสอบ Ctrl+K |
