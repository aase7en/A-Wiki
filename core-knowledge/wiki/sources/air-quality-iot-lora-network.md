---
type: source
title: "AIR-QUALITY-IOT-NETWORK — Distributed LoRa + Kafka + Grafana"
slug: air-quality-iot-lora-network
date_ingested: 2026-04-18
original_file: https://github.com/Thweatt12/AIR-QUALITY-IOT-NETWORK
tags: [esp32, lora, pms5003, bme688, scd41, kafka, influxdb, grafana, raspberry-pi, air-quality]
---

# AIR-QUALITY-IOT-NETWORK

**ประเภท**: GitHub project (open source)  
**ผู้เขียน**: Thweatt12  
**Stack**: ESP32 + LoRa 915MHz + Raspberry Pi + Kafka + InfluxDB + Grafana

## ประเด็นหลัก

1. **Distributed network**: Sensor nodes → LoRa → Gateway → RPi → Kafka → InfluxDB → Grafana
2. **Sensors ต่อ node**: PMS5003 (PM1/2.5/10) + BME688 (Temp/Humidity/Pressure/VOC) + SCD41 (CO2)
3. **LoRa settings**: 915MHz, SF7, 125kHz BW, 14dBm TX, range ~2km
4. **Kafka แทน MQTT**: ใช้ Kafka สำหรับ message streaming (ไม่ใช่ MQTT ปกติ)
5. **Grafana dashboards**: PM2.5/PM10 trends, CO2, rolling averages, rate-of-change

## Full Architecture

```
[ESP32 Node + PMS5003 + BME688 + SCD41]
         ↓ LoRa 915MHz (SF7, 125kHz, 14dBm)
[ESP32 Gateway + OLED]
         ↓ USB Serial
[Raspberry Pi]  ← เพิ่ม RSSI/SNR metadata
         ↓ Kafka (topic: air_quality, 3 partitions, 7-day retention)
[Main PC — Docker Stack]
         ↓
[InfluxDB (bucket: sensor_data, 90-day retention)]
         ↓
[Grafana :3000]
```

## LoRa Packet Format

แต่ละ packet ประกอบด้วย:
- Node ID
- PM1.0, PM2.5, PM10
- Temperature, Humidity, Pressure, VOC
- CO2
- Packet count (สำหรับ detect packet loss)

## เกี่ยวข้องกับโปรเจ็คนี้แค่ไหน

**ตรงมาก** — architecture แบบเดียวกับที่เราใช้ (ESP32 + LoRa + RPi + Grafana) แต่ใช้ Kafka แทน MQTT และ sensors ครบกว่ามาก เหมาะเป็น reference สำหรับ scale up

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/pms5003]] — สร้างใหม่
- [[concepts/iot/air-quality-index]] — สร้างใหม่
