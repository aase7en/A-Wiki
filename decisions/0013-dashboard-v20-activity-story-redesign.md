# ADR-0013: Dashboard v20 "Activity Story" Redesign

- **Status**: proposed
- **Date**: 2026-08-03
- **Decision Maker**: zcode (a-loop Phase 1-2)
- **Supersedes**: none (extends ADR-0010 v18 Cmd+K, ADR-0011 v19 Lucide)
- **Spec**: `docs/specs/dashboard-v20-spec.md`
- **Mockup**: `scripts/live-dashboard/v20-mockup.html`

## Context

Dashboard v19 serves a **swarm operator** (engineer): 13 technical tabs (Summary/Flow/Timeline/Graph/Skills/Coverage/Analytics/Subagents/Eval/Cost/Race/Council/Chat), metrics bar with THROUGHPUT/LATENCY/TIER, particle graph, raw event types. The user (2026-08-03) explicitly asked to **redesign for non-technical users**:

> "ทำอย่างไรก็ได้ให้ผู้ใช้มองข้อมูล Data และเข้าใจอย่างง่าย … สำหรับผู้ใช้ที่ไม่จำเป็นต้องมีความรู้ด้านเทคนิค"

Web research (Stripe/PostHog/Linear/Vercel/Langfuse/Apple WWDC803/Material 3/NN/g/Okabe-Ito) confirmed 10 patterns for this audience; the top pattern is "one plain-language hero metric + max 5-7 top-level items + funnel not node-graph + data→insight→action inline".

## Decision

**Adopt "Activity Story" concept (Stripe/PostHog-inspired)** with full Home-view redesign while preserving all v19 capability behind a Pro mode toggle.

### What changes
1. **Default landing** = new `view-home` (was `view-summary`)
2. **Hero**: one plain-Thai sentence "AI ช่วยคุณทำงาน {N} งาน · ประหยัด ${X}" with count-up once
3. **4 story tiles** (Miller's Law cap): Active / Done / Saved / Risks
4. **Funnel** (Think→Plan→Build→Verify→Ship) replaces particle graph as primary flow viz
5. **Stream** with plain-language sentences + inline actions (data→insight→action)
6. **Plain-language layer** (`src/plainlang.js`) translates every event type + tier + hook
7. **Unified animation system** collapses 17 → 8 keyframes, adopts cubic-bezier(0.2,0,0,1)
8. **Onboarding**: help strip + plain-language callout (none existed in v19)
9. **Pro mode toggle** hides 13 old views (default off for non-tech)

### What stays
- All SSE/REST/simulator infrastructure (untouched)
- All 13 v19 views (hidden behind Pro mode, code unchanged)
- vis-network graph (now drill-down only)
- Settings, Chat, Skills (functional, just not in default landing)
- 164 v19 tests (must all still pass)

## Alternatives Considered

### Alt-1: Concept B "Living Organism" (Apple Health Rings)
- **Pros**: visually striking, reuses `spawnThought`, engaging
- **Cons**: Apple Watch literacy barrier; SVG ring performance cost; thought bubbles can clutter
- **Rejected**: lower research backing than Concept A

### Alt-2: Concept C "Conversational Dashboard" (ChatGPT-style)
- **Pros**: most accessible language; reuses Chat view
- **Cons**: poor for at-a-glance monitoring with parallel agents; typed text slower than visual
- **Rejected**: doesn't fit "live monitoring" use case (only fits "ask AI" use case)

### Alt-3: Replace (delete 8 of 13 views, keep 5)
- **Pros**: simpler IA long-term
- **Cons**: breaks power-user workflows; high regression risk on data flows; user said "ยึดความสามารถเดิม"
- **Rejected**: violates user constraint

### Alt-4: Additive (just add Home as 14th tab)
- **Pros**: fastest, lowest risk
- **Cons**: cognitive load unchanged (14 tabs still visible); doesn't solve the core problem
- **Rejected**: doesn't meet the spirit of "redesign"

## Consequences

### Positive
- Non-technical users see a friendly, story-driven dashboard by default
- Animation system unified (easier to maintain, smaller CSS)
- Onboarding reduces first-time-user confusion
- All v19 power retained behind one toggle (zero capability loss)

### Negative
- +~35KB bundle (plainlang.js + home.js + HTML/CSS additions) — stays under 280KB budget
- Initial Pro mode users need one extra click (acceptable trade-off)
- ~12 new tests to maintain

### Neutral
- v19 CSS cleanup removes some decorative animations (ripple, particle) — replaced by intentional ones

## Compliance

- **Iron Law #1**: every chunk starts with failing test (12 new tests)
- **Iron Law #5**: AGENTS.md / CLAUDE.md untouched
- **Iron Law #6**: no real names; `python scripts/check-privacy.py` in verify chunk
- **Iron Law #11**: claim `zcode-v20-redesign-*` registered (4h TTL, self-reaping)
- **Bundle budget**: ≤280KB (well under 300KB hard cap)
- **Backward-compat**: `?view=summary` auto-enables Pro mode (no broken bookmarks)

## Open Questions

- Should we eventually localize beyond Thai? (deferred to v21+)
- Should Pro mode be opt-out (default on for power users) or opt-in (default off)? — chose opt-in default for non-tech target audience
