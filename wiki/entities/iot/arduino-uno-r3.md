---
type: entity
category: device
tags: [arduino, microcontroller, avr, atmega328p, beginner]
sources: [hardware-inventory-2026-04-18]
created: 2026-04-18
updated: 2026-04-18
---

# Arduino Uno R3 (CH340)

**ผู้ผลิต**: Arduino / Compatible (CH340 = Chinese clone)  
**รุ่นที่มีในแล็บ**: R3 CH340 (clone พร้อม Starter Kit)  
**สถานะใน Lab**: ✅ มีอยู่ × 1 (มาใน Starter Kit)

## ภาพรวม

Arduino Uno R3 เป็น development board คลาสสิกที่ใช้ ATmega328P (AVR 8-bit 16MHz) มาพร้อม ecosystem ขนาดใหญ่มาก รุ่น CH340 เป็น clone ที่ใช้ USB-to-Serial chip จีน (CH340G) แทน ATmega16U2 ของ official Arduino

## Specs หลัก

| คุณสมบัติ | รายละเอียด |
|----------|-----------|
| CPU | ATmega328P 8-bit 16MHz |
| Flash | 32KB |
| SRAM | **2KB** |
| EEPROM | 1KB |
| GPIO | 14 digital, 6 analog |
| PWM | 6 pins |
| USB | CH340G (ต้องลง driver บาง OS) |
| Logic | **5V** |
| Power | 5V USB หรือ 7-12V VIN |

## ข้อจำกัดสำคัญ

- **2KB RAM เท่านั้น** — ไม่พอสำหรับ WiFi, JSON parsing, หรือ String operations ซับซ้อน
- ไม่มี WiFi/Bluetooth built-in — ต้องต่อ module แยก (ESP-01, nRF24L01)
- 5V logic — ต้องระวังถ้าต่อกับ 3.3V module (เช่น ESP32) ต้องใช้ level shifter
- ช้ากว่า ESP32 มาก (~16MHz vs 240MHz)

## บทบาทใน Lab นี้

Arduino Uno เหมาะสำหรับ:
- เรียนรู้ basics (มาพร้อม starter kit tutorial)
- ทดสอบ sensor ง่ายๆ ที่ไม่ต้องการ WiFi
- ควบคุม actuator แบบ standalone (relay, servo, stepper)

**ไม่เหมาะสำหรับ** โปรเจ็ค IoT ที่ต้องการ WiFi/MQTT — ใช้ [[entities/iot/esp32]] แทน

## ความสัมพันธ์

- แข่งขันกับ: [[entities/iot/esp32]] (แรงกว่ามาก, มี WiFi), [[entities/iot/esp32-s3]]
- Sensor ใน Kit: [[entities/iot/dht11]], [[entities/iot/hc-sr501]]

## แหล่งข้อมูล

- [[sources/hardware-inventory-2026-04-18]] — มาพร้อม Arduino Starter Kit
