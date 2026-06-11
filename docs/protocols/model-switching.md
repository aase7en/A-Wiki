---
type: protocol
title: Model-Cost Switching
last_verified: 2026-06-12
tags: [ai-tools, model-switching, cost-management, swarm-intelligence]
sources:
  - ../../wiki/sources/claude-model-cost-switching-strategy-2026-06.md
---

# Model-Cost Switching

ใช้ protocol นี้เมื่อ task หลุดจาก Cost-First Pyramid Level -1 ถึง Level 3 แล้วต้องใช้ primary agent ระดับ Level 4 จริง ๆ. เอกสารนี้ไม่ได้แทน `delegation.md`; มันเป็น sub-ladder ภายใน Level 4 เพื่อเลือก model, effort, และจังหวะสลับ model ให้คุ้มต้นทุน.

## ตำแหน่งใน Cost-First Pyramid

1. เริ่มที่ local search, graph, hook, free model, cheap model, หรือ subagent ก่อนเสมอถ้างาน verifiable และไม่มีความเสี่ยงสูง.
2. ถ้างานต้องใช้ primary agent เพราะต้องมี deep reasoning, source-of-truth wiki edits, architecture, trading risk, หรือ senior review ให้เข้า ladder นี้.
3. ค่า default คือ 4b. ลดลงเป็น 4a เมื่อมี spec ชัดและตรวจผลได้. ขึ้นเป็น 4c เฉพาะเมื่อความยาวหรือความซับซ้อนคุ้ม premium 2-3x.

Related:
- `delegation.md` - Level 1-3 delegation ก่อนใช้ primary agent
- `context-compaction.md` - compress context ก่อนสลับ model
- `bot-trading-iron-law.md` - trading/risk safeguards
- `../../wiki/sources/claude-model-cost-switching-strategy-2026-06.md` - source page พร้อมข้อแก้ไขจาก chat ต้นทาง

## Level 4 Sub-Ladder

<a id="tier-4a"></a>
### 4a - ผู้ช่วย

ใช้ Haiku-class หรือ equivalent สำหรับงานที่มี answer shape ชัดเจนและ verify ง่าย เช่น boilerplate, parsing, formatting, classification, table cleanup, หรือแยก checklist จากข้อความยาว. ห้ามใช้เป็นตัวตัดสิน architecture หรือความเสี่ยงเงินจริง.

<a id="tier-4b"></a>
### 4b - ทีมช่าง (default)

ใช้ Sonnet-class หรือ equivalent เป็น default ของงาน implementation: เขียนตาม spec, refactor scoped code, สร้าง tests, แก้ bug หลัง root cause ชัดแล้ว, integrate API, และเขียน wiki/doc ที่มี source ครบ.

<a id="tier-4c"></a>
### 4c - สถาปนิก

ใช้ Opus/Fable-class หรือ equivalent เมื่อต้องการ one-shot architecture, algorithm design, trading strategy/risk design, ambiguous multi-system decision, หรือ critical review ที่ถ้าพลาดแล้วแพง. หลังได้ spec แล้วต้องลดกลับ 4b ทันที.

## Effort Policy

| Effort | ใช้เมื่อ | หลีกเลี่ยงเมื่อ |
|---|---|---|
| `low` | review สั้น, classify, final sanity check, critical review ที่ spec ชัด | root cause ยังไม่ชัด |
| `medium` | design รายคำถาม, tradeoff ไม่กว้างมาก, hybrid phase | architecture ใหญ่ที่ต้องคิดครั้งเดียว |
| `high` | default เมื่อไม่ระบุ, implementation reasoning, bug trace ปานกลาง | งาน rote ที่ลง 4a ได้ |
| `xhigh` | coding/agentic task ซับซ้อน, หลาย constraint, ต้องวางแผนก่อนแก้ | งานย่อยที่แตก chunk ได้ |
| `max` | one-shot architecture, irreversible design, strategy/risk framework | งานพิมพ์โค้ดหรือแก้ไฟล์จำนวนมาก |

ข้อเท็จจริงที่ verify แล้ว: effort มี 5 ระดับคือ `low | medium | high | xhigh | max`. เปอร์เซ็นต์ token ต่อ effort จาก chat ต้นทางยัง unverified จึงห้ามใช้เป็นตัวเลข policy.

## Cache และ Context

Master Context Document (MCD) ของ A-Wiki คือ `wiki/context/wiki-overview.md` บวก overview ราย domain ที่โหลดตามงาน. Pattern ที่คุ้มคือ cache prefix เดิมแล้วถามหลายข้อใน session เดียว แทนการเปิด prompt ใหม่ซ้ำ ๆ.

