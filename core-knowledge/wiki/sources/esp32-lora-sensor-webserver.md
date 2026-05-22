---
type: source
title: "ESP32 LoRa Sensor Monitoring with Web Server (Long Range Communication)"
slug: esp32-lora-sensor-webserver
date_ingested: 2026-04-18
original_file: raw/ESP32 LoRa Sensor Monitoring with Web Server (Long Range Communication).md
tags: [esp32, lora, webserver, bme280, ttgo, sensor, project]
---

# ESP32 LoRa Sensor Monitoring with Web Server

**ประเภท**: tutorial / project
**วันที่**: 2019-11-20
**ผู้เขียน**: Rui Santos (randomnerdtutorials.com)

## ประเด็นหลัก

1. **Project pattern**: LoRa Sender (sensor node) + LoRa Receiver (gateway + web server) — ตรงกับ architecture ของโปรเจ็คปัจจุบัน
2. **Hardware**: TTGO LoRa32 SX1276 OLED board (ESP32 + SX1276 built-in)
3. **Sensor**: BME280 (temp/humidity/pressure) ส่งทุก 10 วินาที
4. **Gateway**: Receiver รัน async web server แสดงผล real-time บน LittleFS
5. **NTP time**: ใช้ Network Time Protocol เพื่อแสดง timestamp ของ reading ล่าสุด

## Architecture (ตรงกับโปรเจ็คนี้มาก)

```
[BME280 + ESP32 + LoRa TX]
         ~~~ LoRa ~~~
[ESP32 + LoRa RX]
    ↓ WiFi
[Web Server (LittleFS)]
    ← browser access
```

เปรียบกับโปรเจ็คปัจจุบัน:
```
[DHT11 + ESP32 + DX-LR02 TX]
         ~~~ LoRa ~~~
[ESP32-S3 + DX-LR02 RX]
    ↓ WiFi → MQTT → Grafana
```

## ข้อมูลที่น่าสนใจ

- Receiver ใช้ WiFi สำหรับ web server และ NTP พร้อมกัน — ยืนยันว่า ESP32 รัน LoRa + WiFi พร้อมกันได้
- LittleFS สำหรับเก็บ HTML/CSS/JS file บน ESP32 filesystem
- Range: "several hundred meters" ขึ้นอยู่กับ location

## ข้อโต้แย้งหรือความขัดแย้ง

บทความนี้ใช้ TTGO LoRa32 (SX1276 built-in, SPI) ต่างจาก DX-LR02 (UART) — code pattern ต่างกัน แต่ architecture และ concept เหมือนกัน

## หน้า Wiki ที่ได้รับการอัปเดต

- [[concepts/iot/lora-p2p]] — เพิ่มตัวอย่าง project pattern
- [[entities/iot/rfm95-sx1276]] — อ้างอิง TTGO LoRa32
