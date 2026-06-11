---
type: protocol
title: Model-Cost Switching
last_verified: 2026-06-12
tags: [ai-tools, model-switching, cost-management, swarm-intelligence]
sources:
  - ../../wiki/sources/claude-model-cost-switching-strategy-2026-06.md
  - https://api-docs.deepseek.com/quick_start/pricing
  - https://api-docs.deepseek.com/news/news260424
  - https://openrouter.ai/docs/api/api-reference/models/get-models
  - https://openrouter.ai/docs/guides/overview/models
---

# Model-Cost Switching

ใช้ protocol นี้เมื่อ task หลุดจาก Cost-First Pyramid Level -1 ถึง Level 3 แล้วต้องใช้ primary agent ระดับ Level 4 จริง ๆ. เอกสารนี้ไม่ได้แทน `delegation.md`; มันเป็น sub-ladder ภายใน Level 4 เพื่อเลือก model, effort, และจังหวะสลับ model ให้คุ้มต้นทุน. ก่อนเลือก route ทุกครั้งต้อง scout current model/pricing จาก runtime data ก่อน เพราะ model id, availability, และราคาเป็นข้อมูล volatile.

## ตำแหน่งใน Cost-First Pyramid

1. เริ่มที่ local search, graph, hook, `free-current`, `cheap-capable`, หรือ `platform-low-scout` ก่อนเสมอถ้างาน verifiable และไม่มีความเสี่ยงสูง.
2. ถ้างานต้องใช้ `platform-primary` เพราะต้องมี deep reasoning, source-of-truth wiki edits, architecture, trading risk, หรือ senior review ให้เข้า ladder นี้.
3. ค่า default ภายใน Level 4 คือ 4b role. ลดลงเป็น 4a เมื่อมี spec ชัดและตรวจผลได้. ขึ้นเป็น 4c เฉพาะเมื่อความยาวหรือความซับซ้อนคุ้ม premium 2-3x.

Related:
- `delegation.md` - Level 1-3 delegation ก่อนใช้ primary agent
- `context-compaction.md` - compress context ก่อนสลับ model
- `bot-trading-iron-law.md` - trading/risk safeguards
- `../../wiki/sources/claude-model-cost-switching-strategy-2026-06.md` - source page พร้อมข้อแก้ไขจาก chat ต้นทาง
- DeepSeek pricing - current provider price source
- OpenRouter Models API - current model availability source

## Dynamic Scout Gate

ก่อน route งานที่อาจใช้ model ภายนอกหรือ platform model ใด ๆ ให้ทำ scout current model/pricing ก่อน:

```bash
python3 scripts/model-scout-current.py
python3 scripts/model-router-policy.py --scout .tmp/model-scout-current.json
```

| Role | Meaning | Binding rule |
|---|---|---|
| `free-current` | free/current dynamic roster from live provider data | ใช้ก่อนเมื่อ task verify ง่าย |
| `cheap-capable` | cheapest capable paid route discovered at runtime | ใช้เมื่อ free-current ไม่พอหรือ rate limited |
| `platform-low-scout` | current low/default model of the active CLI/agent surface | ใช้ scan/search current model intel ก่อนให้ primary agent ลงแรง |
| `platform-primary` | current primary model in Codex/Claude/Cursor/etc. | ใช้หลัง scout บอกว่า lower tiers ไม่พอ |

model examples are dated examples only. DeepSeek V4 Flash/Pro, Qwen, Gemini Flash, Haiku, Sonnet, Opus/Fable หรือชื่อคล้ายกันห้ามเป็น binding default ใน policy. ถ้าจำเป็นต้องใส่ model id ใน script/config ให้เขียนชัดว่าเป็น seed only; replaced by scout.

## Level 4 Sub-Ladder

<a id="tier-4a"></a>
### 4a - ผู้ช่วย

ใช้ helper-class equivalent สำหรับงานที่มี answer shape ชัดเจนและ verify ง่าย เช่น boilerplate, parsing, formatting, classification, table cleanup, หรือแยก checklist จากข้อความยาว. ห้ามใช้เป็นตัวตัดสิน architecture หรือความเสี่ยงเงินจริง.

<a id="tier-4b"></a>
### 4b - ทีมช่าง (default)

ใช้ workhorse-class equivalent เป็น default ของงาน implementation: เขียนตาม spec, refactor scoped code, สร้าง tests, แก้ bug หลัง root cause ชัดแล้ว, integrate API, และเขียน wiki/doc ที่มี source ครบ.

<a id="tier-4c"></a>
### 4c - สถาปนิก

