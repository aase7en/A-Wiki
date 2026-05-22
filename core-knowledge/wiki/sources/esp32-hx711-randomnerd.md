---
type: source
title: "ESP32 with Load Cell and HX711 Amplifier (Digital Scale)"
slug: esp32-hx711-randomnerd
date_ingested: 2026-04-18
original_file: https://randomnerdtutorials.com/esp32-load-cell-hx711/
tags: [esp32, hx711, load-cell, weight, calibration, oled, arduino]
---

# ESP32 with Load Cell and HX711 Amplifier (Digital Scale)

**ประเภท**: tutorial  
**แหล่ง**: Random Nerd Tutorials  
**วันที่**: 2024-2025

## ประเด็นหลัก

1. **Load Cell ทำงานอย่างไร** — strain gauges แปลงแรงกดเป็นสัญญาณไฟฟ้า, HX711 เป็น ADC 24-bit ที่ขยาย signal ให้ ESP32 อ่านได้
2. **Wiring มาตรฐาน** — load cell 4 สาย (Red=E+, Black=E-, White=A-, Green=A+) → HX711 → ESP32 GPIO16 (DT), GPIO4 (SCK)
3. **Calibration บังคับ** — ต้องหา calibration factor เฉพาะตัวสำหรับ load cell แต่ละชุด ใช้วัตถุน้ำหนักรู้ค่า (เช่น 300g)
4. **Libraries**: HX711 by Bogdan Necula, Adafruit SSD1306, Adafruit GFX, Pushbutton by Polulu
5. **3 Core Methods**: `read()` (raw ADC), `get_units(samples)` (น้ำหนักจริง), `tare()` (归零)

## ข้อมูลที่น่าสนใจ / สถิติ

- HX711 VCC ต่อ 3.3V ได้ (ไม่ต้องการ 5V)
- CPU frequency issue: ESP32 บางรุ่นต้องลด CPU เป็น 80MHz แต่ library ใหม่รองรับ 240MHz แล้ว
- ห้ามใช้ calibration factor ของคนอื่น — ต้อง calibrate เองทุกครั้ง
- สูตร: `calibration_factor = raw_reading / known_weight_grams`

## Wiring Table

| HX711 Pin | ESP32 Pin |
|-----------|-----------|
| DT (Data) | GPIO 16 |
| SCK (Clock) | GPIO 4 |
| VCC | 3.3V |
| GND | GND |

## ข้อโต้แย้งหรือความขัดแย้ง

ไม่มีความขัดแย้งกับ wiki ปัจจุบัน

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/hx711]] — สร้างใหม่
- [[entities/iot/load-cell]] — สร้างใหม่
