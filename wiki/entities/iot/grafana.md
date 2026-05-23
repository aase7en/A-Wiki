---
type: entity
category: platform
tags: [grafana, dashboard, visualization, time-series, open-source]
sources: [iot-lora-gateway-architecture, iot-nodered-mqtt-sql-course]
created: 2026-04-18
updated: 2026-04-18
---

# Grafana

**ผู้พัฒนา**: Grafana Labs  
**License**: AGPL v3 (self-hosted ฟรี)  
**บทบาทในโปรเจ็ค**: Dashboard กราฟอุณหภูมิย้อนหลัง  
**สถานะ**: 🔲 ยังไม่ได้ติดตั้ง

## ภาพรวม

Grafana เป็น visualization platform ที่ดีที่สุดสำหรับ time-series data ใช้คู่กับ [[entities/iot/influxdb]] เป็น data source มาตรฐาน IoT: Grafana query InfluxDB แสดงกราฟ real-time และย้อนหลัง

## Architecture ในโปรเจ็คนี้

```
MQTT Broker (Mosquitto)
       ↓
  Telegraf (bridge)   ← subscribe MQTT topics
       ↓
  InfluxDB            ← เก็บ time-series data
       ↓
  Grafana             ← query และแสดงกราฟ
```

หรือ alternative (ไม่ใช้ Telegraf):
```
Python script → subscribe MQTT → write to InfluxDB → Grafana
```

## การติดตั้ง (Docker Compose แนะนำ)

```yaml
version: '3'
services:
  influxdb:
    image: influxdb:2.7
    ports: ["8086:8086"]
    volumes: ["influxdb-data:/var/lib/influxdb2"]

  grafana:
    image: grafana/grafana:latest
    ports: ["3000:3000"]
    depends_on: [influxdb]

volumes:
  influxdb-data:
```

## Dashboard สำหรับ Temperature Monitor

Panel ที่แนะนำสร้าง:
1. **Gauge** — อุณหภูมิปัจจุบัน (real-time)
2. **Time series graph** — ย้อนหลัง 24 ชั่วโมง
3. **Alert rule** — trigger เมื่ออุณหภูมิ > threshold → ส่ง Telegram

## Data Sources ที่รองรับ

Grafana รองรับ data source หลายแบบ — เลือกตาม stack ที่ใช้:

| Data Source | Stack | เหมาะกับ |
|-------------|-------|---------|
| InfluxDB | Telegraf → InfluxDB → Grafana | time-series sensor, production |
| MySQL | Node-RED → MySQL → Grafana | Data Logger ทั่วไป, lab |
| PostgreSQL | - | relational + time-series |

## ความสัมพันธ์

- Data source (time-series): [[entities/iot/influxdb]]
- Data source (relational): [[entities/iot/mysql]]
- Data pipeline A: [[entities/iot/mosquitto]] → Telegraf → [[entities/iot/influxdb]] → Grafana
- Data pipeline B: [[entities/iot/mosquitto]] → [[entities/iot/node-red]] → [[entities/iot/mysql]] → Grafana
- Alert ไปยัง: [[entities/iot/telegram-bot]]

## แหล่งข้อมูล

- [[sources/iot-lora-gateway-architecture]] — ระบุใน architecture diagram
- [[sources/iot-nodered-mqtt-sql-course]] — Grafana + MySQL datasource
