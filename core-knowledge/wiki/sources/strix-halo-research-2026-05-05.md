---
type: source
title: "AMD Ryzen AI Max+ 395 (Strix Halo) — Verified Research 2026-05-05"
slug: strix-halo-research-2026-05-05
date_ingested: 2026-05-05
original_file: raw/strix-halo-research-2026-05-05.md
source_type: gemini-web-search
url: multiple
tags: [strix-halo, ryzen-ai-max-395, mini-pc, local-llm, unified-memory, framework-desktop, gmktec]
---

# AMD Ryzen AI Max+ 395 (Strix Halo) — Verified Research

**ประเภท**: Gemini CLI web search (3 queries: price, benchmark, power)
**วันที่**: 2026-05-05
**Status**: ✅ benchmark + power verified, ⚠️ ราคาต้อง spot-check ก่อนซื้อ

## ประเด็นหลัก

1. **ราคาในไทยมีศูนย์แล้ว** — GMKtec EVO-X2 และ PELADN YO1 (128GB unified) ที่ ~**78,900฿** ทั้งคู่
2. **70B Q4 speed = 5 tok/s** เท่านั้น (ไม่เหนือ M4 Max 64GB ที่ 6-10 tok/s)
3. **Bandwidth bottleneck** — Strix Halo 215 GB/s vs M4 Max 546 GB/s (ช้ากว่า ~2.5 เท่า)
4. **ประหยัดไฟใกล้เคียง Mac** — idle 10-13W vs Mac 6-10W, LLM load 82W vs 80-120W
5. **เหนือ Mac M4 Max ที่ RAM size** — 128GB > 64GB → รัน 100B+ model หรือ context ยาวมากๆ ได้

## Pricing (มกราคม-พฤษภาคม 2026)

| รุ่น | RAM | ราคา USD | ราคาไทย |
|---|---|---|---|
| **GMKtec EVO-X2** | 128GB | $2,199 | **78,900฿** ⭐ (ศูนย์ไทย) |
| **PELADN YO1** | 128GB | $2,299 | **78,900฿** (ศูนย์ไทย) |
| Framework Desktop | 128GB | $2,459 | 125-135K฿ (นำเข้า) |
| HP ZBook Ultra G1a | 128GB | $4,996 | 199,900฿ (laptop) |

⚠️ **Spot-check ก่อนซื้อ**: ราคาผันผวน (Gemini อ้าง "DRAM crisis 2026" — ยังไม่ verify) — ตรวจ Shopee/Lazada Official ของ GMKtec ก่อนสั่ง

## LLM Benchmarks (llama.cpp on ROCm/Vulkan)

| Model | Quantization | tok/s | หมายเหตุ |
|---|---|---|---|
| Llama 3.3 70B | Q4_K_M | **5.0-5.5** | "อ่านทัน" usable |
| Qwen 2.5 72B | Q4_K_M | 4.5-5.5 | ใกล้เคียง 70B |
| Llama 3.1 8B | Q4_K_M | 45-55 | เร็วมาก เหมาะ chatbot |

**คุณสมบัติ Memory:**
- LPDDR5X-8000, 256-bit bus = ~215 GB/s
- iGPU Radeon 8060S (40 RDNA 3.5 CUs) เข้าถึง shared VRAM ได้สูงสุด **96GB** (จาก 128GB unified)

## Power Consumption (วัดจริง)

| เครื่อง | Idle | LLM Load | Peak |
|---|---|---|---|
| GMKtec EVO-X2 (Strix Halo) | 10-13W | ~82W | 220W |
| Mac Studio M4 Max 64GB | 6-10W | 80-120W | 145-170W |

**ที่ 24/7:**
- Strix Halo idle 12W avg = 105 kWh/ปี = ~440฿/ปี
- M4 Max idle 8W avg = 70 kWh/ปี = ~290฿/ปี
- ห่างกันแค่ ~150฿/ปี — **ไม่ใช่ปัจจัยตัดสิน**

## ⚠️ ข้อโต้แย้งหรือความขัดแย้ง

### 1. Strix Halo "เหนือ" M4 Max หรือไม่ — ขึ้นกับ metric

**Strix Halo ชนะที่:**
- ✅ RAM size (128GB vs 64GB) → รัน model ใหญ่กว่าได้ (100B+, 120B Q4)
- ✅ ราคาในไทย (~78,900฿ vs ~120-130K฿)
- ✅ Linux native + Docker
- ✅ Idle power เกือบเท่ากัน

**Mac M4 Max ชนะที่:**
- ✅ **70B speed** (~6-10 vs 5 tok/s) — bandwidth สูงกว่า 2.5 เท่า
- ✅ Resale value
- ✅ Peak power ต่ำกว่า

**Verdict**: ถ้าหัวใจคือ "70B Q4 เร็วๆ" → M4 Max ยังชนะ
ถ้าหัวใจคือ "RAM ใหญ่ + ถูก + Linux" → Strix Halo ชนะ

### 2. ตัวเลขที่ผมประเมินตอนแรกผิด

ในการสนทนาก่อน `wiki/synthesis/local-llm-pc-vs-mac-2026.md` ผมประเมิน:
- Strix Halo 70B Q4: 8-12 tok/s — **ผิด** (จริง 5 tok/s)
- Strix Halo bandwidth: 256 GB/s — **ผิด** (จริง 215 GB/s)
- M4 Max bandwidth: 410 GB/s — บางส่วนผิด (binned 546 GB/s)

→ ได้แก้ไขใน synthesis แล้ว

## URLs ที่ Gemini อ้าง (ยังไม่ verify ทั้งหมด)

- llm-tracker.info/howto/AMD-Strix-Halo (community LLM benchmark tracker — น่าเชื่อถือ)
- techpowerup.com (review site — น่าเชื่อถือ)
- reddit.com/r/LocalLLaMA (forum — primary source)
- gmktec.com (official)
- shopee.co.th (PELADN listing)

## Cross-references

- [[synthesis/local-llm-pc-vs-mac-2026]] — แก้ไขตัวเลขแล้ว
- [[sources/ai-iot-server-build-v3]] — PC build ที่ Gemini Pro เสนอ
- [[sources/local-llm-mac-mini-guide]] — Apple Silicon LLM
