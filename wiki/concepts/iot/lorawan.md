---
type: concept
tags: [lorawan, lora, network-protocol, lpwan, ttn, chirpstack, iot-network]
sources: [lorawan-network-beginner, esp32-lora-gateway-sparkfun, lorawan-fuota-rak3172]
created: 2026-04-18
updated: 2026-04-18
---

# LoRaWAN

## นิยาม

LoRaWAN (Long Range Wide Area Network) คือ **network protocol** ที่ทำงานบน LoRa radio กำหนด rules สำหรับการ routing, security, และ device management ในเครือข่าย IoT ขนาดใหญ่ พัฒนาและดูแลโดย LoRa Alliance

> **LoRa ≠ LoRaWAN** — LoRa คือ radio technology (physical layer), LoRaWAN คือ network protocol (MAC layer ขึ้นไป)

## ทำไมถึงสำคัญใน IoT

LoRaWAN ทำให้ scale ระบบ IoT ได้จาก 1 node เป็นหลายพัน node บน gateway เดียวกัน พร้อม security (AES-128), device management, และ OTA update (FUOTA)

## วิธีการทำงาน

**Architecture (Star topology):**
```
[End-device A]──┐
[End-device B]──┤ ~~LoRa~~ [Gateway] ──IP──> [Network Server (LNS)]
[End-device C]──┘                                      ↓
                                             [Application Server]
                                                       ↓
                                               [Dashboard / App]
```

**3 Layers:**
| Layer | ส่วนประกอบ | หน้าที่ |
|-------|-----------|--------|
| Perception | End-device (sensor + LoRa module) | เก็บและส่งข้อมูล |
| Transport | Gateway | รับ LoRa signal, ส่งต่อทาง IP |
| Application | Network Server + Application Server | route, decrypt, ส่ง app |

## Device Classes

| Class | รับ downlink | Power | เหมาะกับ |
|-------|------------|-------|---------|
| A | หลัง uplink เท่านั้น (2 windows) | ต่ำที่สุด | sensor node, battery |
| B | beacon-synchronized slots | กลาง | actuator ที่ต้องรับ command |
| C | ตลอดเวลา (always-on) | สูง | mains-powered device |

## Security

- **OTAA** (Over-the-Air Activation): device join network ผ่าน DevEUI/AppKey — session keys สร้างใหม่ทุกครั้ง (แนะนำ)
- **ABP** (Activation by Personalization): hardcode session keys — ง่ายกว่าแต่ไม่ปลอดภัยเท่า
- Encryption: AES-128 ทั้ง network layer และ application layer

## Network Server Options

| Network Server | ประเภท | ข้อดี |
|----------------|--------|-------|
| The Things Network (TTN) | cloud, free tier | ง่าย, community ใหญ่ |
| ChirpStack | self-hosted, open-source | control เต็มที่, ไม่ขึ้น cloud |
| AWS IoT Core for LoRaWAN | managed cloud | integrate AWS ได้ |

## LoRaWAN vs LoRa P2P (โปรเจ็คนี้)

| หัวข้อ | LoRa P2P (โปรเจ็คนี้) | LoRaWAN |
|--------|----------------------|---------|
| Scale | 1-2 nodes | หลายพัน nodes |
| Gateway | ESP32-S3 custom | LoRaWAN-compliant HW |
| Network Server | ไม่มี | TTN/ChirpStack |
| Security | ไม่มี encryption | AES-128 |
| Setup | ง่าย | ซับซ้อน |
| ใช้เมื่อ | lab, prototype | production, scale-up |

## FUOTA (Firmware Update OTA)

LoRaWAN รองรับ Firmware Update Over-the-Air โดยส่ง firmware fragments ผ่าน multicast (Class C) — ดู [[sources/lorawan-fuota-rak3172]] สำหรับ demo

## ความสัมพันธ์

- Physical layer: [[concepts/iot/lora]]
- Protocol เปรียบเทียบ: [[concepts/iot/lora-p2p]]
- Network Server: [[entities/iot/the-things-network]]
- Hardware ที่เข้ากัน: [[entities/iot/rfm95-sx1276]]

## แหล่งข้อมูล

- [[sources/lorawan-network-beginner]] — architecture และ concept
- [[sources/esp32-lora-gateway-sparkfun]] — single-channel gateway + TTN
- [[sources/lorawan-fuota-rak3172]] — FUOTA demo
