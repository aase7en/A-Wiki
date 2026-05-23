---
type: entity
category: device
tags: [esp32-s3, microcontroller, wifi, bluetooth, espressif, usb-native, ai]
sources: [hardware-inventory-2026-04-18, esp32-s3-intro-thai]
created: 2026-04-18
updated: 2026-04-18
---

# ESP32-S3-N16R8

**ผู้ผลิต**: Espressif Systems  
**รุ่นที่มีในแล็บ**: ESP32-S3-N16R8 WROOM + Terminal Breakout (green PCB, 25.50mm width)  
**สถานะใน Lab**: ✅ มีอยู่ × 1

## ภาพรวม

ESP32-S3 เป็น MCU ที่แรงที่สุดใน lab นี้ มี USB OTG native (ไม่ต้องใช้ CH340/CP2102) และ vector instruction สำหรับ AI/ML inference บน edge รุ่น N16R8 หมายถึง 16MB Flash + 8MB PSRAM ซึ่งมากพอสำหรับงาน TinyML หรือ image processing เบาๆ

## Specs หลัก

| คุณสมบัติ | รายละเอียด |
|----------|-----------|
| CPU | Xtensa LX7 dual-core 240MHz |
| RAM | 512KB SRAM + **8MB PSRAM (SPIRAM)** |
| Flash | **16MB** |
| WiFi | 802.11 b/g/n 2.4GHz |
| Bluetooth | BLE 5.0 (ไม่มี Classic BT) |
| USB | **Native USB OTG** (ไม่ต้องใช้ USB-to-Serial chip) |
| GPIO | 45 pins |
| AI acceleration | vector instructions สำหรับ neural net |

## ข้อดีเหนือ ESP32 Classic

| | ESP32 | ESP32-S3 |
|-|-------|---------|
| CPU | LX6 240MHz | LX7 240MHz (เร็วกว่า ~40%) |
| PSRAM | ไม่มี (บางรุ่นมี 4MB) | **8MB** |
| Flash | 4MB | **16MB** |
| USB | ต้องใช้ CH340 | **Native USB** |
| BLE | 4.2 | **5.0** |
| AI | ไม่มี | vector instructions |

## การใช้งานใน IoT

- งานที่ต้องการ RAM มาก: web server, JSON parsing, image buffer
- TinyML: รันโมเดล เช่น keyword detection, anomaly detection
- USB device: appear as HID, CDC, MSC โดยไม่ต้องใช้ chip แปลง
- Firmware flash: ใช้ USB native โดยตรง (ไม่ต้องใช้ [[entities/iot/dx-smart-ttl]])

## ข้อควรระวัง

- USB native ใช้ GPIO19/20 — ห้ามใช้ GPIO นี้เป็น IO ปกติถ้า flash ผ่าน USB
- BLE 5.0 แต่ **ไม่มี Classic Bluetooth** — ถ้าต้องการ audio หรือ SPP ต้องใช้ ESP32 classic
- PSRAM ใช้ SPI bus ร่วม — อาจกระทบ throughput ถ้าใช้ SPI peripheral พร้อมกัน

## ความสัมพันธ์

- รุ่นเก่ากว่า: [[entities/iot/esp32]]
- ใช้งานโปรโตคอล: [[entities/iot/mqtt-protocol]]
- Sensor ที่ใช้ร่วมได้: [[entities/iot/dht11]], [[entities/iot/hc-sr501]]

## Chip Variants (ชื่อ decode)

N16R8 = **N**OR Flash 16MB + **R**AM (PSRAM) 8MB

| Part | Flash | PSRAM |
|------|-------|-------|
| ESP32-S3 | external | — |
| ESP32-S3R8 | external | 8MB |
| ESP32-S3FN8 | 8MB built-in | — |
| **ESP32-S3-N16R8** (ใน lab) | **16MB** | **8MB** |

## Development Environment

เหมือนกับ ESP32 classic — ใช้ Arduino IDE ผ่าน Board Manager เดียวกัน
Board: `ESP32S3 Dev Module`
ตั้งค่าเพิ่ม: Flash Size = 16MB, PSRAM = OPI PSRAM

## ความสัมพันธ์

- รุ่นเก่ากว่า: [[entities/iot/esp32]]
- ใช้งานโปรโตคอล: [[entities/iot/mqtt-protocol]]
- Sensor ที่ใช้ร่วมได้: [[entities/iot/dht11]], [[entities/iot/hc-sr501]]
- IDE: [[entities/iot/arduino-ide]], [[entities/iot/platformio]]

## แหล่งข้อมูล

- [[sources/hardware-inventory-2026-04-18]] — มีใน lab × 1 พร้อม terminal breakout สีเขียว
- [[sources/esp32-s3-intro-thai]] — specs ละเอียด, LX7, PIE, chip variants
