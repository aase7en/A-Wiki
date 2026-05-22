---
type: source
title: "MQTT: The Standard Messaging Protocol for IoT"
slug: mqtt-introduction
date_ingested: 2026-04-18
original_file: raw/mqtt-introduction.md
tags: [mqtt, protocol, messaging, broker, iot-core]
---

# MQTT: The Standard Messaging Protocol for IoT

**ประเภท**: article (example — wiki initialization)  
**วันที่**: 2026-04-18  
**ผู้เขียน**: ตัวอย่างสำหรับการเริ่มต้น wiki

## ประเด็นหลัก

1. MQTT เป็น publish-subscribe protocol ที่ออกแบบมาเพื่อ IoT โดยเฉพาะ มี overhead ต่ำมาก (fixed header 2 bytes)
2. ใช้ Broker เป็นศูนย์กลาง ทำให้อุปกรณ์ไม่ต้องคุยกันตรงๆ — scalable และ decoupled
3. มี 3 ระดับ QoS: fire-and-forget / at-least-once / exactly-once
4. MQTT 5.0 เพิ่ม features สำคัญ เช่น shared subscriptions, message expiry, user properties
5. รองรับ TLS บนพอร์ต 8883 และ client certificate authentication

## ข้อมูลที่น่าสนใจ

- MQTT เก่าแก่มาก ถูกออกแบบในปี 1999 สำหรับ monitoring pipeline น้ำมันผ่านดาวเทียม
- ใช้ battery น้อยกว่า HTTP ถึง ~2 เท่า สำหรับ payload ขนาดเล็ก
- Home Assistant ใช้ MQTT เป็นโปรโตคอลหลัก
- EMQX อ้างว่ารองรับ 100 ล้าน concurrent connections

## ข้อโต้แย้ง / ความขัดแย้ง

*(wiki ยังใหม่ ยังไม่มีข้อมูลเดิมให้เปรียบเทียบ)*

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/mqtt-protocol]] — สร้างใหม่
- [[entities/iot/mosquitto]] — สร้างใหม่
- [[entities/iot/home-assistant]] — สร้างใหม่
- [[concepts/iot/publish-subscribe]] — สร้างใหม่
- [[concepts/iot/mqtt-qos]] — สร้างใหม่