ใช้ architect-class equivalent เมื่อต้องการ one-shot architecture, algorithm design, trading strategy/risk design, ambiguous multi-system decision, หรือ critical review ที่ถ้าพลาดแล้วแพง. หลังได้ spec แล้วต้องลดกลับ 4b ทันที.

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
| Claude Code | ให้ current low/default model เป็น `platform-low-scout` ก่อน; ใช้ `/model` หรือ session picker เฉพาะเมื่อ scout บอกว่าต้องขึ้น `platform-primary` |
| Codex | ให้ current Codex CLI/model picker behavior เป็น `platform-low-scout`; protocol นี้เป็น behavior guide จาก AGENTS.md |
| Gemini CLI | ใช้ current Gemini default เป็น scout; ใช้ `-m` หรือ config เฉพาะเมื่อ scout/verification ระบุความจำเป็น |
| Cursor/Windsurf/Cline | ใช้ IDE model picker เป็น surface เท่านั้น; ห้าม bind model id ใน policy และต้อง verify ด้วย AGENTS.md |
| Antigravity/Manus/Devin/Perplexity/Groq | detect CLI/API availability ใน `scripts/model-scout-current.py`; ถ้า CLI ไม่อยู่ให้ใส่ manual verification matrix เป็น SKIP ไม่ใช่ FAIL |
| GitHub Copilot/Aider | ใช้ config/model option ของ tool; ต้องยังผ่าน test-first, scout-first, และ handoff protocol |

## Decision Checklist

1. งานนี้ทำได้ด้วย Level -1 ถึง Level 3 ไหม ถ้าได้ให้ใช้ `delegation.md`.
2. ก่อนเลือก model ให้ scout current model/pricing ด้วย `scripts/model-scout-current.py` หรืออ่าน `.tmp/model-router-policy.conf` ที่ generated หลัง scout แล้ว.
3. ถ้าต้อง Level 4 ให้เริ่ม 4b role เป็น default.
4. ถ้ามี spec ชัดและตรวจผลง่าย ให้ลดเป็น 4a.
5. ถ้าเป็น architecture, trading risk, irreversible decision, หรือ fail root-cause 2 รอบ ให้ขึ้น 4c.
6. เลือก effort ต่ำสุดที่ยังรักษาคุณภาพได้.
7. ถ้าจะสลับ model ให้ compress context ไม่เกิน 500 tokens และชี้ไฟล์ source-of-truth.
8. หลังจบ architect phase ให้ลดกลับ 4b เสมอ.

## Verification Matrix

Automated CLI probe:

```bash
bash scripts/verify-model-routing.sh
```

เกณฑ์ผ่าน: CLI platforms อย่างน้อย 2 ใน 3 (`claude`, `codex`, `gemini`) ต้องตอบถึง scout current model/pricing, dynamic/current model selection, ladder `4a/4b/4c`, และ no hardcoded model version ได้เองโดยไม่ต้อง prompt ชื่อ skill ตรง ๆ. CLI unavailable = SKIP ไม่ใช่ FAIL เว้นแต่เครื่องนี้คาดหวังว่าต้องมี CLI นั้น. รายงานถูกเขียนลง `exports/` ซึ่งเป็น review artifact ไม่ใช่ source-of-truth.

Manual GUI checklist:

| Platform | Probe | Expected | PASS/FAIL |
|---|---|---|---|
| Claude Desktop | ถาม "โปรเจ็คใหม่ multi-step ควรใช้ model อะไรบ้าง" โดยไม่เอ่ย pyramid/skill | อ้าง scout-first, role labels, 4a/4b/4c, และ no hardcoded model version |  |
| Cursor | เปิด repo แล้วถามคำถาม probe เดียวกัน | อ้าง `AGENTS.md`/protocol, scout-first, หรือ role labels ได้เอง |  |
| Windsurf | เปิด repo แล้วถามคำถาม probe เดียวกัน | อ้าง `AGENTS.md`/protocol, scout-first, หรือ role labels ได้เอง |  |

ความแน่นอนของ trigger เรียงจาก hook (deterministic) > always-loaded context (`AGENTS.md`/`CLAUDE.md`) > skill description. ถ้า probe FAIL ให้แก้ต้นเหตุที่ always-loaded context ก่อน แล้วค่อยปรับ skill description.

## Handoff Note Template

```md
## Model-Cost Switching

- Current tier: 4b workhorse role
- Scout status: <fresh scout timestamp or skipped reason>
- Current route roles: free-current -> cheap-capable -> platform-low-scout -> platform-primary
- Escalation used: none
- Next escalation trigger: architecture blocker, trading risk, or repeated root-cause failure
- Context to load: wiki/context/wiki-overview.md, docs/protocols/model-switching.md, <task-specific files>
- Last completed chunk: <chunk-id>
- Next chunk: <chunk-id>
```
