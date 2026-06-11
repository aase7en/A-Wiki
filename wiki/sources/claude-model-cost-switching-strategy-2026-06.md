---
type: source
title: "การวางแผนใช้ model Fable 5 สำหรับ game project ที่มี trading integration (claude.ai shared chat)"
slug: claude-model-cost-switching-strategy-2026-06
date_ingested: 2026-06-12
original_file: raw/claude-model-cost-switching-strategy-2026-06.md
tags: [ai-tools, model-switching, token-cost, fable-5, claude, cost-management]
---

# การวางแผนสลับ model + บริหาร token cost (Fable 5 / Sonnet / Haiku)

**ประเภท**: article (claude.ai shared chat)
**วันที่**: 2026-06 (shared link captured 2026-06-12)
**ผู้เขียน**: Claude (claude.ai) ตอบคำถาม user เรื่องการ build game + trading project ด้วย model ผสม

## ประเด็นหลัก

1. **Fable 5 = model แพงสุดในตลาด** ($10/M input, $50/M output ≈ 2× Opus 4.8) แต่ lead เหนือ model อื่นโตตามความยาว/ความซับซ้อนของ task → คุ้มเฉพาะงานออกแบบใหญ่ ไม่คุ้มงานสั้นซ้ำๆ
2. **บทบาทสามชั้น**: Fable 5 = สถาปนิก (ออกแบบ architecture/strategy ครั้งเดียว) · Sonnet = ทีมช่าง (implement ตาม spec) · Haiku = ผู้ช่วย (boilerplate/parsing)
3. **5 หลักการบริหาร cost**: (1) prompt caching ของ Master Context Document = หัวใจ (อ่าน cache ลด ~90%) (2) ใช้ model แพงเป็นนักออกแบบ ไม่ใช่คนพิมพ์โค้ด (3) effort parameter เป็นคันเร่งต้นทุน (4) session batching เตรียม 5-10 คำถามถามรวดเดียว (5) compress context ≤500 tokens ก่อนสลับ model (ลด input 80%+)
4. **Phase plan template**: Architect (Fable max) → Workhorse (Sonnet) → Hybrid (Fable medium ออกแบบ algorithm + Sonnet implement) → Critical review (Fable low)
5. **Trading caveat**: ให้ model แพงออกแบบ risk safeguards (daily loss limit, position cap, circuit breaker) ก่อน strategy เสมอ — bug ที่นี่คือเงินจริง
6. **Budget policy**: subscription ใช้ Fable ฟรีถึง 2026-06-22 หลังจากนั้นจำกัด "Fable budget sessions" 2-3 ครั้ง/สัปดาห์

## ข้อมูลที่น่าสนใจ / สถิติ

- ราคา (verified 2026-06-12 กับ Claude API docs): Fable 5 = $10/$50, Opus 4.8 = $5/$25, Sonnet 4.6 = $3/$15, Haiku 4.5 = $1/$5 ต่อ MTok; Batch API ลด 50%
- Cache read ≈ 0.1× ราคา input (ลด 90% จริง) แต่ cache **write = 1.25×** (TTL 5 นาที) หรือ 2× (TTL 1 ชม.) + prefix ขั้นต่ำ 2048 tokens บน Fable 5
- Fable 5 ตัด temperature/top_p ออก ใช้ `effort` ใน `output_config` แทน

## ข้อโต้แย้งหรือความขัดแย้ง

- **effort มี 5 ระดับ ไม่ใช่ 3**: ค่าจริงคือ `low | medium | high (default) | xhigh | max` (verified กับ API docs 2026-06-12) — chat ต้นทางพูดถึงแค่ low/medium/max
- **เปอร์เซ็นต์ token ต่อ effort ("low ≈40%, medium ≈65% ของ max") ไม่มีในเอกสารทางการ** — unverified, เก็บไว้เฉพาะใน raw/ ห้ามอ้างต่อใน protocol
- วันหมดเขต 2026-06-22 เป็นเงื่อนไขเฉพาะบัญชี subscription ของ user ไม่ใช่ข้อเท็จจริงสากล — บันทึกเป็น operational note พร้อมวันที่

## หน้า Wiki ที่ได้รับการอัปเดต

- [[context/model-roster]] — เพิ่ม section "Primary-Model Ladder (Pyramid Level 4)"
- `docs/protocols/model-switching.md` — protocol ฉบับปฏิบัติ (ฝังเป็น skill `model-cost-switching`)
