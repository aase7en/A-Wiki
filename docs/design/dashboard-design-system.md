# A-Wiki Live Dashboard — Design System

> **Version**: 2.2-light · **Created**: 2026-06-16 · **Updated**: 2026-06-19
> **Purpose**: Canonical design tokens + 10-dimension audit baseline for the Live Dashboard redesign
> **Source**: Synthesized from `skills/ecosystem/design-system/` + `skills/ecosystem/frontend-design-direction/` + GLM 5.2 critic loop

---

## 🎯 Design Principles

1. **Operator-first** — every pixel answers an operator question (what's running? what's the cost? what failed?)
2. **Cost discipline** — cost tier visible at all times; free-tier usage celebrated
3. **Thai-readable** — primary user reads Thai; copy is professional, not casual
4. **Light-first** — light default (`#f5f7f6`); dark toggle available via `[data-theme="dark"]` persisted in `localStorage`
5. **Density without clutter** — Grafana-grade information density, not "AI demo" whitespace
6. **Single-file portability** — no build step, no npm install, opens in any browser

---

## 🎨 Color Tokens

### Light Theme (`:root` default)

| Token | Value | Use |
|-------|-------|-----|
| `--bg` | `#f5f7f6` | Body background (off-white with green tint) |
| `--s0` (surface) | `#ffffff` | Card/surface background |
| `--s1` (surface-2) | `#f1f5f4` | Secondary surface, hover state |
| `--b0` (border) | `#e2e8f0` | Default border |
| `--b1` (border-2) | `#cbd5e1` | Strong border, hover border |
| `--t0` (text) | `#0f172a` | Primary text (charcoal, high contrast) |
| `--t1` (text-2) | `#475569` | Secondary text |
| `--t2` (text-3) | `#94a3b8` | Tertiary/hint text |
| `--a0` (accent) | `#4ADE80` | Mint green — primary accent |
| `--a1` (accent-2) | `#A3E635` | Lime green — secondary accent |
| `--ok` | `#16a34a` | Success green |
| `--warn` | `#d97706` | Warning amber |
| `--bad` | `#dc2626` | Error red |

### Dark Theme Override (`[data-theme="dark"]`)

| Token | Value | Change |
|-------|-------|--------|
| `--bg` | `#06060d` | Deep space |
| `--s0` | `#14142a` | Dark surface |
| `--s1` | `#1e1e3a` | Dark secondary |
| `--b0` | `#26265a` | Dark border |
| `--b1` | `#3a3a6a` | Dark strong border |
| `--t0` | `#f1f5f9` | Light primary |
| `--t1` | `#cbd5e1` | Light secondary |
| `--t2` | `#64748b` | Light tertiary |
| `--a0` | `#5eead4` | Teal (dark accent) |
| `--a1` | `#fbbf24` | Amber (dark accent) |
| `--ok` | `#34d399` | Green |
| `--warn` | `#fbbf24` | Amber |
| `--bad` | `#f87171` | Red |

### Role Colors (graph nodes, agent cards)

| Role | Token | Hex |
|------|-------|-----|
| Architect | `--ra` | `#22d3ee` (cyan) |
| Subagent | `--rs` | `#a78bfa` (violet) |

### Provider Colors (settings panel, lane badges)

| Provider | Token | Hex |
|----------|-------|-----|
| Gemini | `--pr` | `#4285F4` |
| DeepSeek | `--ds` | `#00c4d4` |
| Groq | `--gq` | `#ff6b6b` |
| Anthropic | `--an` | `#d4a574` |
| Zhipu | `--zp` | `#34d399` |

---

## 🔤 Typography

**Font stacks**:
- Body: `-apple-system, system-ui, sans-serif`
- Mono (data, timestamps, brackets): `ui-monospace, monospace` (prefers system fonts; JetBrains Mono optional via CDN)

**Size ramp** (6 stops, fluid via `clamp()`):

