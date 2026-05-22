---
type: source
title: "ESP32 PZEM-004T Energy Monitoring — Complete 2025 Guide (ESPHome & MQTT)"
slug: pzem-004t-guide-2025
date_ingested: 2026-04-18
original_file: https://esp32.co.uk/esp32-pzem-004t-energy-monitoring-with-home-assistant-esphome-mqtt-complete-2025-guide/
tags: [esp32, pzem-004t, energy, mqtt, esphome, home-assistant, uart, safety]
---

# ESP32 PZEM-004T Energy Monitoring — 2025 Guide

**ประเภท**: tutorial  
**แหล่ง**: esp32.co.uk  
**วันที่**: 2025

## ประเด็นหลัก

1. **UART wiring**: PZEM-004T ต่อกับ ESP32 ผ่าน GPIO16 (RX) และ GPIO17 (TX), baud 9600, VCC=5V
2. **MQTT JSON payload**: `{"voltage": X, "current": Y, "power": Z, "energy": A, "frequency": B, "pf": C}`
3. **2 วิธี integrate กับ Home Assistant**: ESPHome (auto-discovery) หรือ MQTT (manual config)
4. **Update rate**: publish ทุก 5 วินาที
5. **⚠️ Safety critical**: AC mains ต้องให้ electrician ที่มีใบอนุญาตติดตั้งเท่านั้น

## Wiring Table

| PZEM-004T | ESP32 |
|-----------|-------|
| VCC | 5V |
| GND | GND |
| RX | GPIO 17 |
| TX | GPIO 16 |
| Baud | 9600 |

## MQTT Topic Structure

```
Topic: home/energy/pzem
Payload: {"voltage": 220.5, "current": 2.3, "power": 507, 
          "energy": 12.5, "frequency": 50, "pf": 0.98}
```

Home Assistant sensor template:
```yaml
value_template: "{{ value_json.voltage }}"
```

## ข้อมูลสำคัญ

- InfluxDB/Grafana: ไม่ได้กล่าวถึงในบทความนี้ — ต้อง search ภายนอกถ้าต้องการ
- ESPHome ง่ายกว่า MQTT สำหรับ Home Assistant โดยเฉพาะ
- MQTT ยืดหยุ่นกว่า ใช้กับ platform อื่น (Node-RED, Grafana) ได้

## ข้อโต้แย้งหรือความขัดแย้ง

ไม่มี — สอดคล้องกับ [[entities/iot/pzem-004t]] ที่มีอยู่แล้ว

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/pzem-004t]] — อัปเดต wiring pins และ MQTT format
