---
type: entity
category: platform
tags: [influxdb, time-series, database, iot-core, open-source]
sources: [iot-lora-gateway-architecture]
created: 2026-04-18
updated: 2026-04-18
---

# InfluxDB

**ผู้พัฒนา**: InfluxData  
**เวอร์ชัน**: 2.x (OSS, ฟรี self-hosted)  
**บทบาทในโปรเจ็ค**: เก็บ time-series sensor data สำหรับ Grafana  
**สถานะ**: 🔲 ยังไม่ได้ติดตั้ง

## ภาพรวม

InfluxDB เป็น time-series database ออกแบบมาเพื่อ IoT และ metrics โดยเฉพาะ เก็บข้อมูลที่มี timestamp ได้อย่างมีประสิทธิภาพมาก auto-compress data เก่า (retention policy)

## ทำไมใช้ InfluxDB แทน MySQL/SQLite

| | InfluxDB | MySQL |
|-|---------|-------|
| เหมาะกับ | Time-series (sensor) | General-purpose |
| Storage efficiency | สูงมาก (compression) | ปานกลาง |
| Query for time range | ง่ายมาก (Flux/InfluxQL) | ต้อง index |
| Retention auto-delete | ✅ built-in | ❌ ต้อง custom |
| Grafana integration | ✅ native | ต้องเพิ่ม plugin |

## การเขียนข้อมูล (Python)

```python
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

client = InfluxDBClient(url="http://localhost:8086", token="MY_TOKEN", org="my-org")
write_api = client.write_api(write_options=SYNCHRONOUS)

point = Point("environment") \
    .tag("location", "living_room") \
    .field("temperature", 28.5) \
    .field("humidity", 65.0)

write_api.write(bucket="iot-data", record=point)
```

## Retention Policy แนะนำ

- **Raw data**: เก็บ 30 วัน (ทุก 30 วินาที)
- **Downsampled**: เก็บ 1 ปี (hourly average)

## ความสัมพันธ์

- ถูก query โดย: [[entities/iot/grafana]]
- รับข้อมูลจาก: [[entities/iot/mosquitto]] (ผ่าน Telegraf หรือ Python script)

## แหล่งข้อมูล

- [[sources/iot-lora-gateway-architecture]]
