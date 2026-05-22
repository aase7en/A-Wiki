---
type: source
title: "ESP32 Tank Level Sensor — Ultrasonic + MQTT + Captive Portal"
slug: esp32-tank-level-mqtt
date_ingested: 2026-04-18
original_file: https://github.com/Voelk-IT/esp32-tank-level-sensor
tags: [esp32, ultrasonic, tank, level, mqtt, captive-portal, fuel, water]
---

# ESP32 Tank Level Sensor

**ประเภท**: GitHub project (open source)  
**ผู้เขียน**: Voelk-IT

## ประเด็นหลัก

1. **Ultrasonic + MQTT**: ESP32 วัดระยะด้วย HC-SR04 แปลงเป็น % แล้ว publish MQTT
2. **Captive Portal**: ครั้งแรก ESP32 ทำตัวเป็น AP ให้ config WiFi + MQTT ผ่าน browser ไม่ต้อง re-flash
3. **4 MQTT Topics**: `tank/level` (%), `tank/status`, `tank/lastupdate`, `tank/wificonnect`
4. **NTP sync**: timestamp ถูกต้องสำหรับ logging
5. **Auto WiFi reconnect**: กู้คืนเองเมื่อเน็ตหลุด

## Wiring

| HC-SR04 | ESP32 |
|---------|-------|
| TRIG | GPIO 4 |
| ECHO | GPIO 18 |
| VCC | 5V |
| GND | GND |

## Calibration Parameters

- `Empty Level`: ระยะ (cm) เมื่อถังว่าง (sensor ถึงก้นถัง)
- `Full Level`: ระยะ (cm) เมื่อถังเต็ม (sensor ถึงผิวของเหลว)
- คำนวณ: `level% = (empty - distance) / (empty - full) × 100`

## ใช้กับ Use Case ไหน

- ✅ ถังน้ำมันเชื้อเพลิง (ทรงกระบอก, ของเหลวใส)
- ✅ ถังน้ำ, ถังสารเคมี
- ⚠️ ถังขยะ (solid ไม่สม่ำเสมอ → load cell แม่นกว่า)
- ❌ ของเหลวมีฟองหรือไอ → signal สะท้อนผิด

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/hc-sr04]] — เพิ่ม tank level use case, MQTT topics
