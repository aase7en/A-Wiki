---
type: synthesis
tags: [tank-level, hc-sr04, ultrasonic, mqtt, esp32, captive-portal]
sources: [esp32-tank-level-mqtt]
created: 2026-04-19
updated: 2026-04-19
---

# ระบบ Fuel/Water Tank Level Monitoring (HC-SR04 + ESP32 + MQTT)

> **คำถามที่ตอบ**: จะออกแบบระบบวัดระดับน้ำ/เชื้อเพลิงในถัง และแจ้งเตือนเมื่อน้อยเกินไปอย่างไร?

## สรุป

ใช้ [[entities/iot/hc-sr04]] (ultrasonic distance) ติดตั้งบนปากถัง วัดระยะห่างจาก sensor ถึงผิวน้ำ → คำนวณเป็น % level → publish MQTT → แจ้งเตือน Telegram เมื่อ level ต่ำกว่า threshold

## Data Flow

```
[HC-SR04 Ultrasonic] (ติดที่ปากถัง)
      ↓ trigger + echo
[ESP32] ← WiFi config ผ่าน Captive Portal
      ↓ MQTT publish (distance_cm + level_pct)
[Mosquitto Broker]
      ↓
[Node-RED / Telegraf]
      ↓
[InfluxDB] → [Grafana]
      ↓ alert (level < 20%)
[Telegram Bot]
```

## การคำนวณ Level

```cpp
float tank_height_cm = 100.0;  // ความสูงถัง
float distance_cm = measureUltrasonic();
float level_pct = ((tank_height_cm - distance_cm) / tank_height_cm) * 100.0;
// distance น้อย = น้ำเยอะ = level สูง
```

## Hardware Required

| Component | Status | หมายเหตุ |
|-----------|--------|---------|
| [[entities/iot/hc-sr04]] | ✅ มีแล้ว | 5V trigger+echo, range 2-400cm |
| [[entities/iot/esp32]] | ✅ มีแล้ว | GPIO digital out/in |
| [[entities/iot/mosquitto]] | software | MQTT broker |
| [[entities/iot/telegram-bot]] | software | แจ้งเตือน level ต่ำ |

**ข้อสรุป: Hardware ครบแล้ว ไม่ต้องซื้อเพิ่ม**

## Captive Portal Config (จาก source)

ESP32 เปิด WiFi AP "TankConfig" → ผู้ใช้เชื่อมต่อ → กรอก:
- WiFi SSID + Password
- MQTT Broker IP
- Tank height (cm)
- Alert threshold (%)

บันทึกลง SPIFFS → reboot → เชื่อม WiFi จริง

## MQTT JSON Format

```json
{
  "sensor": "tank_01",
  "distance_cm": 45.2,
  "level_pct": 54.8,
  "alert": false
}
```

**Topic**: `home/tank/<name>/level`

## Grafana Dashboard

| Panel | Metric | Display |
|-------|--------|---------|
| Gauge | Level % | 0-100% สีแดง<20% |
| Stat | Distance cm | raw distance |
| Time-series | Level history | 24h trend |
| Alert | Level < threshold | Telegram |

## ⚠️ ข้อควรระวัง

1. HC-SR04 ต้องการ **5V** แต่ ESP32 logic 3.3V → ใช้ voltage divider บน echo pin
2. foam/น้ำมัน → เสียงสะท้อนผิดปกติ → กรอง outlier ด้วย median filter
3. ถ้าอุณหภูมิเปลี่ยน → speed of sound เปลี่ยน → calibrate ตามฤดูกาล
4. ความชื้นสูงในถัง → condensation บน sensor

## ความสัมพันธ์

- ใช้ร่วมกับ: [[entities/iot/hc-sr04]], [[concepts/iot/data-logger]]
- เกี่ยวข้องกับ: [[entities/iot/node-red]] (flow processing)
- อ้างอิง stack: [[synthesis/iot-lora-architecture]]

## แหล่งข้อมูล

- [[sources/esp32-tank-level-mqtt]] — HC-SR04 + MQTT + Captive Portal implementation
