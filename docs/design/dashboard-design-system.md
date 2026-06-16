# A-Wiki Live Dashboard — Design System

> **Version**: 2.1-pro · **Created**: 2026-06-16
> **Purpose**: Canonical design tokens + 10-dimension audit baseline for the Live Dashboard redesign
> **Source**: Synthesized from `skills/ecosystem/design-system/` + `skills/ecosystem/frontend-design-direction/` + GLM 5.2 critic loop

---

## 🎯 Design Principles

1. **Operator-first** — every pixel answers an operator question (what's running? what's the cost? what failed?)
2. **Cost discipline** — cost tier visible at all times; free-tier usage celebrated
3. **Thai-readable** — primary user reads Thai; copy is professional, not casual
4. **Dark-native** — designed dark-first; light mode is a future option, not a constraint
5. **Density without clutter** — Grafana-grade information density, not "AI demo" whitespace
6. **Single-file portability** — no build step, no npm install, opens in any browser

---

## 🎨 Color Tokens

### Elevation (4 levels, layered depth not flat)

| Token | Hex | Use |
|-------|-----|-----|
| `--elev-0` | `#06060d` | Deepest background (body) |
| `--elev-1` | `#0c0c18` | Panel background (sidebar, settings) |
| `--elev-2` | `#14142a` | Card background (KPI tiles, agent cards) |
| `--elev-3` | `#1e1e3a` | Hover/active state, raised cards |

### Semantic Accents (replace generic AI purple→cyan)

| Token | Hex | Use |
|-------|-----|-----|
| `--accent-brand` | `#5eead4` | Teal — distinctive brand, NOT default purple |
| `--accent-warm` | `#fbbf24` | Amber — cost tier L4, warnings |
| `--accent-cool` | `#60a5fa` | Blue — tasks, info |
| `--accent-success` | `#34d399` | Green — pass, done, free tier |
| `--accent-danger` | `#f87171` | Red — block, fail |

### Role Colors (graph nodes, agent cards)

| Role | Token | Hex |
|------|-------|-----|
| Primary | `--role-primary` | `#fbbf24` (amber) |
| Architect | `--role-architect` | `#22d3ee` (cyan) |
| Executioner | `--role-executioner` | `#34d399` (green) |
| Subagent | `--role-subagent` | `#a78bfa` (violet) |
| Tool | `--role-tool` | `#94a3b8` (slate) |
| Session | `--role-session` | `#fbbf24` (amber) |
| Task | `--role-task` | `#60a5fa` (blue) |

### Text Hierarchy

| Token | Hex | Use |
|-------|-----|-----|
| `--text-primary` | `#f1f5f9` | Headlines, KPI values |
| `--text-secondary` | `#cbd5e1` | Body, labels |
| `--text-tertiary` | `#64748b` | Hints, timestamps |
| `--text-disabled` | `#475569` | Disabled, placeholder |

---

## 🔤 Typography

**Font stacks**:
- Display: `'SF Pro Display', -apple-system, system-ui, sans-serif`
- Body: `'SF Pro Text', -apple-system, system-ui, sans-serif`
- Mono (data, timestamps): `'SF Mono', 'JetBrains Mono', monospace`

**Size ramp** (8 stops, fluid via `clamp()`):

| Token | Range | Use |
|-------|-------|-----|
| `--fs-2xs` | 10–11px | Badges, hints |
| `--fs-xs` | 11–12px | Labels, secondary text |
| `--fs-sm` | 12–13px | Body small |
| `--fs-base` | 14–15px | Body |
| `--fs-lg` | 16–18px | Headings |
| `--fs-xl` | 20–24px | Section titles |
| `--fs-2xl` | 26–32px | KPI values |

---

## 📏 Spacing & Radii

**Spacing scale** (4px base, 8 stops):

`--sp-0` (0) · `--sp-1` (4px) · `--sp-2` (8px) · `--sp-3` (12px) · `--sp-4` (16px) · `--sp-5` (24px) · `--sp-6` (32px) · `--sp-7` (48px)

**Radii** (consistent across components):

`--r-sm` (4px) · `--r-md` (8px) · `--r-lg` (12px) · `--r-xl` (16px) · `--r-full` (9999px)

---

## 🌑 Shadows (elevation via shadow, not just bg)

| Token | Value |
|-------|-------|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.3)` |
| `--shadow-md` | `0 4px 12px rgba(0,0,0,0.35)` |
| `--shadow-lg` | `0 8px 24px rgba(0,0,0,0.45)` |
| `--shadow-glow` | `0 0 16px rgba(94,234,212,0.25)` |

---

## 📊 10-Dimension Audit Baseline

Target scores for the redesign (1–10 scale):

| Dimension | Current | Target | How |
|-----------|---------|--------|-----|
| Color consistency | 4 | 9 | Token system replaces ad-hoc hex |
| Typography hierarchy | 5 | 9 | 8-stop ramp + display/body/mono split |
| Spacing rhythm | 4 | 9 | 4px base scale enforced |
| Component consistency | 3 | 9 | Cards/buttons/inputs share tokens |
| Responsive | 6 | 9 | 3 breakpoints + container queries |
| Dark mode | 7 | 10 | Native dark, elevation layers |
| Animation | 5 | 8 | Pulse edges, fade transitions, no jank |
| Accessibility | 4 | 9 | Contrast ≥ 4.5:1, focus rings, keyboard |
| Information density | 5 | 9 | KPI strip + sidebar split |
| Polish | 4 | 9 | GLM 5.2 critic loop on every step |

---

## 🚫 Anti-Patterns to Avoid

From `design-system` skill "AI slop detection":

- ❌ Purple→cyan gradient (default AI aesthetic)
- ❌ Glass morphism without purpose
- ❌ Generic emoji icons in headers (use SVG or remove)
- ❌ Centered empty states with floating emoji
- ❌ Drop shadows on every element (use elevation layers instead)
- ❌ Mixed border-radius (pick one radius per component tier)

---

## ✅ Definition of Done (per Step R1–R6)

- [ ] All CSS uses tokens, no hardcoded hex outside `:root`
- [ ] `grep -c "primary-card\|connector-svg\|model-grid" live-dashboard.html` = 0
- [ ] HTML file size < 60KB
- [ ] 18/18 tests pass
- [ ] Browser manual check on desktop + mobile breakpoint
- [ ] GLM 5.2 critic score ≥ 7/10 average

---

*Maintained alongside `live-dashboard.html` — update when tokens change.*