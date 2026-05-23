---
type: entity
category: device
tags: [usb, ttl, serial, uart, flash-tool, ch340, type-c]
sources: [hardware-inventory-2026-04-18]
created: 2026-04-18
updated: 2026-04-18
---

# DX-SMART USB-C to TTL (DX-PJ15-V1.1)

**ผู้ผลิต**: DX-SMART  
**รุ่น**: DX-PJ15-V1.1  
**สถานะใน Lab**: ✅ มีอยู่ × 2  
**Connector**: USB Type-C (host) → TTL header pins

## ภาพรวม

USB-to-TTL serial converter สำหรับ flash firmware และ debug serial กับ microcontroller ใช้งานง่าย เสียบ USB-C กับคอมพิวเตอร์ ฝั่ง TTL ต่อกับ TX/RX ของ MCU

## Pinout

| Pin | หน้าที่ |
|-----|--------|
| TX | ส่งจาก converter → RX ของ MCU |
| RX | รับจาก TX ของ MCU |
| NC | No connect |
| GND | Ground |
| 5V | จ่ายไฟ 5V ให้ MCU (ถ้าต้องการ) |
| 3V3 | จ่ายไฟ 3.3V ให้ MCU (ถ้าต้องการ) |
| GND | Ground (เพิ่ม) |

## การใช้งานใน IoT

ใช้หลักในสองกรณี:
1. **Flash firmware** — สำหรับ MCU ที่ไม่มี USB native เช่น ESP32 DevKit V1 (ต้องการ CH340 หรือ CP2102 บน board)
2. **Serial debug** — monitor Serial output จาก MCU ขณะ runtime

> **หมายเหตุ**: [[entities/iot/esp32-s3]] ไม่ต้องใช้ converter นี้ เพราะมี USB OTG native — flash ผ่าน USB-C ได้ตรงเลย

## ความสัมพันธ์

- ใช้กับ: [[entities/iot/esp32]] — flash ผ่าน UART
- ไม่จำเป็นสำหรับ: [[entities/iot/esp32-s3]] — มี USB native

## แหล่งข้อมูล

- [[sources/hardware-inventory-2026-04-18]] — มีใน lab × 2, ใช้สำหรับ flash/debug serial
