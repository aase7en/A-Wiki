---
type: source
title: "LoRa - Getting Started with Arduino, ESP32 & Pico"
slug: lora-getting-started-dronebot
date_ingested: 2026-04-18
original_file: raw/LoRa - Getting Started with Arduino, ESP32 & Pico.md
tags: [lora, arduino, esp32, raspberry-pi-pico, css, sx1276, practical]
---

# LoRa - Getting Started with Arduino, ESP32 & Pico

**ประเภท**: tutorial + video
**วันที่**: 2023-09-11
**ผู้เขียน**: DroneBot Workshop

## ประเด็นหลัก

1. **CSS (Chirp Spread Spectrum)**: LoRa ส่งสัญญาณเป็น frequency sweep (chirp) — ทนทาน interference, รับสัญญาณอ่อนได้
2. **Bandwidth**: 300–50,000 bps — เทียบเท่า dial-up modem (เหมาะ sensor เท่านั้น)
3. **LoRa vs alternatives**: WiFi/BLE range จำกัด, Cellular ราคาแพง → LoRa คือ sweet spot สำหรับ small IoT data
4. **SX1276 chip ครอบคลุม**: 137–1020 MHz, ใช้ SPI interface
5. **ครอบคลุม 3 boards**: Arduino, ESP32, Raspberry Pi Pico — ใช้ library เดียวกัน

## Technical Specs (CSS)

| Parameter | Value |
|-----------|-------|
| Modulation | Chirp Spread Spectrum (CSS) |
| Bandwidth | 300–50,000 bps |
| Sensitivity | ถึง -148dBm (SX1276) |
| Frequency range | 137–1020 MHz (SX1276) |
| Interface | SPI |

## ข้อมูลที่น่าสนใจ

- "Chirp" = สัญญาณที่เปลี่ยน frequency จาก low→high หรือ high→low อย่างต่อเนื่อง
- สาเหตุที่ทน interference: chirp ที่เหมือนกันเท่านั้นที่ decode ได้ — noise ไม่เป็น chirp
- ราคา LoRa module ถูกมาก (~$5 สำหรับ RFM95)

## ข้อโต้แย้งหรือความขัดแย้ง

ไม่มี — ยืนยัน technical details ของ lora.md ที่มีอยู่แล้ว

## หน้า Wiki ที่ได้รับการอัปเดต

- [[concepts/iot/lora]] — เพิ่ม CSS technical detail
- [[entities/iot/rfm95-sx1276]] — เพิ่ม SX1276 specs
