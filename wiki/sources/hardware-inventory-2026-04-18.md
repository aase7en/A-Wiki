---
type: source
title: "Hardware Inventory — My IoT Lab (2026-04-18)"
slug: hardware-inventory-2026-04-18
date_ingested: 2026-04-18
original_file: raw/hardware-inventory-2026-04-18.md
tags: [inventory, esp32, esp32-s3, arduino, lora, dht11, hardware, personal-lab]
---

# Hardware Inventory — My IoT Lab

**ประเภท**: personal inventory (ถ่ายรูปอุปกรณ์จริง)  
**วันที่**: 2026-04-18  
**ผู้เขียน**: เจ้าของ wiki

## ประเด็นหลัก

1. Lab มี MCU 3 ตัวต่างสถาปัตยกรรม: ESP32 (classic), ESP32-S3 (USB native), Arduino Uno (AVR)
2. มี LoRa module 2 ตัว (DX-LR02-900T22D) — เหมาะสำหรับ long-range wireless ที่ไม่พึ่ง WiFi
3. Power system พร้อม: 18650 × 2 + Battery Shield ให้ 5V/4A และ 3.3V ต่อ MCU โดยตรง
4. Starter Kit มี sensor ครบสำหรับ beginner: DHT11, PIR, relay, ultrasonic, OLED
5. โปรเจ็คเป้าหมาย: temperature monitoring → Line/Telegram/Dashboard

## อุปกรณ์ที่โดดเด่นที่สุด

- **ESP32-S3-N16R8**: 16MB Flash + 8MB PSRAM, USB native, แรงที่สุดในชุด
- **DX-LR02 LoRa 900MHz**: ถ้าใช้ 2 ตัว สามารถทำ point-to-point LoRa link ได้เลย โดยไม่ต้องมี gateway
- **Vapcell M35**: high-drain cell (10A continuous) — เกินพอสำหรับ ESP32 (peak ~500mA)

## แนวทางโปรเจ็คที่เป็นไปได้

| โปรเจ็ค | อุปกรณ์ที่ใช้ |
|---------|------------|
| Temp monitor → MQTT → Dashboard | ESP32 + DHT11 + WiFi + Mosquitto |
| Temp monitor แบบ LoRa (ไม่ใช้ WiFi) | ESP32 + DHT11 + DX-LR02 × 2 |
| Home alert ผ่าน Telegram | ESP32 + WiFi + Bot API |
| Plant monitor | ESP32-S3 + Soil sensor + DHT11 |

## ข้อโต้แย้ง / ความขัดแย้ง

*(wiki ยังใหม่ ไม่มีข้อมูลเดิมขัดแย้ง)*

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/esp32]] — สร้างใหม่ (แทน stub)
- [[entities/iot/esp32-s3]] — สร้างใหม่
- [[entities/iot/arduino-uno-r3]] — สร้างใหม่
- [[entities/iot/dx-lr02-lora]] — สร้างใหม่
- [[entities/iot/18650-battery-shield]] — สร้างใหม่
- [[entities/iot/dht11]] — สร้างใหม่
- [[entities/iot/hc-sr501]] — สร้างใหม่
- [[concepts/iot/lora]] — สร้างใหม่
