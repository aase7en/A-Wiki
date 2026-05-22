---
type: synthesis
tags: [air-quality, pms5003, lora, esp32, grafana, aqi, pm25]
sources: [air-quality-iot-lora-network, air-quality-sensors-dronebot, iot-lora-gateway-architecture]
created: 2026-04-19
updated: 2026-04-19
---

# ระบบ Air Quality Monitoring (PMS5003 + LoRa + Grafana)

> **คำถามที่ตอบ**: จะออกแบบระบบวัด PM2.5/PM10 แบบ distributed (หลายจุด) อย่างไร?

## สรุป

ใช้ [[entities/iot/pms5003]] วัด PM2.5/PM10 ต่อกับ [[entities/iot/esp32]] ส่งผ่าน LoRa (DX-LR02) → Gateway → MQTT → [[entities/iot/influxdb]] → [[entities/iot/grafana]] แสดงบน map หรือ dashboard เปรียบเทียบหลายจุด

## Data Flow

```
[PMS5003 UART 5V]
      ↓
[ESP32 Sensor Node] ← battery (18650 shield)
      ↓ LoRa (DX-LR02 P2P)
[ESP32-S3 Gateway]
      ↓ WiFi MQTT
[Mosquitto Broker]
      ↓
[Node-RED] → [InfluxDB] → [Grafana Dashboard + Map]
      ↓ alert (PM2.5 > 37.5 µg/m³)
[Telegram Bot]
```

## Thai AQI Standard

| ระดับ | PM2.5 (µg/m³) | สี | ความหมาย |
|-------|--------------|-----|---------|
| ดีมาก | 0-25 | ฟ้า | ปลอดภัย |
| ดี | 25.1-37.5 | เขียว | ปลอดภัย |
| ปานกลาง | 37.6-75 | เหลือง | ผู้ป่วยระวัง |
| ไม่ดี | 75.1-150 | ส้ม | ทุกคนระวัง |
| แย่มาก | >150 | แดง | อันตราย |

**Alert threshold แนะนำ**: PM2.5 > 37.5 µg/m³ → Telegram

## Hardware Required

| Component | Status | หมายเหตุ |
|-----------|--------|---------|
| [[entities/iot/pms5003]] | ❌ ยังไม่มี | UART 5V, ~100mA, ต้องมี level shifter |
| [[entities/iot/esp32]] | ✅ มีแล้ว | UART1 (GPIO16/17) ต่อ PMS5003 |
| [[entities/iot/dx-lr02-lora]] | ✅×2 มีแล้ว | LoRa P2P sensor → gateway |
| [[entities/iot/esp32-s3]] | ✅ มีแล้ว | Gateway (WiFi) |
| [[entities/iot/18650-battery-shield]] | ✅ มีแล้ว | Sensor node power |

## ⚠️ ข้อควรระวัง

1. PMS5003 ใช้ไฟ 5V แต่ data line 3.3V → ต้องมี **level shifter** (หรือ voltage divider)
2. warm-up time ~30 วินาทีก่อนอ่านค่าได้เสถียร
3. ทำความสะอาด sensor ทุก 3-6 เดือน (ฝุ่นอุด laser)
4. Multi-sensor LoRa network → ต้องกำหนด device ID ในแต่ละ node

## MQTT JSON Format

```json
{
  "node_id": "sensor_01",
  "pm25": 35.2,
  "pm10": 48.7,
  "pm1": 22.1,
  "rssi": -72,
  "battery": 3.85
}
```

**Topic**: `air/sensor/<node_id>/data`

## ความสัมพันธ์

- ใช้ร่วมกับ: [[concepts/iot/air-quality-index]], [[concepts/iot/lora-p2p]]
- เกี่ยวข้องกับ: [[entities/iot/pms5003]], [[entities/iot/dx-lr02-lora]]
- TinyML ต่อยอด: [[concepts/iot/tinyml]] (anomaly detection บน sensor data)
- อ้างอิง stack: [[synthesis/iot-lora-architecture]]

## แหล่งข้อมูล

- [[sources/air-quality-iot-lora-network]] — ESP32+PMS5003+LoRa+Grafana reference
- [[sources/air-quality-sensors-dronebot]] — sensor comparison (PMS5003, SGP30, BME280)
