---
type: source
title: "การเริ่มต้นใช้งานชิป Espressif ESP32-S3 - IoT Engineering Education"
slug: esp32-s3-intro-thai
date_ingested: 2026-04-18
original_file: raw/การเริ่มต้นใช้งานชิป Espressif ESP32-S3 - IoT Engineering Education.md
tags: [esp32-s3, espressif, xtensa-lx7, usb-otg, ble5, pie, specs, thai]
---

# การเริ่มต้นใช้งานชิป Espressif ESP32-S3

**ประเภท**: article (ภาษาไทย)
**วันที่**: unknown
**ผู้เขียน**: RSP (iot-kmutnb.github.io — KMUTNB IoT Engineering)

## ประเด็นหลัก

1. **Xtensa LX7 dual-core 240MHz** — เร็วกว่า LX6 ของ ESP32 classic ประมาณ 40%
2. **PIE (Processor Instruction Extensions)** — 128-bit SIMD operations สำหรับ DSP/ML inference
3. **USB-OTG built-in** — USB host + device, ไม่ต้อง CH340/CP2102
4. **Bluetooth LE 5.0** — ไม่มี Classic BT (ต่างจาก ESP32 classic)
5. **Released December 2020** — ใช้ TSMC 40nm ultra-low-power process

## Chip Variants ของ ESP32-S3

| Variant | Flash | PSRAM |
|---------|-------|-------|
| ESP32-S3 | external only | ไม่มี |
| ESP32-S3R2 | external | 2MB |
| ESP32-S3R8 | external | 8MB |
| ESP32-S3R8V | external | 8MB (1.8V) |
| ESP32-S3FN8 | 8MB built-in | ไม่มี |
| ESP32-S3FH4R2 | 4MB built-in | 2MB |

**ใน Lab**: ESP32-S3-N16R8 = 16MB Flash external + 8MB PSRAM = รุ่น top ใน lab นี้

## เปรียบเทียบ ESP32-S2 vs ESP32-S3

| Feature | ESP32-S2 | ESP32-S3 (ใน lab) |
|---------|---------|-------------|
| CPU | LX7 single-core | LX7 dual-core |
| Bluetooth | ❌ | ✅ BLE 5.0 |
| SRAM | 320 KB | 512 KB |
| AI (PIE) | ✅ | ✅ |
| USB OTG | ✅ | ✅ |

## ข้อมูลที่น่าสนใจ

- PIE extension เหมาะมาก TinyML: keyword spotting, anomaly detection ใน sensor data
- N16R8 = ชื่อรุ่น: **N**16 (16MB flash, **N**OR flash) + **R**8 (8MB psRAM)

## ข้อโต้แย้งหรือความขัดแย้ง

ไม่มี — ยืนยัน specs ที่มีใน esp32-s3.md

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/esp32-s3]] — เพิ่ม PIE, chip variants table, LX7 details
