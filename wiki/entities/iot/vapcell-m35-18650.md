---
type: entity
category: device
tags: [power, 18650, battery, li-ion, portable]
sources: [hardware-inventory-2026-04-18]
created: 2026-04-18
updated: 2026-04-18
---

# Vapcell INR18650 M35

**ผู้ผลิต**: Vapcell  
**รุ่น**: INR18650 M35  
**สถานะใน Lab**: ✅ มีอยู่ × 2  
**ใช้คู่กับ**: [[entities/iot/18650-battery-shield]]

## ภาพรวม

แบตเตอรี่ลิเธียมไอออน ขนาด 18650 ความจุสูง 3500mAh เหมาะสำหรับ IoT project ที่ต้องการพลังงานต่อเนื่องนาน ใช้คู่กับ 18650 Battery Shield V3 เพื่อจ่ายไฟให้ ESP32 และอุปกรณ์ต่างๆ

## Specs หลัก

| คุณสมบัติ | ค่า |
|----------|-----|
| ความจุ | 3500mAh |
| แรงดันนอมินัล | 3.7V |
| Discharge สูงสุด (continuous) | 10A |
| Discharge สูงสุด (pulse) | 25A / 5 วินาที |
| ขนาด | 18mm × 65mm |

## การคำนวณ Runtime (กับ Battery Shield V3)

| การใช้งาน | กระแสเฉลี่ย | Runtime ประมาณ |
|----------|------------|--------------|
| ESP32 WiFi active | ~150mA | ~20 ชั่วโมง |
| ESP32 + DHT11 ทุก 30s | ~5mA | ~500 ชั่วโมง |
| ESP32 deep sleep | ~10µA | หลายร้อยวัน |

(Runtime = ความจุ × efficiency 85% ÷ กระแสเฉลี่ย)

## ข้อควรระวัง

- ใส่ orientation ถูกทิศเสมอ — ใส่กลับทำ battery shield เสียได้
- ถ้าใช้ 2 ก้อนพร้อมกัน ต้องใช้ capacity และ charge cycle ใกล้เคียงกัน
- เก็บที่ charge ~50% ถ้าไม่ได้ใช้นาน

## ความสัมพันธ์

- ใช้กับ: [[entities/iot/18650-battery-shield]] — shield V3 รองรับ 1 ก้อน
- Power ให้: [[entities/iot/esp32]], [[entities/iot/esp32-s3]]

## แหล่งข้อมูล

- [[sources/hardware-inventory-2026-04-18]] — มีใน lab × 2
