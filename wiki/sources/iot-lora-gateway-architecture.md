---
type: source
title: "IoT Architecture Diagram: ESP32 + LoRa + MQTT + Services"
slug: iot-lora-gateway-architecture
date_ingested: 2026-04-18
original_file: raw/iot-lora-gateway-architecture.md
tags: [architecture, lora, esp32, esp32-s3, mqtt, telegram, grafana, line-notify, project-plan]
---

# IoT Architecture Diagram: ESP32 + LoRa + MQTT + Services

**ประเภท**: Architecture decision diagram (SVG)  
**วันที่**: 2026-04-18

## ประเด็นหลัก

1. **Architecture ถูกตัดสินใจแล้ว** — เลือก Approach C (LoRa P2P) ไม่ใช่ WiFi direct
2. **Role ของ hardware ชัดเจน**: ESP32 DevKit = Sensor Node, ESP32-S3 = Gateway
3. **Services ที่ต้องการ**: Telegram Bot + Line Notify + Grafana (3 services พร้อมกัน)
4. MQTT Broker = Mosquitto (ยืนยัน choice จาก wiki เดิม)

## สิ่งที่ยังต้องตัดสินใจ

- Mosquitto จะรันที่ไหน? (RPi / VPS / Mac local)
- InfluxDB: local หรือ cloud? (Grafana ต้องการ data source)
- Line Notify vs Line Messaging API (Line Notify deprecate แล้วปี 2025)

## ความขัดแย้งกับ wiki เดิม

- synthesis/temperature-monitor-project เสนอ 3 แนวทาง — ตอนนี้ **ยืนยัน Approach C (LoRa)** แล้ว → ต้องอัปเดตหน้านั้น

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/telegram-bot]] — สร้างใหม่
- [[entities/iot/line-notify]] — สร้างใหม่
- [[entities/iot/grafana]] — สร้างใหม่
- [[entities/iot/influxdb]] — สร้างใหม่
- [[synthesis/temperature-monitor-project]] — อัปเดต: ยืนยัน approach C
- [[synthesis/iot-lora-architecture]] — สร้างใหม่ (architecture เต็ม)
