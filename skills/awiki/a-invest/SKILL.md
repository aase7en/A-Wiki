---
name: a-invest
description: "งานวิเคราะห์การลงทุน — ผูก 7-phase spine เข้ากับ finance-pipeline, monte-carlo-quant-analysis, ito-trade-planner, ito-market-intelligence, prediction-market-risk-review. Trigger: 'ลงทุน', 'หุ้น', 'พอร์ต', 'investment', 'portfolio'."
version: 1.0.0
author: A-Wiki
domain: [trader, business]
lifecycle_phase: meta
category: pipeline
agents: [all]
status: canonical
invocation: manual
invocation_hint: "/A-Invest"
a_phase: any
---

# A-Invest — การลงทุน

> **Dispatcher ล้วน** — ไม่มีเทคนิคเป็นของตัวเอง หน้าที่เดียวคือผูก 7-phase spine
> เข้ากับ canonical skill ที่มีอยู่แล้ว ถ้าต้อง *อธิบายวิธีทำ* แปลว่ามันควรเป็น
> canonical skill ไม่ใช่ pack

## เมื่อไหร่ใช้

✅ ใช้:
- วิเคราะห์การลงทุน / เปรียบเทียบพอร์ต
- ประเมินความเสี่ยง, quant simulation
- market intelligence ก่อนตัดสินใจ

❌ ข้าม:
- ถามราคาปัจจุบัน → ค้นเว็บตรง
- งานธุรกิจทั่วไปที่ไม่ใช่การลงทุน → `project-flow-ops` หรือ `agent-sort` (เรียกตรง)

## Iron Law

> **`focus_set` ก่อนเริ่มเสมอ** — pack ครอบทั้ง chain ถ้าไม่ประกาศ phase
> จะไหลจาก ASK ไป IMPLEMENT โดยไม่มีอะไรจับได้

```
focus_set({"skill": "a-invest", "goal": "<done criteria>", "phase": "ask"})
```

## Phase → skill

| Phase | ใช้ | ทำอะไร |
|-------|-----|--------|
| ASK | `a-think` | สมมติฐานคืออะไร รับความเสี่ยงได้แค่ไหน |
| DESIGN | `ito-trade-planner` | วางกรอบกลยุทธ์ + เกณฑ์เข้า/ออก |
| PLAN | `a-plan` | แตกเป็นขั้นที่ตรวจสอบได้ |
| IMPLEMENT | `finance-pipeline` · `ito-market-intelligence` | ดึงข้อมูล + วิเคราะห์ |
| REVIEW | `a-council` · `prediction-market-risk-review` | รีวิวความเสี่ยงหลายมุม |
| DEBUG | `a-debug` | ผลไม่ตรงโมเดล → หาว่าสมมติฐานไหนพัง |
| TEST | `monte-carlo-quant-analysis` · `ito-basket-compare` | simulate + เทียบพอร์ต |

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
/A-Invest "<งาน>"
```
