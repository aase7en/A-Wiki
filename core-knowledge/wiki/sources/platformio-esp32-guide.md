---
type: source
title: "Create an ESP32 Project With PlatformIO: A Guide for Beginners"
slug: platformio-esp32-guide
date_ingested: 2026-04-18
original_file: raw/Create an ESP32 Project With PlatformIO An Guide for Beginners.md
tags: [platformio, esp32, vscode, ide, cmake, dht, firmware]
---

# Create an ESP32 Project With PlatformIO: A Guide for Beginners

**ประเภท**: tutorial
**วันที่**: 2024-10-07
**ผู้เขียน**: Riccardo Medda (Elektor Magazine)

## ประเด็นหลัก

1. **PlatformIO คือ plugin ของ VS Code** — ไม่ใช่ standalone IDE แต่รันบน VSCode, Atom, Eclipse
2. **ดีกว่า Arduino IDE สำหรับ professional**: CMake build system, dependency management, multi-board support
3. **ตัวอย่าง project**: ESP32 + DHT sensor (humidity/temperature) — ตรงกับ use case ของเรา
4. **`platformio.ini`**: config file กำหนด board, framework, library dependencies
5. **ข้อดี**: intellisense ดีกว่า, version control ง่ายกว่า, CI/CD integration

## เปรียบเทียบ Arduino IDE vs PlatformIO

| หัวข้อ | Arduino IDE 2 | PlatformIO (VSCode) |
|--------|--------------|---------------------|
| ง่าย beginner | ✅ มาก | ⬜ ต้องตั้งค่า |
| Autocomplete / IntelliSense | ⬜ จำกัด | ✅ เต็มที่ |
| Dependency management | ⬜ manual | ✅ platformio.ini |
| Multi-platform | ⬜ จำกัด | ✅ เต็มที่ |
| Debug (hardware debug) | ⬜ จำกัด | ✅ รองรับ JTAG |
| Community | ✅ ใหญ่ | ✅ ใหญ่ (professional) |
| เหมาะกับ | เรียนรู้, prototype | production, team, CI/CD |

## platformio.ini ตัวอย่าง

```ini
[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino
lib_deps =
    adafruit/DHT sensor library
    knolleary/PubSubClient
```

## ข้อมูลที่น่าสนใจ

- PlatformIO จัดการ library versions อัตโนมัติ — ไม่ต้องกังวล compatibility
- ใช้ร่วมกับ Git ได้ดีมาก — `platformio.ini` commit ลง repo

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/platformio]] — สร้างใหม่
- [[entities/iot/arduino-ide]] — เปรียบเทียบ
