---
type: entity
category: device
tags: [sensor, pir, motion, hc-sr501, digital]
sources: [hardware-inventory-2026-04-18]
created: 2026-04-18
updated: 2026-04-18
---

# HC-SR501 PIR Motion Sensor

**สถานะใน Lab**: ✅ มีอยู่ × 1 (ใน Starter Kit)

## ภาพรวม

HC-SR501 เป็น Passive Infrared (PIR) sensor วัด motion ของสิ่งมีชีวิต (คน/สัตว์) จาก body heat ราคาถูกมาก output เป็น digital HIGH/LOW มี potentiometer ปรับ sensitivity และ delay

## Specs หลัก

| คุณสมบัติ | รายละเอียด |
|----------|-----------|
| Voltage | 5V–20V |
| Output | Digital HIGH (3.3V) เมื่อ detect |
| Range | สูงสุด 7m |
| Angle | 120° cone |
| Delay time | ปรับได้ 3s–5min |
| Sensitivity | ปรับได้ |
| Warm-up time | **~30 วินาที** หลัง power on |

## การใช้งานใน IoT

- Security alert: ส่ง notification เมื่อมีคนเข้า
- Smart lighting: เปิดไฟอัตโนมัติ
- Power saving: wake MCU เมื่อมีคน (ใช้กับ interrupt)

## ข้อควรระวัง

- ต้องรอ warm-up ~30 วินาทีหลัง power on — อย่า check output ทันที
- อ่าน output ผ่าน interrupt ดีกว่า polling
- แสงแดดหรือแหล่งความร้อนอื่นอาจ trigger false positive

## ความสัมพันธ์

- ใช้กับ: [[entities/iot/esp32]], [[entities/iot/arduino-uno-r3]]

## แหล่งข้อมูล

- [[sources/hardware-inventory-2026-04-18]]