| เรื่อง | Policy |
|---|---|
| Cache read | ประมาณ 0.1x input price หรือประหยัดราว 90% เมื่อ prefix hit |
| Cache write | 1.25x สำหรับ TTL 5 นาที หรือ 2x สำหรับ TTL 1 ชั่วโมง |
| Minimum prefix | 2048 tokens สำหรับ Fable 5 ตาม source page |
| Break-even | คุ้มเมื่อ prefix ถูกอ่านซ้ำตั้งแต่ 2 ครั้งขึ้นไป |
| Before switch | compress context เหลือไม่เกิน 500 tokens แล้วแนบ pointer ไปไฟล์ source-of-truth |

## 5 หลักการฉบับ A-Wiki

| หลักการ | วิธีทำใน repo นี้ |
|---|---|
| Prompt caching | ใช้ `wiki/context/wiki-overview.md` เป็น MCD และโหลด domain overview เฉพาะที่ต้องใช้ |
| Architect, not typist | 4c ออกแบบ spec/ADR/test plan; 4b implement; 4a ช่วยงานตรวจรูปแบบ |
| Effort throttle | เริ่ม 4b/high, ลดเมื่อ verify ง่าย, เพิ่มเมื่อ ambiguity หรือ downside สูง |
| Session batching | รวมคำถาม architecture 5-10 ข้อก่อนเรียก 4c แพง |
| Context compression | ใช้ `context-compaction.md` ก่อนสลับ model หรือก่อนส่งต่อ agent |

## Project Phase Template

| Phase | Model tier | Output ที่ต้องได้ |
|---|---|---|
| Phase A - Architect | 4c `max` หรือ `xhigh` one-shot | spec, constraints, risk register, test strategy, chunk plan |
| Phase B - Workhorse | 4b `high` หรือ `medium` | tests, implementation, docs, focused commits |
| Phase C - Hybrid | 4c `medium` เฉพาะคำถามยาก แล้วกลับ 4b | decision note สั้นและ patch ที่อ้าง test ได้ |
| Phase D - Critical review | 4c `low` | bug/risk list, missing tests, go/no-go |

Trading caveat: ก่อน strategy ต้องออกแบบ risk safeguards ก่อน เช่น daily loss limit, position cap, circuit breaker, audit log, และ rollback. งานที่แตะเงินจริงห้ามเริ่มจาก optimization หรือ profit logic.

## Budget Policy หลัง 2026-06-22

วันที่ 2026-06-22 เป็น operational note เฉพาะบัญชีของ user ตาม source page ไม่ใช่ข้อเท็จจริงสากล. หลังวันนั้นให้จำกัด Fable/4c เป็น 2-3 architecture sessions ต่อสัปดาห์ เว้นแต่งานมี downside สูงหรือเป็น blocker ของหลาย chunk.

## Platform Equivalents

| Platform | เลือก model/tier อย่างไร |
|---|---|
| Claude Code | ใช้ `/model` หรือ session picker; บันทึก decision ใน handoff/commit เมื่อสลับ tier |
| Codex | ใช้ model picker ของ Codex; protocol นี้เป็น behavior guide จาก AGENTS.md |
| Gemini CLI | ใช้ `-m` หรือ config ที่ platform รองรับ; ถ้าเป็น lookup ให้กลับไป `delegation.md` ก่อน |
| Cursor/Windsurf/Cline | ใช้ model picker ใน IDE; โหลด AGENTS.md เป็น always-loaded rule |
| GitHub Copilot/Aider | ใช้ config/model option ของ tool; ต้องยังผ่าน test-first และ handoff protocol |

## Decision Checklist

1. งานนี้ทำได้ด้วย Level -1 ถึง Level 3 ไหม ถ้าได้ให้ใช้ `delegation.md`.
2. ถ้าต้อง Level 4 ให้เริ่ม 4b เป็น default.
3. ถ้ามี spec ชัดและตรวจผลง่าย ให้ลดเป็น 4a.
4. ถ้าเป็น architecture, trading risk, irreversible decision, หรือ fail root-cause 2 รอบ ให้ขึ้น 4c.
5. เลือก effort ต่ำสุดที่ยังรักษาคุณภาพได้.
6. ถ้าจะสลับ model ให้ compress context ไม่เกิน 500 tokens และชี้ไฟล์ source-of-truth.
7. หลังจบ architect phase ให้ลดกลับ 4b เสมอ.

## Handoff Note Template

```md
## Model-Cost Switching

- Current tier: 4b Sonnet-class default
- Escalation used: none
- Next escalation trigger: architecture blocker, trading risk, or repeated root-cause failure
- Context to load: wiki/context/wiki-overview.md, docs/protocols/model-switching.md, <task-specific files>
- Last completed chunk: <chunk-id>
- Next chunk: <chunk-id>
```
