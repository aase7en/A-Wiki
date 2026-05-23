---
type: entity
category: platform
tags: [platformio, vscode, ide, cmake, esp32, professional, dependency-management]
sources: [platformio-esp32-guide]
created: 2026-04-18
updated: 2026-04-18
---

# PlatformIO

**ผู้พัฒนา**: PlatformIO Labs
**License**: Open source (Community) / Commercial (Pro)
**รูปแบบ**: Plugin สำหรับ VS Code (ไม่ใช่ standalone IDE)

## ภาพรวม

PlatformIO เป็น ecosystem สำหรับ embedded development ที่ทรงพลังกว่า Arduino IDE มีระบบ dependency management, multi-environment, และ IntelliSense เต็มรูปแบบ เหมาะสำหรับโปรเจ็คขนาดใหญ่หรือ team development

## คุณสมบัติหลัก

- **platformio.ini**: config file กำหนด board, framework, library ทั้งหมด
- **Library management**: ล็อค version library ได้ เหมาะ reproducible build
- **Multi-environment**: build สำหรับ ESP32 classic + ESP32-S3 ในไฟล์เดียว
- **Hardware debugger**: รองรับ JTAG debug ผ่าน VS Code
- **CI/CD**: integrate กับ GitHub Actions ได้ตรง

## ตัวอย่าง platformio.ini

```ini
[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino
monitor_speed = 115200
lib_deps =
    adafruit/DHT sensor library@^1.4.6
    knolleary/PubSubClient@^2.8
    sandeepmistry/LoRa@^0.8.0

[env:esp32-s3]
platform = espressif32
board = esp32-s3-devkitc-1
framework = arduino
```

## ความสัมพันธ์

- ทางเลือก: [[entities/iot/arduino-ide]] (ง่ายกว่า), [[entities/iot/esp-idf]] (native)
- ใช้กับ: [[entities/iot/esp32]], [[entities/iot/esp32-s3]]

## แหล่งข้อมูล

- [[sources/platformio-esp32-guide]] — beginner guide + DHT project
