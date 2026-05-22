---
type: source
title: "Arduino IDE คืออะไร วิธีติดตั้งและใช้งาน ESP32 และ Arduino ปี2025"
slug: arduino-ide-esp32-setup
date_ingested: 2026-04-18
original_file: raw/Arduino IDE คืออะไร วิธีติดตั้งและใช้งาน ESP32 และ Arduino ปี2025.md
tags: [arduino-ide, esp32, setup, development-tool, board-manager, serial-monitor]
---

# Arduino IDE คืออะไร วิธีติดตั้งและใช้งาน ESP32 (2025)

**ประเภท**: tutorial (ภาษาไทย)
**วันที่**: 2025-08-12
**ผู้เขียน**: deva_diy (devadiy.com)

## ประเด็นหลัก

1. **Arduino IDE 2.x** — รุ่นใหม่แนะนำ, เร็วกว่า 1.x, มี autocomplete และ debug
2. **ESP32 Board Manager URL**: `https://espressif.github.io/arduino-esp32/package_esp32_index.json`
3. **Serial Monitor** — ใช้ debug ระหว่าง develop, แสดง Serial.print() output real-time
4. **Board Manager** — เพิ่ม ESP32 support ผ่าน Preferences → Additional URLs
5. **Library Manager** — ติดตั้ง library เช่น PubSubClient, DHT, LoRa ได้โดยตรงใน IDE

## วิธีเพิ่ม ESP32 Board

```
Arduino IDE → File → Preferences → Additional Boards Manager URLs
เพิ่ม: https://espressif.github.io/arduino-esp32/package_esp32_index.json
→ Tools → Board → Boards Manager → ค้นหา "esp32" → Install
→ Tools → Board → เลือก "ESP32 Dev Module"
```

## บอร์ดที่รองรับ

- Arduino UNO / Nano / Mega (built-in)
- ESP32 DevKit, WROOM, WROVER (เพิ่ม Board Manager)
- ESP32-S3, ESP32-C3 (เพิ่ม Board Manager เดียวกัน)
- ESP8266 (เพิ่ม Board Manager URL แยก)

## ข้อมูลที่น่าสนใจ

- Arduino IDE 2 ใช้ Monaco editor เดียวกับ VS Code
- Serial Plotter ดู sensor data เป็น graph real-time ได้ทันที — ใช้ debug DHT11 ได้ดี

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/arduino-ide]] — สร้างใหม่
- [[entities/iot/esp32]] — เพิ่ม Board Manager URL
