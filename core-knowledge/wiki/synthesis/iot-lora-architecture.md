---
type: synthesis
tags: [architecture, lora, esp32, esp32-s3, mqtt, telegram, grafana, project-decided]
sources: [iot-lora-gateway-architecture, hardware-inventory-2026-04-18, mqtt-introduction]
created: 2026-04-18
updated: 2026-04-18
---

# สถาปัตยกรรมโปรเจ็ค: IoT Temperature Monitor (LoRa Gateway)

> **สถานะ**: Architecture ตัดสินใจแล้ว (จาก diagram 2026-04-18)

## Data Flow ทั้งหมด

```
[DHT11]
   │ single-wire
[ESP32 DevKit V1]  ← Sensor Node (ไม่ต้องมี WiFi)
   │ UART (TX/RX/M0/M1/AUX)
[DX-LR02 TX]
   │ LoRa 900MHz ~~ wireless (สูงสุด km)
[DX-LR02 RX]
   │ UART
[ESP32-S3-N16R8]   ← LoRa Gateway (มี WiFi)
   │ WiFi + MQTT (TCP port 1883)
[Mosquitto Broker] ← MQTT Broker
   │
   ├── [Python/Node.js bridge] → [Telegram Bot]  ← alert อุณหภูมิผิดปกติ
   └── [Telegraf] → [InfluxDB] → [Grafana]       ← dashboard กราฟย้อนหลัง
```

## Hardware Mapping (จาก inventory)

| บทบาท | Hardware | สถานะ |
|------|---------|-------|
| Sensor | [[entities/iot/esp32]] DevKit V1 | ✅ มีแล้ว |
| Sensor | [[entities/iot/dht11]] | ✅ มีแล้ว |
| LoRa TX | [[entities/iot/dx-lr02-lora]] #1 | ✅ มีแล้ว |
| LoRa RX | [[entities/iot/dx-lr02-lora]] #2 | ✅ มีแล้ว |
| Gateway | [[entities/iot/esp32-s3]] N16R8 | ✅ มีแล้ว |
| Power | [[entities/iot/18650-battery-shield]] + Vapcell M35 ×2 | ✅ มีแล้ว |

**ข้อสรุปสำคัญ: Hardware ครบทุกชิ้นแล้ว ไม่ต้องซื้อเพิ่ม**

## Software Stack (ต้องติดตั้ง)

| Layer | Software | ติดตั้งที่ | สถานะ |
|-------|---------|----------|-------|
| Firmware (Sensor) | Arduino/ESP-IDF + DHT lib | ESP32 flash | 🔲 |
| Firmware (Gateway) | Arduino/ESP-IDF + PubSubClient | ESP32-S3 flash | 🔲 |
| MQTT Broker | [[entities/iot/mosquitto]] | Server/Mac | 🔲 |
| Data bridge | **Telegraf** หรือ **[[entities/iot/node-red]]** | Server/Mac | 🔲 |
| DB | [[entities/iot/influxdb]] v2 หรือ [[entities/iot/mysql]] | Server/Mac | 🔲 |
| Dashboard | [[entities/iot/grafana]] | Server/Mac | 🔲 |
| Alert | [[entities/iot/telegram-bot]] | Python script | 🔲 |

### ⚡ เปรียบเทียบ Stack ทางเลือก

| หัวข้อ | Stack A (Telegraf) | Stack B (Node-RED) |
|--------|--------------------|--------------------|
| Middleware | Telegraf | [[entities/iot/node-red]] |
| Database | [[entities/iot/influxdb]] | [[entities/iot/mysql]] |
| Dashboard | [[entities/iot/grafana]] | Grafana หรือ Node-RED Dashboard |
| ความซับซ้อน | ปานกลาง | ต่ำ (low-code) |
| Control Panel | ❌ | ✅ (Button/Switch บน dashboard) |
| เหมาะกับ | production, analytics | lab, prototype, control |

## MQTT Topic Structure (แนะนำ)

```
home/
├── room/
│   ├── temperature      ← ESP32-S3 publish
│   └── humidity         ← ESP32-S3 publish
└── alerts/
    └── temperature      ← Python bridge publish (เมื่อเกิน threshold)
```

## ⚠️ ข้อควรระวัง / Open Questions

1. **Line Notify deprecated** — เปลี่ยนเป็น Telegram หรือ Line Messaging API
2. **Mosquitto รันที่ไหน?** — Mac local (dev) vs Raspberry Pi (production)
3. **LoRa channel config** — DX-LR02 ทั้ง 2 ตัวต้องตั้งค่า channel เดียวกัน
4. **Power budget** — ESP32 Sensor node ใช้ 18650 shield หรือ USB?
5. **Deep sleep** — ESP32 Sensor ควร deep sleep ระหว่าง reading เพื่อประหยัด battery

## ลำดับการ Implement (แนะนำ)

1. **Phase 1** — Flash ESP32 + DHT11 → Serial print ทดสอบ sensor
2. **Phase 2** — ต่อ DX-LR02 TX กับ ESP32, ทดสอบ LoRa send
3. **Phase 3** — ต่อ DX-LR02 RX กับ ESP32-S3, ทดสอบ LoRa receive
4. **Phase 4** — ESP32-S3 → WiFi → Mosquitto local → MQTT subscribe ยืนยันได้
5. **Phase 5** — Telegraf + InfluxDB + Grafana dashboard
6. **Phase 6** — Telegram Bot alert

## แหล่งข้อมูล

- [[sources/iot-lora-gateway-architecture]] — architecture diagram (ตัดสินใจ)
- [[sources/hardware-inventory-2026-04-18]] — hardware ที่มี
- [[sources/mqtt-introduction]] — MQTT foundation
