---
type: entity
category: device
tags: [esp32-c6, microcontroller, wifi6, ble5, thread, zigbee, espressif, edge-ai, iot-core]
sources: [iot-edge-ai-esp32-c6-2026]
created: 2026-05-13
updated: 2026-05-13
last_verified: 2026-05-13
verify_tool: training
---

# ESP32-C6

**ผู้ผลิต**: Espressif Systems  
**สถานะใน Lab**: ❌ ยังไม่มีในแล็บ (reference only)

## ภาพรวม

ESP32-C6 เป็น MCU จาก Espressif ที่ออกแบบมาเพื่อการเชื่อมต่อไร้สายสมัยใหม่ เป็นรุ่นแรกในตระกูล ESP32 ที่รองรับ **WiFi 6 (802.11ax)**, **BLE 5.0**, และ **Thread/Zigbee (IEEE 802.15.4)** ในชิปเดียว ใช้ CPU RISC-V single-core แทน Xtensa [training]

## Specs หลัก [training]

| คุณสมบัติ | รายละเอียด |
|----------|-----------|
| CPU | RISC-V single-core 160MHz |
| RAM | 512KB SRAM |
| Flash | 4MB (มาตรฐาน) |
| WiFi | **802.11ax (WiFi 6)** 2.4GHz |
| Bluetooth | **BLE 5.0** |
| Sub-GHz | **Thread / Zigbee** (IEEE 802.15.4) |
| GPIO | 30 pins |
| ADC | 7ch 12-bit |
| Logic level | 3.3V |
| Deep sleep current | ~5µA |

## จุดเด่นเทียบกับ ESP32 classic

| ด้าน | ESP32 classic | ESP32-C6 |
|------|--------------|----------|
| WiFi standard | 802.11 b/g/n | **802.11ax (WiFi 6)** |
| Bluetooth | BT 4.2 + BLE | **BLE 5.0 เท่านั้น** |
| Thread/Zigbee | ❌ | ✅ IEEE 802.15.4 |
| CPU | Xtensa LX6 dual-core | RISC-V single-core |
| ML workload | ปานกลาง | ปานกลาง (ไม่มี PSRAM) |
| ราคา | ถูก | ใกล้เคียงกัน |

## การใช้งานใน IoT

- **Smart Home gateway**: รองรับ Matter/Thread ทำให้ควบคุมอุปกรณ์ Matter-compatible ได้โดยตรง
- **Edge AI gateway**: รับข้อมูลจาก LoRa sensor nodes → วิเคราะห์ด้วย TinyML on-device → สั่ง actuator
- **Smart Farm**: เป็น gateway กลาง รับ soil moisture ผ่าน LoRa → Edge AI ตัดสินใจ → เปิด Relay วาล์วน้ำ → แจ้งเตือนผ่าน WiFi 6
- **WiFi 6 environment**: เหมาะกับสภาพแวดล้อมที่มี congestion (กล้องวงจรปิด, อุปกรณ์หลายชิ้น) เพราะ OFDMA ลด interference

## TinyML บน ESP32-C6

แม้จะไม่มี PSRAM เหมือน ESP32-S3 แต่ ESP32-C6 รัน TinyML สำหรับงานเบาได้:
- Anomaly detection บนข้อมูล sensor (vibration, temperature pattern)
- Keyword spotting แบบเบา
- Classification จากค่า sensor ไม่กี่ channel

สำหรับ model ขนาดใหญ่กว่า → แนะนำ [[entities/iot/esp32-s3]] (8MB PSRAM)

## ความสัมพันธ์

- รุ่นพี่น้อง: [[entities/iot/esp32]] (classic), [[entities/iot/esp32-s3]] (ML workload สูง)
- Thread/Zigbee ecosystem: Matter standard (cross-platform IoT)
- ใช้ร่วมกับ: [[entities/iot/dx-lr02-lora]] (LoRa gateway), [[entities/iot/mqtt-protocol]]
- ML on-device: [[concepts/iot/tinyml]]
- Use case: Smart Farm ด้วย LoRa + Edge AI

## แหล่งข้อมูล

- [[sources/iot-edge-ai-esp32-c6-2026]] — overview architecture + Smart Farm example
- [Espressif official](https://www.espressif.com/en/products/socs/esp32-c6) — product page
