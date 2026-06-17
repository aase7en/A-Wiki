---
tags: [iot, lora, gateway, architecture]
type: source
title: "iot lora gateway architecture"
slug: iot-lora-gateway-architecture
date_ingested: 2026-05-24
original_file: raw/iot-lora-gateway-architecture.md
---

```yaml
---
---
```

# IoT Architecture: ESP32 Sensor + LoRa + Gateway + MQTT + Services

**Source**: iot_lora_gateway_architecture.svg (architecture diagram)  
**Date**: 2026-04-18  
**ประเภท**: Architecture decision document

## Data Flow (ซ้าย → ขวา)

```
DHT11 → ESP32 DevKit (LoRa TX node) → DX-LR02 TX
                                              ↓ LoRa 900MHz (wireless)
                                       DX-LR02 RX → ESP32-S3 (WiFi Gateway)
                                                            ↓ WiFi + MQTT
                                                     MQTT Broker (Mosquitto)
                                                            ↓
                                          ┌─────────────────┼─────────────────┐
                                     Telegram Bot      Line Notify          Grafana
```

## Zones

### Zone 1: Sensor Node (ไม่มี WiFi)
- DHT11 → ESP32 DevKit V1 (LoRa TX node)
- ESP32 DevKit → DX-LR02 (UART)
- DX-LR02 TX ส่งข้อมูลผ่าน LoRa 900MHz

### Zone 2: LoRa Gateway (มี WiFi)
- DX-LR02 RX รับสัญญาณ
- ESP32-S3 N16R8 รับข้อมูลจาก DX-LR02 ผ่าน UART
- ESP32-S3 publish ไปยัง MQTT Broker ผ่าน WiFi

### Zone 3: Cloud / Services
- MQTT Broker: Mosquitto
- Subscribers: Telegram Bot, Line Notify, Grafana (+ InfluxDB)

## คำถามที่ระบุใน diagram (onClick prompts)

1. DHT11 วัดอะไร ต่อ pin กับ ESP32 ยังไง?
2. ESP32 อ่าน DHT11 แล้วส่งผ่าน Serial ไปยัง DX-LR02 ยังไง? ขอ code ตัวอย่าง
3. DX-LR02 TX mode ตั้งค่า M0/M1/AUX ยังไง?
4. DX-LR02 RX ส่งต่อไปยัง ESP32-S3 ยังไง?
5. ESP32-S3 publish MQTT ผ่าน WiFi ยังไง?
6. ควรรัน Mosquitto ที่ไหน? RPi / VPS / Cloud?
7. สร้าง Telegram Bot จาก MQTT ยังไง?
8. Line Notify token หาได้ยังไง?
9. Grafana + InfluxDB ต้องติดตั้งอะไรบ้าง?
