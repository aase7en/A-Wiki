---
type: source
title: "ESP32 LoRa 1-CH Gateway, LoRaWAN, and the Things Network"
slug: esp32-lora-gateway-sparkfun
date_ingested: 2026-04-18
original_file: raw/ESP32 LoRa 1-CH Gateway, LoRaWAN, and the Things Network.md
tags: [esp32, lora, lorawan, ttn, gateway, rfm95, sparkfun]
---

# ESP32 LoRa 1-CH Gateway, LoRaWAN, and the Things Network

**ประเภท**: tutorial
**วันที่**: unknown
**ผู้เขียน**: jimblom (SparkFun)

## ประเด็นหลัก

1. **Single-channel gateway**: ESP32 + RFM95W สร้าง LoRaWAN gateway ช่องเดียวได้ — ถูกกว่า multi-channel gateway มาก
2. **Dual mode**: บอร์ดเดียวกันใช้เป็น gateway หรือ LoRa end-device ได้
3. **The Things Network (TTN)**: cloud LoRaWAN Network Server ฟรี — รับข้อมูลจาก gateway ส่งต่อไป application
4. **Qwiic connector**: ต่อ sensor modules ได้ง่าย

## LoRaWAN Stack ที่นำเสนอ

```
[LoRa End-device]
    ~~~ LoRa ~~~
[ESP32 1-CH Gateway]
    ↓ WiFi / Ethernet
[The Things Network (TTN)]
    ↓ HTTP / MQTT
[Application / Dashboard]
```

## ข้อมูลที่น่าสนใจ

- Single-channel gateway ไม่ใช่ LoRaWAN compliant เต็มรูปแบบ (จริงๆ ต้องการ 8+ channels) แต่เพียงพอสำหรับ hobbyist
- บอร์ด SPX-14893 ปัจจุบัน Retired แล้ว — รุ่นใหม่คือ WRL-15006

## เกี่ยวข้องกับโปรเจ็คนี้แค่ไหน

โปรเจ็คปัจจุบันใช้ **LoRa P2P** ไม่ใช่ LoRaWAN — source นี้เป็น reference สำหรับ **อนาคต** ถ้าต้องการ scale ขึ้น

## หน้า Wiki ที่ได้รับการอัปเดต

- [[concepts/iot/lorawan]] — สร้างใหม่
- [[entities/iot/the-things-network]] — สร้างใหม่
