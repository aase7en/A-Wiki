---
type: concept
tags: [mqtt, qos, reliability, messaging]
sources: [mqtt-introduction, wiki/sources/iot/mqtt-protocol-overview.md]
created: 2026-04-18
updated: 2026-04-18
---

# MQTT Quality of Service (QoS)

## นิยาม

QoS ใน MQTT กำหนดระดับความมั่นใจในการส่งข้อความ มี 3 ระดับ แต่ละระดับแลก tradeoff ระหว่าง reliability กับ performance

## ทำไมถึงสำคัญใน IoT

อุปกรณ์ IoT อยู่ในสภาวะเครือข่ายไม่เสถียร การเลือก QoS ผิดทำให้:
- QoS 0 บน sensor critical → ข้อมูลหายโดยไม่รู้ตัว
- QoS 2 บน sensor ที่อ่านทุกวินาที → battery และ bandwidth สิ้นเปลือง

## วิธีการทำงาน

| QoS | ชื่อ | Handshake | ผลลัพธ์ |
|-----|------|-----------|---------|
| 0 | At most once | ไม่มี | ส่งครั้งเดียว อาจหาย |
| 1 | At least once | PUBACK | รับแน่นอน อาจซ้ำ |
| 2 | Exactly once | PUBREC→PUBREL→PUBCOMP | รับแน่นอน ไม่ซ้ำ |

## ตัวอย่างการใช้งาน

- **QoS 0**: อุณหภูมิที่อ่านทุก 5 วินาที — หายไปครั้งนึงไม่เป็นไร
- **QoS 1**: การแจ้งเตือน door sensor เปิด — ต้องได้รับ ซ้ำได้รับมือได้
- **QoS 2**: คำสั่ง actuator (เปิด/ปิดวาล์ว) — ต้องทำครั้งเดียวเท่านั้น

## ข้อควรระวัง

- QoS เป็น end-to-end ระหว่าง publisher กับ broker และ broker กับ subscriber แยกกัน
- Broker อาจ downgrade QoS ถ้า subscriber ขอ QoS ต่ำกว่า
- QoS 2 ช้าที่สุด ใช้เฉพาะเมื่อ duplicate action มีผลเสีย

## ความสัมพันธ์

- ส่วนหนึ่งของ: [[entities/iot/mqtt-protocol]]
- แนวคิดพื้นฐาน: [[concepts/iot/publish-subscribe]]

## แหล่งข้อมูล

- [[sources/mqtt-introduction]]
