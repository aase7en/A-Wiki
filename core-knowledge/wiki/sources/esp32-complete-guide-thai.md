---
type: source
title: "ESP32 คู่มือฉบับสมบูรณ์ พร้อมสอนติดตั้งและใช้งาน"
slug: esp32-complete-guide-thai
date_ingested: 2026-04-18
original_file: raw/ESP32 คู่มือฉบับสมบูรณ์ พร้อมสอนติดตั้งและใช้งาน.md
tags: [esp32, thai, overview, specs, deep-sleep, iot, smart-farm]
---

# ESP32 คู่มือฉบับสมบูรณ์ (Thai)

**ประเภท**: article (ภาษาไทย)
**วันที่**: 2025-12-08
**ผู้เผยแพร่**: Global Byte Shop (globalbyteshop.com)

## ประเด็นหลัก

1. **ESP32 = SoC** — รวม Dual-core CPU + WiFi + Bluetooth + peripherals ในชิปเดียว (ไม่ใช่แค่ MCU)
2. **Dual-core Xtensa LX6 240MHz** — สามารถรัน 2 tasks พร้อมกันได้ (เช่น LoRa receive + WiFi publish)
3. **Touch Pins** — ESP32 classic มี capacitive touch sensor 10 pins (T0-T9)
4. **Deep Sleep ~10µA** — ประหยัดพลังงานสูง เหมาะ battery-powered sensor node
5. **Arduino IDE compatible** — เพิ่ม ESP32 Board Manager ผ่าน JSON URL

## Key Specs

| คุณสมบัติ | รายละเอียด |
|----------|-----------|
| CPU | Xtensa LX6 dual-core 240MHz |
| RAM | 512KB SRAM |
| Flash | ขึ้นอยู่กับรุ่น (4MB–16MB external) |
| WiFi | 802.11 b/g/n 2.4GHz |
| Bluetooth | Classic 4.2 + BLE |
| Touch pins | 10 pins capacitive |
| Deep sleep | ~10µA |
| ADC | 18 channels 12-bit |
| UART/SPI/I2C | 3/4/2 |

## Arduino Board Manager URL

```
https://espressif.github.io/arduino-esp32/package_esp32_index.json
```

## ข้อมูลที่น่าสนใจ

- ESP32 แรงกว่า Arduino UNO มาก — แต่ยังใช้ Arduino IDE ได้
- เหมาะ Smart Home, Smart Farm ที่ต้องการ WiFi + sensor พร้อมกัน
- ESP32-S3 คือรุ่นใหม่ที่แรงกว่า (Xtensa LX7, USB native, BLE 5.0)

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/esp32]] — ยืนยัน specs, เพิ่ม touch pin, deep sleep note
- [[entities/iot/arduino-ide]] — สร้างใหม่ (Board Manager URL)
