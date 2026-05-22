---
type: source
title: "ESP32-HX711-MQTT — Weight Scale IoT by ESP32"
slug: esp32-hx711-mqtt-github
date_ingested: 2026-04-18
original_file: https://github.com/coniferconifer/ESP32-HX711-MQTT
tags: [esp32, hx711, mqtt, weight, node-red, thingsboard, deep-sleep, pubsubclient]
---

# ESP32-HX711-MQTT — Weight Scale IoT by ESP32

**ประเภท**: GitHub project (open source)  
**ผู้เขียน**: coniferconifer  
**ภาษา**: C++ (96.3%), C (3.7%)

## ประเด็นหลัก

1. **Retrofit scale เดิม** — ถอด control board ของ TANITA ออก แทนด้วย ESP32 ทำให้ตาชั่งเดิมส่งข้อมูลผ่าน WiFi ได้
2. **MQTT → Node-RED → Thingsboard + Slack** — architecture ส่ง weight ผ่าน MQTT port 2883, Node-RED route ต่อไป Thingsboard (visualization) และ Slack (mobile notification)
3. **Deep sleep support** — ประหยัดพลังงาน แต่มี known issue เรื่อง WiFi reconnect หลือตื่นจาก deep sleep บางครั้งล้มเหลว
4. **Library**: PubSubClient (knolleary) สำหรับ MQTT

## ข้อมูลที่น่าสนใจ

- แนวคิด retrofit ประหยัดกว่าซื้อ load cell ใหม่ — ถ้ามีตาชั่งเก่าสามารถนำ load cell เดิมมาใช้ได้
- Port 2883 (ไม่ใช่ 1883 มาตรฐาน) — ต้องตรวจสอบการตั้งค่า broker
- Deep sleep + WiFi reconnect issue เป็นปัญหาทั่วไปของ ESP32 (ดู [[entities/iot/esp32]] สำหรับ workaround)

## Architecture

```
[ESP32 + HX711 + Load Cell]
        ↓ MQTT (port 2883)
   [MQTT Broker]
        ↓
   [Node-RED]
    ↙        ↘
[Thingsboard] [Slack notification]
```

## ข้อโต้แย้งหรือความขัดแย้ง

- Port 2883 ผิดปกติ — broker มาตรฐานใช้ 1883 ควรตรวจสอบการตั้งค่า Mosquitto ก่อน deploy

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/hx711]] — เพิ่มข้อมูล MQTT integration
