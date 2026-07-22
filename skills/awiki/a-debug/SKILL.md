---
name: a-debug
description: "Debug loop ครบวงจร — reproduce → root-cause → failing-test → fix → verify → scrutinize. Chain: A-Think → debug-mantra (Iron Law #2) → root-cause-first → tdd (Iron Law #1) → fix → verify-before-done → scrutinize. รองรับ subagent fan-out สำหรับ bug ซับซ้อน (delegate-subagent → council). Trigger: 'แก้บั๊ก', 'ไม่ทำงาน', 'error', 'crash', 'fail', 'หาสาเหตุ', 'broken'."
version: 1.0.0
author: A-Wiki
domain: [debug, code]
lifecycle_phase: verify
category: pipeline
agents: [all]
invocation: manual
# 2026-07-23: both → manual — parent aggregator ไม่ควรโหลดเข้าทุก session (ประหยัด ~1.4k tokens; เรียกเอาเมื่อ /A-Debug)
---

# A-Debug — Debug Loop + Subagent Fan-out

Aggregator สำหรับ debug — บังคับ Iron Law #1 (failing test ก่อน fix) + #2 (root cause ก่อน) ผ่าน canonical skills

## เมื่อไหร่ใช้

✅ ใช้:
- แก้ bug ใดๆ (logic, perf, security, crash)
- หา root cause ของอาการผิดปกติ
- Test แดง ไม่รู้ทำไม
- Production incident

❌ ข้าม:
- Feature ใหม่ (ใช้ A-Plan → build)
- Refactor ล้วน (ใช้ code-simplification)
- lint/format (ใช้ /lint)

## Iron Laws (บังคับ — สืบทอดจาก debug-mantra + scrutinize)

> **#1: NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST**
> **#2: NO BUG FIX WITHOUT ROOT CAUSE INVESTIGATION FIRST**

ถ้า parallel model พยายาม patch โดยไม่ทำ chain ข้างล่าง → **DISCARD + REWRITE**

## Chain (7 stages)

```
┌─────────┐   ┌─────────────┐   ┌──────────────────┐   ┌─────┐   ┌─────┐   ┌──────────────────┐   ┌────────────┐
│ A-Think │──▶│ debug-mantra│──▶│ root-cause-first │──▶│ tdd │──▶│ fix │──▶│ verify-before-   │──▶│ scrutinize │
│ (1,5)   │   │ (4 mantras) │   │ (no symptom fix) │   │(red)│   │     │   │ done             │   │ (end2end)  │
└─────────┘   └─────────────┘   └──────────────────┘   └─────┘   └─────┘   └──────────────────┘   └────────────┘
                                                                                                          │
                                                                                   (bug ใหญ่)            ▼
                                                                            ┌──────────────────┐   ┌────────────┐
                                                                            │ post-mortem     │◀──│ delegate + │
                                                                            │ (optional)      │   │ council    │
                                                                            └──────────────────┘   └────────────┘
```

### Stage 1: `a-think` (steps 1 + 5)
- **Step 1 (Restate)**: อาการจริงๆคืออะไร? ไม่ใช่ "มันพัง" แต่ "function X return null เมื่อ input Y"
- **Step 5 (Pre-mortem)**: สมมุติว่า fix แล้วยังพัง — เพราะอะไร?

### Stage 2: `debug-mantra` (Iron Law #2 — 4 mantras บังคับ)
> 1. **Reproducibility** — build runnable repro ก่อน (1-5s, deterministic)
> 2. **Know the fail path** — debugger → source trace → instrumentation
> 3. **Question hypothesis** — disproof first, 3-5 ranked hypotheses
> 4. **Every run = breadcrumb** — ledger ทุก experiment

ถ้า repro ไม่ได้ → **ห้าม hypothesize** — ขอ env access / log / artifact จาก user

### Stage 3: `root-cause-first`
- ห้าม fix ปมผิด (symptom)
- ใช้ 5-Whys หรือ fishbone ถ้าซับซ้อน
- ยืนยัน root cause ผ่าน disproof experiment

### Stage 4: `tdd` (Iron Law #1)
- เขียน **failing test** ที่ reproduce bug ก่อน fix
- Test ต้อง fail ก่อน → pass หลัง fix (เท่านั้นจึงยืนยันว่า fix ถูก)

### Stage 5: Fix
- Minimal change ที่จบ root cause
- ห้าม "while I'm at it" refactor (แยก commit)

### Stage 6: `verify-before-done`
- run full test suite (ไม่ใช่แค่ test ใหม่)
- manual smoke test ถ้าเกี่ยวกับ UI/integration
- confirm ไม่ break regression

### Stage 7: `scrutinize`
- end-to-end review ( outsider perspective, ไม่ใช่ diff-local)
- ถาม: "ควรมีไหม?" "มีวิธีง่ายกว่าไหม?" "ตามจริงไหม?"
- ถ้า fail → กลับไป stage 2

## Subagent Fan-out (bug ซับซ้อนเท่านั้น)

เมื่อไหร่ใช้: bug ที่ root cause ไม่ชัด หลัง stage 2-3 หรือกระทบหลายระบบ

### Pattern: `delegate-subagent` → `council`
1. `delegate-subagent` — กระจาย hypothesis 3-5 ตัวขนานกัน (แต่ละตัวสำรวจ root cause ทางเดียว)
2. `council` — multi-perspective review:
   - senior engineer: logic/architecture
   - QA: edge cases / regression
   - security: exploit surface
   - merge เมื่อ critical/important findings

### เมื่อไหร่ใช้ loop (`continuous-agent-loop`)
- bug ที่ test ยังไม่เขียวหลัง fix รอบแรก
- ตั้ง max iterations (เช่น 5) — ถ้าเกิน = กลับไป stage 2

## Handoff contract

แต่ละ stage ส่ง output เป็น ledger entry:
```yaml
stage: <name>
input: "<what came in>"
hypothesis: "<what we tested>"
evidence: "<log/repro output>"
finding: "<what we learned>"
next: "<which stage + why>"
```

## Rationalization table

| ข้ออ้าง | คำตอบโต้ |
|---|---|
| "ลองแก้ดูก่อน" | ไม่ได้ — Iron Law #1/#2; failing test ก่อน |
| "bug ง่าย ข้าม root cause" | ถ้าง่ายจริง root cause เจอใน <1 นาที — ทำเลย |
| "ใช้ workaround พอ" | workaround = symptom fix; root cause จะกลับมาถามหา |
| "test เสียเวลา" | test คือ repro artifact — เก็บไว้กัน regression ตลอดชีพโค้ด |

## Examples

**Bad (skip chain)**:
```
user: dashboard รพ. error 500 เปิดไม่ได้
agent: [ลอง restart server] → ok รอบนึง → พังอีกวันถัดมา
```

**Good (follow chain)**:
```
user: dashboard รพ. error 500
A-Think: restate = GET /api/dashboard return 500 intermittent (3/10 requests)
debug-mantra:
  1. Repro: curl loop 10x → 3 ครั้ง 500
  2. Fail path: stack trace → null pointer in patient_repo.get_active()
  3. Hypothesis: cache miss + DB timeout race
  4. Ledger: hypothesis 1 (cache) ✓, hypothesis 2 (timeout) ✗
root-cause-first: cache TTL หมด + DB slow query ไม่มี fallback → null
tdd: test_dashboard_handles_cache_miss (RED)
fix: add null-check + retry logic (minimal change)
verify: full suite + curl 1000x → 0/1000 error
scrutinize: ถาม "ทำไม DB slow?" → missing index → separate ticket
```

## Invocation

```
/A-Debug [bug description + repro steps if known]
```
