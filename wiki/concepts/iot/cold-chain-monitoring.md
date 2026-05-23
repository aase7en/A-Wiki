---
type: concept
tags: [cold-chain, vaccine, temperature, monitoring, iot, alert]
sources: [vaccine-temp-monitoring-iot, vaccine-cae-anomaly-detection, ds18b20-esp32-randomnerd]
created: 2026-04-18
updated: 2026-04-18
---

# Cold Chain Monitoring (การติดตาม Cold Chain)

## นิยาม

Cold chain monitoring คือระบบ IoT ที่ติดตามและบันทึกอุณหภูมิของสินค้าที่ต้องควบคุมอุณหภูมิตลอดห่วงโซ่อุปทาน ตั้งแต่การผลิต การขนส่ง จนถึงจุดใช้งาน โดยเฉพาะวัคซีน ยา และอาหาร

## ทำไมถึงสำคัญ

วัคซีนเสื่อมสภาพถาวรเมื่อออกนอก cold chain — ไม่สามารถมองเห็นความเสียหายด้วยตาเปล่า:
- WHO กำหนด: วัคซีนต้องเก็บที่ **+2°C ถึง +8°C**
- อุณหภูมิสูงเกิน → protein denaturation → วัคซีนไม่มีประสิทธิภาพ
- อุณหภูมิต่ำเกิน (freeze) → วัคซีนบางชนิดเสียหายถาวร

## Architecture IoT สำหรับ Cold Chain

```
[DS18B20 sensors × หลายจุด]
         ↓ One-Wire
[ESP32 + GSM module]
    ↓              ↓
[MQTT publish]  [SMS/Call alert]  ← ทันที เมื่ออุณหภูมิออกนอก range
    ↓
[MQTT Broker → Node-RED]
    ↓
[InfluxDB]  ← log ทุก 5 นาที
    ↓
[Grafana]   ← dashboard + alert rule
```

## Alert Levels

| ระดับ | เงื่อนไข | การแจ้งเตือน |
|-------|---------|------------|
| Warning | >8°C หรือ <2°C ครั้งแรก | Telegram push |
| Critical | ออกนอก range > 15 นาที | SMS + Phone call (GSM) |
| Emergency | >25°C หรือ <0°C | SMS + Call + Log incident |

## Advanced: AI Anomaly Detection

แทนที่จะตั้ง threshold ตายตัว ใช้ **Convolutional Autoencoder (CAE)** รันบน ESP32 โดยตรง:
- Model เรียนรู้ pattern "ปกติ" ของอุณหภูมิในตู้แช่
- ตรวจจับ pattern ผิดปกติก่อนที่จะถึง threshold
- Accuracy 92%, ใช้ไฟเพียง 50mW

ดู [[concepts/iot/tinyml]] สำหรับ workflow การ train และ deploy

## Hardware Stack แนะนำ (งบประหยัด)

| Component | รายการ | ราคาประมาณ |
|-----------|--------|-----------|
| MCU | [[entities/iot/esp32]] | ~$3 |
| Temp sensor | [[entities/iot/ds18b20]] × 3 | ~$6 |
| Pull-up resistor | 4.7kΩ | <$0.1 |
| Alert | [[entities/iot/telegram-bot]] (ฟรี) | ฟรี |
| Storage | [[entities/iot/influxdb]] บน [[entities/iot/raspberry-pi]] | ~$30 RPi |
| Dashboard | [[entities/iot/grafana]] (ฟรี) | ฟรี |

## ความสัมพันธ์

- Sensor: [[entities/iot/ds18b20]]
- Alert: [[entities/iot/telegram-bot]]
- AI layer: [[concepts/iot/tinyml]]
- Storage: [[entities/iot/influxdb]], [[concepts/iot/data-logger]]
- Visualization: [[entities/iot/grafana]]

## แหล่งข้อมูล

- [[sources/vaccine-temp-monitoring-iot]] — complete cold chain IoT system
- [[sources/vaccine-cae-anomaly-detection]] — AI anomaly detection research 2024
- [[sources/ds18b20-esp32-randomnerd]] — sensor implementation
