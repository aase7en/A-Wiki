---
type: entity
category: device
tags: [sensor, temperature, humidity, dht11, digital, beginner]
sources: [hardware-inventory-2026-04-18]
created: 2026-04-18
updated: 2026-04-18
---

# DHT11 Temperature & Humidity Sensor

**ผู้ผลิต**: Aosong (generic)  
**สถานะใน Lab**: ✅ มีอยู่ × 1 (ใน Starter Kit)

## ภาพรวม

DHT11 เป็น sensor วัดอุณหภูมิและความชื้นแบบ digital output ใช้ protocol เดียว (single-wire) ราคาถูกมาก เป็นตัวเลือกแรกสำหรับ beginner IoT project รวมถึงโปรเจ็ค temperature monitor ที่วางแผนไว้

## Specs หลัก

| คุณสมบัติ | รายละเอียด |
|----------|-----------|
| Temperature range | 0–50°C |
| Temperature accuracy | **±2°C** |
| Humidity range | 20–90% RH |
| Humidity accuracy | **±5% RH** |
| Sampling rate | **1 ครั้ง/วินาที** (ช้ามาก) |
| Interface | Single-wire digital |
| Voltage | 3.3V–5.5V |
| Current | 0.3mA measuring, 60µA standby |

## ข้อจำกัด (สำคัญ)

- **±2°C accuracy** — ถ้าต้องการความแม่นยำสูงกว่านี้ ใช้ DHT22 (±0.5°C) หรือ SHT30 (±0.2°C)
- **อ่านได้แค่ทุก 1-2 วินาที** — ถ้า poll เร็วกว่านี้ sensor อาจ hang
- **ไม่รองรับ I2C/SPI** — ใช้ protocol เฉพาะของตัวเอง ต้องใช้ library

## Library สำหรับ ESP32

```cpp
#include <DHT.h>
#define DHTPIN 4
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

float t = dht.readTemperature();
float h = dht.readHumidity();
```

## เปรียบเทียบกับรุ่นอื่น

| Sensor | Temp accuracy | RH accuracy | ราคา |
|--------|-------------|------------|------|
| **DHT11** | ±2°C | ±5% | ถูกสุด |
| DHT22 | ±0.5°C | ±2-5% | กลาง |
| SHT30 | ±0.2°C | ±2% | แพงกว่า |
| BME280 | ±1°C | ±3% | กลาง (มี pressure ด้วย) |

## ความสัมพันธ์

- ใช้กับ: [[entities/iot/esp32]], [[entities/iot/esp32-s3]], [[entities/iot/arduino-uno-r3]]
- เหมาะสำหรับโปรเจ็ค: Temperature Monitor (เป้าหมายของ lab นี้)
- อัปเกรดได้เป็น: DHT22, SHT30, BME280 (ยังไม่มีหน้า)

## แหล่งข้อมูล

- [[sources/hardware-inventory-2026-04-18]]
