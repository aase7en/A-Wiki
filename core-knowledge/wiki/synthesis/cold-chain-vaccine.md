---
type: synthesis
tags: [cold-chain, vaccine, ds18b20, esp32, lora, tinyml, anomaly-detection]
sources: [vaccine-temp-monitoring-iot, vaccine-cae-anomaly-detection, ds18b20-esp32-randomnerd]
created: 2026-04-19
updated: 2026-04-19
---

# ระบบ Cold Chain Vaccine Monitoring (DS18B20 + ESP32 + AI Anomaly)

> **คำถามที่ตอบ**: จะออกแบบระบบตรวจสอบอุณหภูมิวัคซีน (+2°C~+8°C) ที่แจ้งเตือนทันทีเมื่อผิดปกติอย่างไร?

## สรุป

ใช้ [[entities/iot/ds18b20]] (One-Wire, ±0.5°C, waterproof) วัดอุณหภูมิตู้เก็บวัคซีน ส่งข้อมูลผ่าน LoRa หรือ GSM → MQTT → alert ทันทีผ่าน Telegram ต่อยอดด้วย TinyML anomaly detection บน ESP32 เพื่อตรวจสอบ pattern ผิดปกติก่อนที่อุณหภูมิจะเกิน threshold

## ข้อกำหนด Cold Chain วัคซีน

| ประเภทวัคซีน | Range อุณหภูมิ | ความเสี่ยง |
|------------|--------------|---------|
| วัคซีนทั่วไป (OPV, Hep B) | +2°C ~ +8°C | เสียได้ถ้าเกิน 8°C >1 ชั่วโมง |
| วัคซีนที่แช่แข็ง (OPV บางชนิด) | -15°C ~ -25°C | เสียได้ถ้าละลาย |
| Alert threshold แนะนำ | เกิน +7°C หรือต่ำกว่า +3°C | แจ้งเตือนทันที |

## Data Flow

```
[DS18B20 One-Wire] (หลายตัวใน 1 สาย)
      ↓
[ESP32 Sensor]
  ├── TinyML Anomaly Detection (local inference)
  │   └── แจ้งเตือน pattern ผิดปกติ ก่อน threshold
  └── LoRa P2P / GSM → [Gateway/Cloud]
                              ↓ MQTT
                        [Mosquitto]
                              ↓
                        [InfluxDB] → [Grafana]
                              ↓ alert
                        [Telegram Bot] 🚨
```

## Hardware Required

| Component | Status | หมายเหตุ |
|-----------|--------|---------|
| [[entities/iot/ds18b20]] | ❌ ยังไม่มี | One-Wire, waterproof, ±0.5°C |
| [[entities/iot/esp32]] | ✅ มีแล้ว | One-Wire library, DallasTemperature |
| [[entities/iot/dx-lr02-lora]] | ✅×2 มีแล้ว | LoRa P2P (ถ้าไม่มี WiFi) |
| [[entities/iot/18650-battery-shield]] | ✅ มีแล้ว | backup power สำคัญมาก |

## Multi-Sensor One-Wire (DS18B20)

```cpp
// ต่อหลายตัวใน pin เดียว (4.7kΩ pull-up)
OneWire oneWire(2);           // GPIO2
DallasTemperature sensors(&oneWire);
sensors.getDeviceCount();     // นับจำนวน sensors
sensors.getTempCByIndex(0);   // อ่านตัวที่ 0
```

## TinyML Anomaly Detection (ต่อยอด)

จาก [[sources/vaccine-cae-anomaly-detection]]: ใช้ **Convolutional Autoencoder (CAE)** train ด้วย temperature time-series ปกติ → ตรวจจับ anomaly ด้วย reconstruction error

| วิธี | Accuracy | Hardware | Latency |
|-----|---------|---------|---------|
| Threshold rule | ~70% | ทุก MCU | real-time |
| CAE (TF Lite) | **92%** | ESP32-S3 (PSRAM ต้องการ) | ~50ms |

**แนะนำ**: เริ่มด้วย threshold → ต่อยอด CAE บน ESP32-S3

## MQTT JSON Format

```json
{
  "sensor_id": "fridge_01",
  "temp_c": 5.25,
  "anomaly_score": 0.02,
  "alert": false,
  "battery_v": 3.82,
  "ts": 1745001234
}
```

## ⚠️ ข้อควรระวัง

1. **Battery backup** — ถ้าไฟดับ ระบบต้องทำงานต่อ ≥4 ชั่วโมง
2. **One-Wire parasite power** — ระวัง cable ยาว → ใช้ external power mode
3. **GSM vs LoRa** — ถ้าอยู่ในห้องเย็นที่มีผนังหนา → GSM ดีกว่า LoRa
4. **Log ไม่ขาดหาย** — ใช้ local SD card buffer ก่อน sync cloud

## ความสัมพันธ์

- เกี่ยวข้องกับ: [[concepts/iot/cold-chain-monitoring]], [[concepts/iot/tinyml]]
- ใช้ร่วมกับ: [[entities/iot/ds18b20]], [[entities/iot/esp32-s3]] (CAE)
- อ้างอิง stack: [[synthesis/iot-lora-architecture]]

## แหล่งข้อมูล

- [[sources/vaccine-temp-monitoring-iot]] — ESP32 + GSM alert cold chain
- [[sources/vaccine-cae-anomaly-detection]] — Deep Learning anomaly 92% accuracy
- [[sources/ds18b20-esp32-randomnerd]] — One-Wire wiring + library guide
