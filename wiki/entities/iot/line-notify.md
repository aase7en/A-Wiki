---
type: entity
category: platform
tags: [line, notification, thailand, deprecated, messaging]
sources: [iot-lora-gateway-architecture]
created: 2026-04-18
updated: 2026-04-18
---

# Line Notify

**ผู้ให้บริการ**: LINE Corporation  
**สถานะ**: ⚠️ **DEPRECATED — หยุดให้บริการ 31 มีนาคม 2025**  
**ทางเลือก**: Line Messaging API (ซับซ้อนกว่า) หรือ [[entities/iot/telegram-bot]]

## ภาพรวม

Line Notify เป็น service ที่ให้ส่งข้อความเข้า Line chat ผ่าน HTTP POST ง่ายมาก แต่ **ปิดให้บริการแล้วตั้งแต่ 31 มีนาคม 2025** ไม่สามารถใช้งานได้อีกแล้ว

## ⚠️ ข้อขัดแย้งกับ Architecture Diagram

Architecture diagram ที่ ingest เข้ามาระบุ "Line Notify" เป็น service ปลายทาง แต่ **Line Notify deprecated แล้ว** ต้องเปลี่ยนเป็น Line Messaging API หรือย้ายไปใช้ Telegram แทน

## ทางเลือกแทน Line Notify

### 1. Line Messaging API (Messaging API)
- สมัครที่ LINE Developers Console
- สร้าง Channel → ได้ `Channel Access Token`
- ซับซ้อนกว่า Line Notify แต่ยังรองรับอยู่

### 2. Telegram Bot (แนะนำสำหรับ IoT)
- ดูรายละเอียดที่ [[entities/iot/telegram-bot]]
- API ง่ายกว่า, ฟรี, ไม่มี deprecation risk

## ความสัมพันธ์

- แทนที่ด้วย: [[entities/iot/telegram-bot]] (แนะนำ)
- Subscribe จาก: [[entities/iot/mosquitto]]

## แหล่งข้อมูล

- [[sources/iot-lora-gateway-architecture]] — ระบุใน diagram แต่ deprecated แล้ว
