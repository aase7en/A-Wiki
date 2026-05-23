---
type: entity
category: device
tags: [power, 18650, battery, boost-converter, portable]
sources: [hardware-inventory-2026-04-18]
created: 2026-04-18
updated: 2026-04-18
---

# 18650 Battery Shield V3

**รุ่น**: 18650 Battery Shield V3 (V1045)  
**สถานะใน Lab**: ✅ มีอยู่ × 2  
**ใช้คู่กับ**: [[entities/iot/vapcell-m35-18650]]

## ภาพรวม

Battery shield สำหรับ 18650 cell 1 ก้อน แปลง 3.7V เป็น 5V (boost) และ 3.3V (LDO) พร้อม USB-A output สำหรับชาร์จ device อื่น มี Micro-USB สำหรับชาร์จ battery

## Specs หลัก

| Output | Voltage | Current | ใช้สำหรับ |
|--------|---------|---------|----------|
| 5V rail | 5V | **4A max** | ESP32 VIN, อุปกรณ์ USB |
| 3V rail | 3.3V | 1A max | MCU 3.3V โดยตรง |
| USB-A | 5V | 4A | ชาร์จ/power อุปกรณ์ภายนอก |

**Input**: Micro-USB (ชาร์จ 18650)

## การคำนวณ Battery Life

กับ [[entities/iot/vapcell-m35-18650]] (3500mAh):
- ESP32 WiFi active: ~150mA avg → ประมาณ **~20 ชั่วโมง** (3500/150 × efficiency 85%)
- ESP32 deep sleep: ~10µA → ถ้า duty cycle 1% active → ประมาณ **หลายร้อยชั่วโมง**
- ESP32 + DHT11 polling ทุก 30s: avg ~5mA → ประมาณ **~500 ชั่วโมง**

## ข้อควรระวัง

- 18650 slot เดียว — ถ้าต้องการ runtime นาน ต้องหา shield 2-slot แทน
- มี on/off switch — สำคัญสำหรับ deployment จริง
- "Becareful + and -" ที่ silkscreen เตือน orientation ของ battery

## ความสัมพันธ์

- ใช้คู่กับ: Vapcell INR18650 M35 (ยังไม่มีหน้า)
- Power ให้: [[entities/iot/esp32]], [[entities/iot/esp32-s3]]

## แหล่งข้อมูล

- [[sources/hardware-inventory-2026-04-18]]
