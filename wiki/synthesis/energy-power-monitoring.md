---
type: synthesis
tags: [energy, pzem-004t, modbus, mqtt, esp32, grafana, power-monitoring]
sources: [pzem-004t-guide-2025, espem-energy-monitor, iot-lora-gateway-architecture]
created: 2026-04-19
updated: 2026-04-19
---

# ระบบ Energy/Power Monitoring (PZEM-004T + ESP32 + MQTT)

> **คำถามที่ตอบ**: จะออกแบบระบบมอนิเตอร์ไฟฟ้า (V/A/W/Wh) อย่างไร?

## สรุป

ใช้ [[entities/iot/pzem-004t]] ต่อกับ [[entities/iot/esp32]] ผ่าน UART (Modbus RTU) แล้ว publish ไปยัง [[entities/iot/mosquitto]] → [[entities/iot/influxdb]] → [[entities/iot/grafana]] dashboard เหมาะสำหรับมอนิเตอร์ปลั๊กไฟ ตู้แช่ หรืออุปกรณ์ไฟฟ้า AC

## Data Flow

```
[AC Load] → [PZEM-004T] ← UART Modbus RTU → [ESP32]
                                                  ↓ WiFi MQTT JSON
                                          [Mosquitto Broker]
                                                  ↓
                                          [Node-RED / Telegraf]
                                                  ↓
                                          [InfluxDB] → [Grafana]
                                                  ↓ alert
                                          [Telegram Bot]
```

## Hardware Required

| Component | Status | หมายเหตุ |
|-----------|--------|---------|
| [[entities/iot/pzem-004t]] | ❌ ยังไม่มี | ต้องซื้อ — UART 5V, Modbus RTU |
| [[entities/iot/esp32]] | ✅ มีแล้ว | Serial2 (GPIO16/17) ต่อ PZEM |
| [[entities/iot/mosquitto]] | software | ต้องติดตั้ง |
| [[entities/iot/influxdb]] | software | ต้องติดตั้ง |
| [[entities/iot/grafana]] | software | ต้องติดตั้ง |
| [[entities/iot/telegram-bot]] | software | alert ค่า W เกิน threshold |

## MQTT JSON Format (จาก ESPEM project)

```json
{
  "voltage": 220.5,
  "current": 1.23,
  "power": 271.2,
  "energy": 1.456,
  "frequency": 50.0,
  "pf": 0.98
}
```

**Topic แนะนำ**: `home/power/<room>/data`

## Grafana Dashboard Panels

| Panel | Metric | Unit |
|-------|--------|------|
| Gauge | Voltage | V |
| Gauge | Current | A |
| Stat | Active Power | W |
| Time-series | Power history | W/time |
| Stat | Energy (Wh) | kWh |
| Gauge | Power Factor | % |

## ⚠️ ข้อควรระวัง

1. PZEM-004T ต้องการ **CT clamp บน live wire** — ระวังไฟฟ้า 220V
2. PZEM มี 2 รุ่น: v3.0 (UART ตรง) และ รุ่นเก่า (ต้องแก้ address)
3. ใช้ `EspSoftwareSerial` ถ้าไม่มี hardware Serial ว่าง
4. ต้องต่อ **isolator optocoupler** ถ้า ground loop เป็นปัญหา

## ความสัมพันธ์

- ใช้ร่วมกับ: [[concepts/iot/modbus]], [[concepts/iot/data-logger]]
- เกี่ยวข้องกับ: [[entities/iot/node-red]] (flow-based processing)
- อ้างอิง stack: [[synthesis/iot-lora-architecture]]

## แหล่งข้อมูล

- [[sources/pzem-004t-guide-2025]] — UART wiring, MQTT JSON, ESPHome integration
- [[sources/espem-energy-monitor]] — ESPEM project reference implementation
