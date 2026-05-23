---
type: concept
tags: [architecture, messaging, pattern, decoupling, iot-core]
sources: [mqtt-introduction]
created: 2026-04-18
updated: 2026-04-18
---

# Publish-Subscribe Pattern

## นิยาม

Publish-Subscribe (pub/sub) เป็น messaging pattern ที่ผู้ส่งข้อความ (publisher) ไม่ส่งตรงถึงผู้รับ (subscriber) แต่ส่งผ่าน **broker** กลาง ผู้รับแจ้งความสนใจผ่าน **topics** และรับเฉพาะข้อความที่ตรงกัน

## ทำไมถึงสำคัญใน IoT

IoT มีอุปกรณ์จำนวนมากที่ต้องการแลกเปลี่ยนข้อมูลโดยไม่รู้จักกันล่วงหน้า Pub/sub แก้ปัญหานี้:
- อุปกรณ์ใหม่ subscribe เข้ามาได้โดยไม่กระทบระบบเดิม
- Publisher ไม่ต้องรู้ว่ามีใคร subscribe อยู่
- Broker ทำหน้าที่ buffer เมื่ออุปกรณ์ offline

## วิธีการทำงาน

```
[Sensor] --publish("home/temp", 25)--> [Broker] --forward--> [Dashboard]
                                                  --forward--> [AC Controller]
                                                  --forward--> [Logger]
```

## ตัวอย่างการใช้งาน

- MQTT topic: `factory/line-1/machine-3/temperature`
- Subscriber ของ `factory/#` ได้รับข้อมูลทุก machine ทุก line
- Subscriber ของ `factory/line-1/+/temperature` ได้เฉพาะอุณหภูมิ line-1

## ข้อดี / ข้อเสีย

| ข้อดี | ข้อเสีย |
|-------|---------|
| Decoupling สูง — publisher/subscriber ไม่รู้จักกัน | Broker เป็น single point of failure |
| Scale ได้ง่าย — เพิ่ม subscriber โดยไม่ต้องแก้ publisher | Debugging ยากกว่า request-response |
| Async — publisher ไม่ต้องรอ response | ไม่รู้ว่ามีคนรับข้อความหรือเปล่า (QoS 0) |
| Fan-out ง่าย — 1 message ถึงหลาย subscriber | Latency ขึ้นอยู่กับ broker |

## ความสัมพันธ์

- ใช้งานโดย: [[entities/iot/mqtt-protocol]]
- แนวคิดเกี่ยวข้อง: [[concepts/iot/mqtt-qos]]
- เปรียบเทียบกับ: Request-Response (HTTP pattern)

## แหล่งข้อมูล

- [[sources/mqtt-introduction]]
