# Performance Checklist

**source**: addyosmani/agent-skills@v0.6.2 | **adapted**: A-Wiki | **verified**: 2026-06-20

Quick reference checklist for web application performance. Use alongside the `performance-optimization` skill.

## Table of Contents

- [Core Web Vitals Targets](#core-web-vitals-targets)
- [Frontend Checklist](#frontend-checklist)
- [Backend Checklist](#backend-checklist)
- [Measurement Commands](#measurement-commands)
- [Common Anti-Patterns](#common-anti-patterns)

## Core Web Vitals Targets

| Metric | Good | Needs Work | Poor |
|--------|------|------------|------|
| LCP (Largest Contentful Paint) | ≤ 2.5s | ≤ 4.0s | > 4.0s |
| INP (Interaction to Next Paint) | ≤ 200ms | ≤ 500ms | > 500ms |
| CLS (Cumulative Layout Shift) | ≤ 0.1 | ≤ 0.25 | > 0.25 |

## Frontend Checklist

### Images
- [ ] Images use modern formats (WebP, AVIF)
- [ ] Images are responsively sized (`srcset` and `sizes`)
- [ ] Images have explicit `width` and `height` (prevents CLS)
- [ ] Below-the-fold images use `loading="lazy"` and `decoding="async"`
- [ ] Hero/LCP images use `fetchpriority="high"` and no lazy loading

### JavaScript
- [ ] Bundle size under 200KB gzipped (initial load)
- [ ] Code splitting with dynamic `import()` for routes and heavy features
- [ ] Tree shaking enabled
- [ ] No blocking JavaScript in `<head>` (use `defer` or `async`)
- [ ] Long tasks (> 50ms) broken up to keep the main thread available
- [ ] Third-party scripts loaded with `async` / `defer`, audited for size

### CSS
- [ ] Critical CSS inlined or preloaded
- [ ] No render-blocking CSS for non-critical styles

### Fonts
- [ ] Limited to 2-3 font families, WOFF2 format only
- [ ] Self-hosted when possible
- [ ] `font-display: swap` to avoid FOIT blocking render
- [ ] Variable fonts considered when multiple weights are required

### Network
- [ ] Static assets cached with long `max-age` + content hashing
- [ ] API responses cached where appropriate
- [ ] HTTP/2 or HTTP/3 enabled
- [ ] Resources preconnected for known origins

### Rendering
- [ ] No layout thrashing (forced synchronous layouts)
- [ ] Animations use `transform` and `opacity` (GPU-accelerated)
- [ ] Long lists use virtualization
- [ ] Off-screen sections use `content-visibility: auto`

## Backend Checklist

### Database
- [ ] No N+1 query patterns (use eager loading / joins)
- [ ] Queries have appropriate indexes
- [ ] List endpoints paginated
- [ ] Connection pooling configured
- [ ] Slow query logging enabled

### API
- [ ] Response times < 200ms (p95)
- [ ] No synchronous heavy computation in request handlers
- [ ] Bulk operations instead of loops of individual calls
- [ ] Response compression (gzip/brotli)
- [ ] Appropriate caching (in-memory, Redis, CDN)

### Infrastructure
- [ ] CDN for static assets
- [ ] Server located close to users (or edge deployment)
- [ ] Horizontal scaling configured (if needed)

## Measurement Commands

```bash
# Lighthouse CLI
npx lighthouse https://localhost:3000 --output json --output-path ./report.json

# Bundle analysis
npx webpack-bundle-analyzer stats.json

# Web Vitals in code
import { onLCP, onINP, onCLS } from 'web-vitals';
onLCP(console.log);
onINP(console.log);
onCLS(console.log);
```

## Common Anti-Patterns

| Anti-Pattern | Impact | Fix |
|---|---|---|
| N+1 queries | Linear DB load growth | Use joins, includes, or batch loading |
| Unbounded queries | Memory exhaustion, timeouts | Always paginate, add LIMIT |
| Missing indexes | Slow reads as data grows | Add indexes for filtered/sorted columns |
| Layout thrashing | Jank, dropped frames | Batch DOM reads, then batch writes |
| Unoptimized images | Slow LCP, wasted bandwidth | Use WebP, responsive sizes, lazy load |
| Large bundles | Slow Time to Interactive | Code split, tree shake, audit deps |
| Blocking main thread | Poor INP, unresponsive UI | Chunk long tasks, offload to Web Workers |
| Memory leaks | Growing memory, eventual crash | Clean up listeners, intervals, refs |
