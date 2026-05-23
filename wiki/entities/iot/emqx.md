---
type: entity
category: project
tags: [mqtt, broker, enterprise, open-source, high-scale]
sources: [mqtt-introduction]
created: 2026-04-18
updated: 2026-04-18
---

# EMQX

**ประเภท**: MQTT Broker (Open Source / Enterprise)  
**ผู้พัฒนา**: EMQ Technologies  
**License**: Apache 2.0 (Community), Commercial (Enterprise)  
**เวอร์ชัน MQTT**: 3.1, 3.1.1, 5.0

## ภาพรวม

EMQX เป็น MQTT broker ที่ออกแบบมาสำหรับ scale ขนาดใหญ่ อ้างว่ารองรับ **100 ล้าน concurrent connections** บน cluster เดียว เหมาะสำหรับ production IoT platform ที่มี device จำนวนมาก ต่างจาก Mosquitto ที่เน้น lightweight สำหรับ edge

## คุณสมบัติหลัก

- Clustered deployment — horizontal scale ได้
- Built-in dashboard และ REST API สำหรับ management
- Rule Engine — route messages ไปยัง database/webhook ได้โดยตรง
- รองรับ MQTT over WebSocket, TLS, QUIC (enterprise)
- Authentication: username/password, JWT, X.509 certificates, LDAP

## การใช้งานใน IoT

เหมาะสำหรับ:
- Production platform ที่มี > 10,000 concurrent devices
- ระบบที่ต้องการ built-in monitoring และ management UI
- Integration กับ databases (MySQL, InfluxDB, Kafka) ผ่าน Rule Engine

ไม่จำเป็นสำหรับ:
- Home lab หรือโปรเจ็คส่วนตัวที่มีอุปกรณ์ไม่กี่ตัว — ใช้ Mosquitto แทน

## ความสัมพันธ์

- แข่งขันกับ: [[entities/iot/mosquitto]] (lightweight, edge), HiveMQ (enterprise)
- ใช้งานโปรโตคอล: [[entities/iot/mqtt-protocol]]
- ใช้ร่วมกับ: [[entities/iot/node-red]], [[entities/iot/grafana]]

## แหล่งข้อมูล

- [[sources/mqtt-introduction]] — กล่าวถึง EMQX ในฐานะ high-scale broker (100M connections claim)
