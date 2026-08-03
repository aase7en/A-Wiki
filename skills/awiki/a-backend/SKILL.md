---
name: a-backend
description: "สร้าง backend/API/service — bind api-design, backend-patterns, database-migrations, postgres-patterns, redis-patterns, prisma-patterns, error-handling, api-connector-builder. Dispatcher ล้วน ไม่มีเทคนิคของตัวเอง. Trigger: 'backend', 'API', 'service', 'endpoint', 'REST', 'database schema'."
version: 1.0.0
author: A-Wiki
domain: [engineering, code]
lifecycle_phase: meta
category: pipeline
agents: [all]
status: canonical
invocation: manual
invocation_hint: "/A-Backend"
a_phase: any
---

# A-Backend — งาน backend / API / service

> **Dispatcher ล้วน** — ไม่มีเทคนิคเป็นของตัวเอง

## เมื่อไหร่ใช้

✅ ใช้:
- สร้าง API/service ใหม่
- ออกแบบ database schema / migration
- แก้ / เพิ่ม endpoint
- เชื่อม third-party API (connector)
- งาน backend ที่ต้องผ่านทั้ง design → build → test

❌ ข้าม:
- แก้ endpoint เดียว → ทำเลย
- งาน frontend/UI → `/A-Web`
- bug backend ที่ชัดเจน → `/A-Debug`

## Iron Law

> **`focus_set` ก่อนเริ่มเสมอ**

```
focus_set({"skill": "a-backend", "goal": "<done criteria>", "phase": "ask"})
```

## Phase → skill

| Phase | ใช้ | ทำอะไร |
|-------|-----|--------|
| ASK | `a-think` · `grill-with-docs` | นิยาม: REST/GraphQL/gRPC? sync/async? scale? |
| DESIGN | `api-design` · `domain-modeling` | contract + schema + boundary |
| PLAN | `a-plan` | แตกเป็น slice (model → endpoint → migration → test) |
| IMPLEMENT | `backend-patterns` · `api-connector-builder` · framework pick | django/fastapi/laravel/nestjs/springboot/quarkus/golang/rust |
| REVIEW | `a-council` · `error-handling` · `security-and-hardening` | รีวิว + ตรวจ error path + security |
| DEBUG | `a-debug` | repro → root cause → failing test |
| TEST | `python-testing` · `e2e-testing` · `database-migrations` (verify) | unit + integration + migration smoke |

> เลือก DB stack ตาม use case: `postgres-patterns` (relational), `redis-patterns` (cache/queue), `prisma-patterns` (ORM), `clickhouse-io` (analytics)

## Rationalization table

| ข้ออ้าง | คำตอบโต้ |
|---|---|
| "ใช้ framework skill ตรงๆ ก็ได้" | ได้ — แต่ยังต้อง `focus_set` ไม่งั้นไม่มีใครรู้ว่าอยู่ phase ไหน |
| "ไม่ต้องออกแบบ API ก่อนโค้ด" | ผิด — backend พังตรง contract บ่อยกว่าตรง implementation |

## Invocation

```
/A-Backend "<งาน>"
```
