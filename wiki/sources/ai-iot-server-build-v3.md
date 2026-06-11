---
type: source
title: "Personal AI & IoT Server Build List (v3)"
slug: ai-iot-server-build-v3
date_ingested: 2026-05-05
original_file: raw/ai-iot-server-build-v3-final.md
source_type: ai-generated-build-spec
url: null
tags: [local-llm, pc-build, ai-server, iot-server, ryzen, rtx-4070-ti-super, ddr5, 24-7]
---

# Personal AI & IoT Server Build List (v3)

**ประเภท**: AI-generated build spec (PDF)
**วันที่อ้างอิง**: พฤษภาคม 2026
**ผู้เขียน**: AI Assistant (ไม่ระบุตัว)

## ประเด็นหลัก

1. **PC build ราคา ~98,500฿** — เน้นใช้งาน 24/7 สำหรับ Local LLM (70B+), IoT Monitor, AI Agent, Web Server
2. **CPU เน้นประหยัดไฟ** — Ryzen 7 9700X เปิด Eco Mode 65W TDP (จาก 105W default) เหมาะ 24/7
3. **RAM 128GB DDR5** — 4 แถว 32GB เพื่อรองรับ context ใหญ่ + multi-app
4. **GPU 16GB VRAM** — RTX 4070 Ti Super (16GB) เป็น sweet spot ราคา-ประสิทธิภาพ ปี 2026
5. **Storage แยก SSD/HDD** — 2TB NVMe สำหรับ OS+model, 8TB HDD NAS-grade สำหรับ IoT data
6. **เคสเล็ก SFX form factor** — Jonsbo TK-1 v2 + Noctua NH-L9x65 (low-profile cooler) เน้นเงียบ + วางในห้องนั่งเล่น

## สเปก (สรุป)

| Component | Model | ราคา (฿) |
|---|---|---|
| CPU | Ryzen 7 9700X (Eco 65W) | 12,000 |
| Mainboard | ASRock B860M Pro RS ⚠️ | 5,500 |
| RAM | 128GB DDR5-5600 (Kingston FURY Beast) | 20,000 |
| GPU | RTX 4070 Ti Super 16GB | 34,000 |
| SSD | Samsung 990 Pro 2TB NVMe Gen4 | 5,000 |
| HDD | 8TB WD Red Plus / Seagate IronWolf | 8,500 |
| Case | Jonsbo TK-1 v2 (กระจก 270°) | 5,000 |
| PSU | Cooler Master V750 SFX Gold | 5,000 |
| Cooler | Noctua NH-L9x65 (low-profile) | 3,500 |
| **รวม** | | **98,500** |

## ⚠️ ข้อโต้แย้งหรือความขัดแย้ง

### 1. Mainboard ระบุ chipset ผิด (Critical Error)

**ปัญหา**: PDF ระบุ **"ASRock B860M Pro RS"** — แต่ chipset **B860 เป็นของ Intel** (LGA1851 socket, ใช้กับ Core Ultra 200 series) ไม่ใช่ของ AMD

AMD Ryzen 7 9700X ใช้ **socket AM5** ซึ่งต้องคู่กับ chipset ตระกูล:
- A620 / B650 / B650E (รุ่นแรก ปี 2022)
- B850 / B850E / X870 / X870E (รุ่นใหม่ ปี 2024-2025)

**คาดว่าตั้งใจจะหมายถึง**: **ASRock B850M Pro RS** (AM5 chipset ชื่อใกล้เคียง) — น่าจะเป็น typo หรือ AI hallucination ของผู้สร้าง PDF

**ก่อนซื้อต้องตรวจสอบ**: ขอ verify ชื่อ board ที่ถูกต้องกับร้านอีกครั้ง — board ที่เลือกต้อง socket AM5 และมี 4 RAM slots รองรับ DDR5-5600+ (เช่น B850M Pro RS, B850 Tomahawk, X870 ในงบสูงขึ้น)

### 2. 16GB VRAM กับ Local LLM 70B+

PDF อ้าง use case "Local LLM 70B+" แต่:
- 70B model Q4 quantized ต้องใช้ VRAM ~40GB (เกิน 16GB VRAM ของ 4070 Ti Super มาก)
- 16GB VRAM เหมาะกับ 7B-14B Q4 (รันใน VRAM เต็ม), หรือ 32B แบบ partial offload
- รัน 70B จะต้อง **offload ไป system RAM (128GB)** ซึ่งทำได้แต่ช้ากว่ารันใน VRAM ล้วนๆ มาก (~2-5 tok/s แทนที่จะ 10+ tok/s)
- เทียบ Mac Studio M4 Max 64GB unified memory จะรัน 70B ได้ดีกว่าด้วย bandwidth สูง (ดู [[sources/local-llm-mac-mini-guide]])

**สรุป**: spec นี้เหมาะรัน 7B-32B ลื่นๆ + 70B แบบช้า — ถ้าต้องการ 70B เร็วๆ ควรพิจารณา GPU ที่มี VRAM สูงขึ้น (RTX 5090 32GB หรือ 2x GPU)

### 3. RAM 128GB อาจมากเกินจำเป็น

128GB DDR5 4 แถวที่ 5600MHz มักรันที่ความเร็วลดลง (DDR5 มี signal integrity issue กับ 4 DIMM) — Ryzen 9000 series มัก stable ที่ 5200-5600 ด้วย 4 แถว แต่บางเครื่อง drop ไป 4800

**ทางเลือก**: 64GB (32GB x 2) ลดราคา ~10,000฿ และได้ความเร็วเต็ม 5600+ — ถ้าใช้ 70B ผ่าน CPU offload จริงๆ ค่อย upgrade เพิ่ม

## Technician Checklist (สำคัญ)

1. **Memtest86 อย่างน้อย 4 ชั่วโมง** ใส่ครบ 4 แถว — สำคัญมากสำหรับ 24/7
2. **BIOS update + AMD Eco Mode 65W + XMP/EXPO 5200-5600MHz**
3. **GPU ความยาวไม่เกิน 270-280mm** — TK-1 v2 พื้นที่จำกัด, แนะนำรุ่น 2 พัดลม
4. **HDD ต้องเป็น NAS-grade (WD Red Plus, IronWolf)** — ออกแบบมาสำหรับ 24/7 workload
5. **Cable management** — เคสกระจกใส โชว์รอบด้าน
6. **Fan curve เงียบ** — รัน 24/7 ในห้องนั่งเล่น

## Cross-references

- เปรียบเทียบกับแนวทาง Mac → [[synthesis/local-llm-pc-vs-mac-2026]]
- พื้นฐาน Local LLM bandwidth/RAM rules → [[sources/local-llm-mac-mini-guide]]
- Routing pattern (local + cloud) → [[concepts/ai-tools/local-llm-routing]]
- ทางเลือกเริ่มต้นบน Pi5 → [[sources/ollama-pi5]], [[sources/rpi-ai-hat-plus-2-official]]

## หน้า Wiki ที่ได้รับการอัปเดต

- [[synthesis/local-llm-pc-vs-mac-2026]] — สร้างใหม่ (synthesis เปรียบเทียบ PC vs Mac)
- [[index-ai-tools]] — เพิ่ม source + synthesis ใหม่
