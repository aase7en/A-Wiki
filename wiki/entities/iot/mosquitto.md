---
type: entity
category: project
tags: [mqtt, broker, open-source, eclipse, edge]
sources: [mqtt-introduction]
created: 2026-04-18
updated: 2026-04-18
---

# Eclipse Mosquitto

**ประเภท**: MQTT Broker (Open Source)  
**ผู้พัฒนา**: Eclipse Foundation  
**License**: EPL/EDL  
**เวอร์ชัน MQTT**: 3.1, 3.1.1, 5.0

## ภาพรวม

Mosquitto เป็น MQTT broker ที่ได้รับความนิยมสูงสุดในโลก open source มีน้ำหนักเบามาก เหมาะสำหรับ deployment บน Raspberry Pi หรืออุปกรณ์ edge ที่มีทรัพยากรจำกัด

## คุณสมบัติหลัก

- ใช้ RAM น้อยมาก — รันบน Raspberry Pi Zero ได้สบาย
- รองรับ MQTT 3.1, 3.1.1, และ 5.0
- TLS/SSL และ WebSocket support
- Plugin API สำหรับ authentication/authorization

## การใช้งานใน IoT

เหมาะมากสำหรับ home lab, self-hosted home automation, และ edge gateway ขนาดเล็ก ไม่แนะนำสำหรับ production ที่ต้องการ > 10,000 concurrent connections (ใช้ EMQX หรือ HiveMQ แทน)

## ความสัมพันธ์

- ใช้งานโปรโตคอล: [[entities/iot/mqtt-protocol]]
- ใช้ร่วมกับ: [[entities/iot/home-assistant]]
- แข่งขันกับ: [[entities/iot/emqx]] (ยังไม่มีหน้า), HiveMQ (ยังไม่มีหน้า)

## แหล่งข้อมูล

- [[sources/mqtt-introduction]]
