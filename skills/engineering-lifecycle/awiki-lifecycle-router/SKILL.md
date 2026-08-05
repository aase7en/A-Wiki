---
name: awiki-lifecycle-router
description: Discovers the right A-Wiki skill for a task. Loaded at session start. Routes through the A-Suite 7-phase spine (ask → design → plan → implement → review → debug → test) and maps A-Wiki-specific intents (ingest-source, lint-wiki, pharmacy-order). The authoritative trigger table is generated at wiki/A-ROUTER.md.
---

# A-Wiki Lifecycle Router

**source**: adapted from addyosmani/agent-skills using-agent-skills skill (MIT)

> **Authoritative routing lives in `wiki/A-ROUTER.md`** — generated from
> `skills-registry.json`, so it cannot drift from the skills it names. This file
> is the session-start pointer; that file is the table.
>
> Agents with MCP should call `skill_route` instead of reading either.

## Route (A-Suite spine)

```
ASK → DESIGN → PLAN → IMPLEMENT → REVIEW → DEBUG → TEST
```

```
Task arrives
    │
    ├── ไม่รู้ว่าจะใช้อะไร? ─────────────→ /A-Router  (หรือ MCP skill_route)
    ├── ยังไม่ชัดว่าต้องการอะไร? ────────→ /A-Think → grill-with-docs
    ├── ออกแบบ / วางแผนของใหม่? ─────────→ /A-Plan
    ├── งานเว็บ / frontend? ─────────────→ /A-Web
    ├── เอกสารราชการ / docx? ────────────→ /A-Doc
    ├── ค้นคว้า / วิจัย / ตรวจแหล่ง? ────→ /A-Research
    ├── คอนเทนต์ / การตลาด? ─────────────→ /A-Content
    ├── การลงทุน? ───────────────────────→ /A-Invest
    ├── ธุรกิจส่วนตัว? ──────────────────→ /A-Business
    ├── รีวิวก่อน ship? ─────────────────→ /A-Council
    ├── พัง / bug / test แดง? ───────────→ /A-Debug
    ├── งานยาวข้าม session? ─────────────→ /A-Loop "<objective>"
    └── เกินกำลัง model ปัจจุบัน? ───────→ /A-Escalate
```

ไม่ match อะไรเลย → **`/A-Think`** (fallback — ห้ามเดา)

### A-Wiki domain-specific intents

```
    ├── Wiki ingest (URL / pasted text / file)? → ingest-source
    ├── Platform fetch (Reddit/YouTube/Bilibili, no-auth, anti-bot-protected)? → platform-ingest
    ├── Wiki health check / lint? ──────────────→ lint-wiki
    ├── Wiki search? ───────────────────────────→ wiki-search-local
    ├── Pharmacy order lookup? ─────────────────→ pharmacy-order-lookup
    ├── Cross-domain synthesis? ────────────────→ ask-notebooklm
    ├── Multi-model delegation? ────────────────→ delegate-subagent
    └── Refine vague ideas? ────────────────────→ brainstorm-before-build
```

## Core operating behaviors

These apply at all times, across all skills:

1. **Route, then declare focus.** After picking a skill, call MCP `focus_set`
   with the skill, a one-line goal and the starting phase. Without it nothing
   can tell the session has drifted from DESIGN into IMPLEMENT.
2. **Walk the chain.** `focus_advance` between phases, `focus_clear` at the end.
3. **Never skip ASK/DESIGN on non-trivial work.** Most failures are requirement
   failures, not coding failures.
4. **Fallback is a decision, not a shrug.** Nothing matching means `/A-Think`,
   never "pick the nearest-looking skill".
5. **Surface assumptions** — state them before implementing. No silent guesses.
6. **Verify, don't assume** — "seems right" is never sufficient.
7. **Registry is the single source of truth** (Iron Law #10). To change how a
   skill is discovered, edit `skills-registry.json` then run
   `python scripts/regen-skill-surfaces.py`. Never hand-edit a generated surface.

## Lifecycle skills by phase

The A-* packs dispatch to these; call them directly if you already know which
one you need. Full table with triggers: `wiki/A-ROUTER.md`.

| A-phase | lifecycle skills |
|---------|------------------|
| ASK | `grill-with-docs`, `brainstorm-before-build` |
| DESIGN | `spec-driven-development`, **`a-design`** (UX/UI spine), `ui-ux-pro-max` (data: palettes/fonts/rules), `taste-skill` (anti-slop), `accessibility` (WCAG from start), `domain-modeling`, `api-design`, `codebase-design` |
| PLAN | `planning-and-task-breakdown`, `plan-orchestrate` |
| IMPLEMENT | `implement`, `build`, `tdd`, `context-budget` |
| REVIEW | `scrutinize`, `code-simplification`, `security-and-hardening`, `performance-optimization`, `two-axis-code-review` |
| DEBUG | `debug-mantra`, `post-mortem` |
| TEST | `verify-before-done`, `browser-testing-with-devtools`, `e2e-testing` |
| SHIP | `git-workflow-and-versioning`, `ci-cd-and-automation`, `documentation-and-adrs`, `observability-and-instrumentation`, `shipping-and-launch`, `deprecation-and-migration` |

## Skill rules

1. **Check for an applicable skill before starting work.** Skills encode
   processes that prevent common mistakes.
2. **Skills are workflows, not suggestions.** Follow the steps in order; do not
   skip verification.
3. **One skill at a time.** Finish or explicitly abandon before starting another.
4. **Personas do not invoke other personas** — parallel fan-out only.
5. **If a skill's Iron Law conflicts with speed, the Iron Law wins.**

---

_Rewritten 2026-07-27 (A-Suite v2 C10). The previous version routed to seven
skills under `skills/engineering-lifecycle/build/` — a directory that does not
exist — and to grill-me, an alias for `grill-with-docs`. It also predated the
entire A-* family and named none of it. Routing now points at generated surfaces
so the same rot cannot recur unnoticed._
