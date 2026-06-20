---
name: performance-optimization
description: Measure-first approach to web performance. Use when performance requirements exist, you suspect regressions, or you need to optimize a specific metric. Use when before-and-after measurement is possible.
source: addyosmani/agent-skills@v0.6.2
adapted_for: A-Wiki
---

# Performance Optimization

## Overview

Never optimize without measuring first. Performance intuition is unreliable — what feels slow may be fast, and what feels fast may hide a regression. This skill follows a measure-first approach: collect data, identify the bottleneck, optimize, then measure again to confirm improvement.

## When to Use

- Performance requirements exist (LCP < 2.5s, INP < 200ms)
- A Lighthouse or Core Web Vitals audit shows poor scores
- Users report slowness or unresponsiveness
- You're adding a feature that could impact performance
- Before shipping to production (performance gate)

**When NOT to use:** The feature is not user-facing, has no performance requirements, and no regression risk.

## The Measure-First Process

### Step 1: Establish the Baseline

Run the measurement BEFORE making any changes:
```
Baseline (before optimization):
- LCP: 3.8s
- INP: 320ms
- CLS: 0.15
- Bundle size: 420KB gzipped
```

### Step 2: Identify the Bottleneck

Use profiling tools to find what's slow:
- **LCP slow?** → Largest element? Render-blocking resource? Slow server?
- **INP slow?** → Long tasks? Event handler too complex? Layout thrashing?
- **CLS high?** → Images without dimensions? Dynamic content? Font swap?
- **Bundle large?** → Bundle analysis, code splitting opportunities
- **API slow?** → Database query? External call? Unnecessary computation?

### Step 3: Apply the Target Optimization

One optimization at a time. Measure after each.

| Bottleneck | Optimization |
|---|---|
| Render-blocking resources | Inline critical CSS, defer non-critical JS |
| Large images | WebP/AVIF, responsive sizes, lazy loading |
| Long tasks | Break up with `scheduler.yield()` or `yieldToMain` |
| Layout shifts | Explicit dimensions, font-display swap |
| N+1 queries | Eager loading, batch loading, query optimization |
| Large bundles | Code splitting, tree shaking, dependency audit |

### Step 4: Measure Again

Run the same measurement after the optimization. Compare:
```
After optimization:
- LCP: 2.1s (improved 1.7s)
- INP: 180ms (improved 140ms) ✓ within target
- CLS: 0.05 (improved 0.10) ✓ within target
- Bundle size: 310KB gzipped (saved 110KB)
```

### Step 5: Guard Against Regression

- Document the baseline for future reference
- Add a performance budget check to CI
- Set up Web Vitals monitoring (RUM)

## Core Web Vitals

| Metric | Good | Target | How to Measure |
|--------|------|--------|---------------|
| LCP | ≤ 2.5s | Hero content visible | Lighthouse, Chrome DevTools |
| INP | ≤ 200ms | Interaction responsiveness | Performance panel, CrUX |
| CLS | ≤ 0.1 | Visual stability | Lighthouse, Performance panel |

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "This page feels fast enough" | Feeling is not a metric. Measure before and after. |
| "I know what the bottleneck is" | You're probably wrong. Measure first, then optimize. |
| "Small performance wins add up" | They do, but only if the bottleneck is in that area. Optimizing a non-bottleneck is wasted effort. |
| "We'll fix performance after shipping" | Performance is a feature. Shipping a slow feature means users perceive it as slow forever. |
| "This optimization is obviously correct" | Every optimization is a tradeoff. Measure to verify the tradeoff is worth it. |

## Red Flags

- Optimizing without a baseline measurement
- Multiple optimizations applied before measuring the effect
- "Premature optimization is the root of all evil" used to avoid all performance considerations
- Performance data from localhost on a MacBook Pro (not representative)
- Claiming improvement without comparative measurement
- Optimizing code that runs once at init instead of code that runs on every interaction

## Verification

- [ ] Baseline measurement recorded before any change
- [ ] Single optimization applied at a time
- [ ] Post-optimization measurement confirms improvement
- [ ] Core Web Vitals targets met (LCP, INP, CLS)
- [ ] No regressions in unrelated metrics
- [ ] Performance budget documented
- [ ] Regression guard in place (CI check or monitoring)