| Token | Range | Use |
|-------|-------|-----|
| `--f1` | 10–11px | Badges, hints |
| `--f2` | 11–12px | Labels, secondary text |
| `--f3` | 12–13px | Body small |
| `--f4` | 14–15px | Body, card titles |
| `--f5` | 16–18px | Brand, headings |
| `--f6` | 20–24px | KPI values |

---

## 📏 Spacing & Radii

**Spacing scale** (4px base, 6 stops):

`--p1` (4px) · `--p2` (8px) · `--p3` (12px) · `--p4` (16px) · `--p5` (20px) · `--p6` (24px)

**Radii** (consistent across components):

`--r1` (4px) · `--r2` (8px) · `--r3` (12px) · `--r4` (16px) · `--r9` (9999px)

---

## 🌑 Shadows

| Token | Light Value | Dark Value |
|-------|-------------|------------|
| `--sc` (card) | `0 2px 8px rgba(0,0,0,.06)` | `0 4px 14px rgba(0,0,0,.45)` |
| `--sm` (medium) | `0 4px 14px rgba(0,0,0,.08)` | `0 8px 26px rgba(0,0,0,.55)` |

---

## 🧱 Component Architecture (3-Zone Layout)

```
┌─ HEADER ─────────────────────────────────────────────────────┐
├─ Z1: METRICS BAR ───────────────────────────────────────────┤
├─ Z2-LEFT (ORCHESTRATOR) ────┬─ Z2-CENTER (SUBAGENTS | VIEWS) ──┬─ SIDEBAR ─┤
├─ Z3: RESOURCE MONITOR ───────────────────────────────────────┤
├─ RECOMMENDATION STRIP ───────────────────────────────────────┤
```

- **Z1 Metrics Bar**: `[ BASE ]` provider count · throughput · P50/P99 latency · uptime · total requests
- **Z2-Left Orchestrator**: Origin card, status, active model, cost tier progress bar, view toggle
- **Z2-Center**: Default = subagents grid (agent cards); toggleable to Flow / Timeline / Graph views
- **Z3 Resource Monitor**: Per-model utilization bars + infra footer
- **Right sidebar**: Event log (retained from v2.1)
- **Settings**: Slide-over overlay (Models, API Keys, Help) — retained from v2.1

---

## 📊 10-Dimension Audit Baseline

| Dimension | v2.1 | v2.2 | How |
|-----------|------|------|-----|
| Color consistency | 9 | 9 | Token system (light + dark) |
| Typography hierarchy | 9 | 8 | 6-stop ramp (reduced from 8), sans + mono |
| Spacing rhythm | 9 | 9 | 4px base scale enforced |
| Component consistency | 9 | 9 | Shared tokens, minimal per-component rules |
| Responsive | 9 | 8 | 3 breakpoints (900/700px); layout collapses to single column |
| Theme | 10 | 10 | Light default + dark toggle via `[data-theme]` + `localStorage` |
| Animation | 8 | 7 | Reduced transitions for < 60KB target; core anims retained |
| Accessibility | 9 | 8 | `prefers-reduced-motion` honored; basic focus rings; contrast ≥ 4.5:1 |
| Information density | 9 | 9 | 3-zone layout packs more data in same space |
| Polish | 9 | 8 | Leaner CSS trade-off for size budget |

---

## 🚫 Anti-Patterns to Avoid

- ❌ Purple→cyan gradient (default AI aesthetic)
- ❌ Glass morphism without purpose
- ❌ Drop shadows on every element (use elevation layers instead)
- ❌ Mixed border-radius (pick one radius per component tier)

---

## ✅ Definition of Done (per v2.2)

- [x] All CSS uses tokens, no hardcoded hex outside `:root`
- [x] `grep -c "primary-card\|connector-svg\|model-grid" live-dashboard.html` = 0
- [x] HTML file size < 60KB (61,437 bytes)
- [x] 17/17 tests pass
- [x] Browser manual check on desktop + mobile breakpoint
- [x] Light default + dark toggle persists via `localStorage`

---

*Maintained alongside `live-dashboard.html` — update when tokens change.*
