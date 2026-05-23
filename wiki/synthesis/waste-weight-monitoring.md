---
type: synthesis
tags: [weight, load-cell, hx711, esp32, lora, mqtt, waste-monitoring]
sources: [esp32-hx711-randomnerd, esp32-hx711-mqtt-github, iot-lora-gateway-architecture]
created: 2026-04-19
updated: 2026-04-19
---

# ระบบ Waste/Weight Monitoring (Load Cell + HX711 + ESP32 + LoRa)

> **คำถามที่ตอบ**: จะออกแบบระบบชั่งน้ำหนักถังขยะ/สินค้า แบบ wireless อย่างไร?

## สรุป

ใช้ [[entities/iot/load-cell]] (strain gauge) + [[entities/iot/hx711]] (24-bit ADC) วัดน้ำหนัก ต่อกับ [[entities/iot/esp32]] → ส่งผ่าน LoRa P2P (DX-LR02) → Gateway → MQTT → Dashboard แจ้งเตือนเมื่อถังเต็ม

## Data Flow

```
[Load Cell] (ติดใต้ถังขยะ)
      ↓ analog differential
[HX711 ADC] (24-bit, gain 128)
      ↓ 2-wire (DOUT + SCK)
[ESP32 Sensor] ← deep sleep ระหว่าง reading (ประหยัด battery)
      ↓ LoRa (DX-LR02 P2P)
[ESP32-S3 Gateway]
      ↓ WiFi MQTT
[Mosquitto] → [InfluxDB] → [Grafana]
      ↓ alert (weight > threshold)
[Telegram Bot] → แจ้ง "ถังขยะใกล้เต็ม"
```

## Hardware Required

| Component | Status | หมายเหตุ |
|-----------|--------|---------|
| [[entities/iot/load-cell]] | ❌ ยังไม่มี | ต้องซื้อ, เลือก range ตาม load (5kg/50kg) |
| [[entities/iot/hx711]] | ❌ ยังไม่มี | ต้องซื้อ, 24-bit ADC |
| [[entities/iot/esp32]] | ✅ มีแล้ว | GPIO digital สำหรับ HX711 |
| [[entities/iot/dx-lr02-lora]] | ✅×2 มีแล้ว | LoRa P2P wireless |
| [[entities/iot/18650-battery-shield]] | ✅ มีแล้ว | battery-powered node |

## Calibration ขั้นตอน

```cpp
#include <HX711.h>
HX711 scale;
scale.begin(DOUT, SCK);
scale.set_scale(calibration_factor);  // หา factor จากน้ำหนักรู้ค่า
scale.tare();                          // reset 0
float weight_kg = scale.get_units(10); // average 10 readings
```

**Calibration**: วางน้ำหนักรู้ค่า (1kg) → ปรับ `calibration_factor` จนแสดงค่าถูกต้อง

## Deep Sleep Strategy (ประหยัด Battery)

```
อ่านค่า → publish MQTT → deep sleep 5 นาที → ตื่น → repeat
Active: ~250mA × 2 วินาที
Sleep:  ~10µA × 298 วินาที
Average: ~1.7mA → 18650 3500mAh → ~85 วัน
```

## MQTT JSON Format

```json
{
  "bin_id": "bin_A1",
  "weight_kg": 12.5,
  "fill_pct": 62.5,
  "battery_v": 3.81,
  "rssi": -68
}
```

**Topic**: `waste/bin/<bin_id>/weight`

## ⚠️ ข้อควรระวัง

1. Load Cell ต้องการ **mechanical mounting ที่ดี** — ถ้าถังเอียง ค่าผิดพลาด
2. Temperature drift — HX711 gain เปลี่ยนตามอุณหภูมิ → calibrate ใหม่ทุกฤดู
3. LoRa interference — ถ้าหลาย sensor node → ใช้ time-slotting เพื่อกัน collision
4. ลม/vibration → noise ใน load cell → average readings 10-20 ครั้ง

## ความสัมพันธ์

- เกี่ยวข้องกับ: [[entities/iot/load-cell]], [[entities/iot/hx711]], [[concepts/iot/lora-p2p]]
- ใช้ร่วมกับ: [[concepts/iot/data-logger]], [[concepts/iot/dashboard-design]]
- TinyML ต่อยอด: [[concepts/iot/tinyml]] (predict fill rate, optimize pickup schedule)
- อ้างอิง stack: [[synthesis/iot-lora-architecture]]

## แหล่งข้อมูล

- [[sources/esp32-hx711-randomnerd]] — wiring, calibration, HX711 library
- [[sources/esp32-hx711-mqtt-github]] — MQTT integration + Node-RED + Thingsboard
