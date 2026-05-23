---
type: entity
category: device
tags: [sensor, load-cell, strain-gauge, weight, hx711]
sources: [esp32-hx711-randomnerd]
created: 2026-04-18
updated: 2026-04-18
---

# Load Cell (Strain Gauge)

**ประเภท**: Weight Sensor (Analog)  
**สถานะใน Lab**: ❌ ยังไม่มี  
**ราคาประมาณ**: ~$2-10 ขึ้นกับ capacity (1kg / 5kg / 50kg)  
**ใช้คู่กับ**: [[entities/iot/hx711]] (ADC amplifier บังคับ)

## ภาพรวม

Load cell คือ transducer แปลงแรงกด/น้ำหนักเป็นสัญญาณไฟฟ้า โดยใช้ strain gauge (ตัวต้านทานที่เปลี่ยนค่าตามแรงที่กระทำ) สัญญาณออกมาเป็น mV ต้องต่อผ่าน [[entities/iot/hx711]] ก่อนเชื่อมต่อ microcontroller

## ประเภทที่นิยมใน IoT

| ประเภท | Capacity | ใช้สำหรับ |
|--------|---------|---------|
| Single point (bar) | 1kg, 5kg, 10kg | ตาชั่งในครัว, กล่องเล็ก |
| S-type | 50kg, 100kg | ถังขยะ, ถังน้ำ, ถังเชื้อเพลิง |
| Platform / Beam | 50-500kg | ถังอุตสาหกรรม |

## Wiring (4 สาย)

| สี | Pin HX711 | ความหมาย |
|----|----------|---------|
| Red | E+ | Excitation + |
| Black | E- | Excitation – |
| Green | A+ | Signal + |
| White | A- | Signal – |

> บางผู้ผลิตใช้สีต่าง — ตรวจสอบ datasheet ก่อนต่อสายทุกครั้ง

## การใช้งานใน IoT (Use Cases)

**น้ำหนักขยะ**:
- Load cell 50kg ใต้ถังขยะ
- ESP32 + HX711 วัดน้ำหนักทุก X นาที
- MQTT publish → Node-RED → แจ้งเตือนเมื่อถังเต็ม (เช่น > 80% capacity)

**ถังน้ำมัน/น้ำ**:
- ทางเลือกแทน ultrasonic เมื่อถัง geometry ไม่สม่ำเสมอ
- ชั่งน้ำหนักถังรวม แล้วลบน้ำหนักถังเปล่า

## ข้อดี / ข้อเสีย

| ข้อดี | ข้อเสีย |
|-------|---------|
| วัดได้แม่นยำ (±0.1%) | ต้องติดตั้งให้น้ำหนักกระจายสม่ำเสมอ |
| ทนทาน, ไม่มีชิ้นส่วนเคลื่อนไหว | ต้อง calibrate ทุกครั้ง |
| ราคาถูก | สัญญาณ mV ต้องการ HX711 เสมอ |
| ไม่กระทบจาก shape ของถัง | อุณหภูมิกระทบความแม่นยำ |

## ความสัมพันธ์

- ต้องใช้คู่กับ: [[entities/iot/hx711]] — ADC amplifier
- MCU: [[entities/iot/esp32]]
- Protocol: [[entities/iot/mqtt-protocol]]

## แหล่งข้อมูล

- [[sources/esp32-hx711-randomnerd]] — wiring, calibration guide ครบถ้วน
