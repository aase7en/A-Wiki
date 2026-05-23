---
type: entity
category: device
tags: [sensor, ultrasonic, distance, level, hc-sr04]
sources: [hardware-inventory-2026-04-18, esp32-tank-level-mqtt]
created: 2026-04-18
updated: 2026-04-18
---

# HC-SR04

**ผู้ผลิต**: หลายยี่ห้อ (generic)  
**ประเภท**: Ultrasonic Distance Sensor  
**สถานะใน Lab**: ✅ มีอยู่ × 1 (ในชุด Arduino Starter Kit)  
**ราคาประมาณ**: ~$1-2

## ภาพรวม

HC-SR04 ใช้คลื่นเสียง ultrasonic วัดระยะห่างจากวัตถุ 2–400cm ใช้งานง่ายผ่าน Trigger/Echo pins นอกจาก distance measurement แล้วยังใช้ทำ **tank level monitoring** (น้ำ, น้ำมัน, เชื้อเพลิง) ได้โดยติดตั้งด้านบนถัง แล้วคำนวณระดับจากระยะที่วัดได้

## Specs หลัก

| คุณสมบัติ | ค่า |
|----------|-----|
| Range | 2–400cm |
| Accuracy | ±0.3cm |
| Angle | <15° |
| Supply | 5V |
| Trigger | 10µs pulse |
| Interface | Digital (Trigger + Echo) |

## Wiring กับ ESP32

| HC-SR04 | ESP32 |
|---------|-------|
| VCC | 5V (Vin) |
| GND | GND |
| TRIG | GPIO 4 |
| ECHO | GPIO 18 (ต้องใช้ voltage divider: 5V→3.3V) |

> **⚠️ Echo pin ส่งสัญญาณ 5V** — ต้องใช้ voltage divider (1kΩ + 2kΩ) หรือ level shifter ก่อนต่อกับ ESP32

## Tank Level Monitoring

```
[HC-SR04 ติดบนฝาถัง]
         ↓ วัดระยะ d (cm)
[ESP32 คำนวณ level]
   level% = (H_empty - d) / (H_empty - H_full) × 100
         ↓ MQTT publish
   topic: tank/level   payload: {"level": 73.5}
   topic: tank/status  payload: "normal"
```

**Captive Portal config** (จาก Voelk-IT project):
- ครั้งแรก ESP32 ทำตัวเป็น AP
- ผู้ใช้ connect และตั้งค่า WiFi, MQTT broker, ค่า empty/full distance ผ่าน web form
- ค่า config เก็บใน flash memory

## MQTT Topics

| Topic | Payload | คำอธิบาย |
|-------|---------|---------|
| `tank/level` | `73.5` | % เต็ม |
| `tank/status` | `"normal"` | สถานะ |
| `tank/lastupdate` | timestamp | อัปเดตล่าสุด |
| `tank/wificonnect` | timestamp | WiFi connect time |

## Use Cases ใน IoT

- **ถังน้ำมันเชื้อเพลิง** — วัดระดับน้ำมัน แจ้งเตือนเมื่อใกล้หมด
- **ถังน้ำ** — monitor ถังเก็บน้ำ, pump automation
- **ถังขยะ** — ทางเลือกแทน load cell เมื่อ geometry สม่ำเสมอ

## ข้อจำกัด

- ไม่เหมาะกับของเหลวที่มีฟอง, ไอ, หรือผิวไม่สม่ำเสมอ
- ของแข็ง (เช่น ขยะ) อาจสะท้อนสัญญาณผิดพลาด → load cell แม่นกว่า
- ต้องติดตั้งให้ตั้งฉากกับผิวของเหลว

## ความสัมพันธ์

- MCU: [[entities/iot/esp32]]
- Protocol: [[entities/iot/mqtt-protocol]]
- ทางเลือก (น้ำหนัก): [[entities/iot/load-cell]] + [[entities/iot/hx711]]

## แหล่งข้อมูล

- [[sources/hardware-inventory-2026-04-18]] — มีในชุด Arduino Starter Kit × 1
- [[sources/esp32-tank-level-mqtt]] — tank level sensor project (MQTT + captive portal)
