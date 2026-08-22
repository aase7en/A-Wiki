---
name: a-web
description: "สร้างเว็บ/frontend ครบ chain — ผูก 7-phase spine เข้ากับ frontend-design, react-patterns, nextjs-turbopack, api-design, e2e-testing, frontend-a11y. Dispatcher ล้วน ไม่มีเทคนิคของตัวเอง. Trigger: 'สร้างเว็บ', 'เว็บไซต์', 'frontend', 'react', 'nextjs'."
version: 1.0.0
author: A-Wiki
domain: [engineering, ux-ui, code]
lifecycle_phase: meta
category: pipeline
agents: [all]
status: canonical
invocation: manual
invocation_hint: "/A-Web"
a_phase: any
---

# A-Web — งานเว็บ / frontend

> **Dispatcher ล้วน** — ไม่มีเทคนิคเป็นของตัวเอง หน้าที่เดียวคือผูก 7-phase spine
> เข้ากับ canonical skill ที่มีอยู่แล้ว ถ้าต้อง *อธิบายวิธีทำ* แปลว่ามันควรเป็น
> canonical skill ไม่ใช่ pack

## เมื่อไหร่ใช้

✅ ใช้:
- สร้างหน้าเว็บ / web app ใหม่
- แก้ / เพิ่ม UI component
- งาน frontend ที่ต้องผ่านทั้ง design → build → test

❌ ข้าม:
- แก้ CSS บรรทัดเดียว → ทำเลย
- bug frontend ที่ชัดเจนแล้ว → `/A-Debug`
- ออกแบบ API อย่างเดียว ไม่มี UI → `/A-Plan`

## Iron Law

> **`focus_set` ก่อนเริ่มเสมอ** — pack ครอบทั้ง chain ถ้าไม่ประกาศ phase
> จะไหลจาก ASK ไป IMPLEMENT โดยไม่มีอะไรจับได้

```
focus_set({"skill": "a-web", "goal": "<done criteria>", "phase": "ask"})
```

## Phase → skill

| Phase | ใช้ | ทำอะไร |
|-------|-----|--------|
| ASK | `a-think` · `grill-with-docs` | ถามให้ชัดก่อน: ใครใช้ อะไรคือ done |
| DESIGN | **`ui-ux-pro-max`** (data: 161 palettes + 74 fonts + 99 rules) · **`taste-skill`** (anti-AI-slop) · **`a-design`** (composition + Quality Gate) · `accessibility` (WCAG 2.2 AA from start) · `api-design` (contract) | palette/font/style selection, anti-slop defaults, a11y, สัญญา API |
| PLAN | `a-plan` | แตกเป็น slice ที่ ship ได้ทีละอัน |
| IMPLEMENT | `react-patterns` · `nextjs-turbopack` · `frontend-patterns` · `vite-patterns` · `motion-advanced` | เขียนจริง |
| REVIEW | `a-council` · `frontend-a11y` | รีวิว + a11y (WCAG) |
| DEBUG | `a-debug` · `browser-qa` | repro → root cause → failing test |
| TEST | `e2e-testing` · `webapp-testing` · `react-performance` | E2E + perf |

> เดิน phase ด้วย `focus_advance` · จบงาน `focus_clear`
> phase ไหนไม่มี skill เฉพาะ → ใช้ตัว generic ของ spine (`a-plan`, `a-council`, `a-debug`)

## Rationalization table

| ข้ออ้าง | คำตอบโต้ |
|---|---|
| "ข้าม ASK/DESIGN ไปโค้ดเลย" | pack ไม่ได้ทำให้ข้ามได้ — งานเว็บ/วิจัย/คอนเทนต์พังตรง requirement บ่อยกว่าตรงโค้ด |
| "เรียก canonical skill ตรงก็ได้" | ได้ — แต่ยังต้อง `focus_set` ไม่งั้นไม่มีใครรู้ว่าอยู่ phase ไหน |
| "pack นี้ควรมีเทคนิคของตัวเอง" | ไม่ — ถ้าต้องอธิบายวิธีทำ ให้ไปสร้าง canonical skill แล้ว bind มาแทน |

## Invocation

```
/A-Web "<งาน>"
```
