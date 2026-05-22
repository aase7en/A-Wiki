---
type: source
title: "How LoRaWAN Network Works: A Beginner's Guide"
slug: lorawan-network-beginner
date_ingested: 2026-04-18
original_file: raw/How LoRaWAN Network Works A Beginner.md
tags: [lorawan, network, architecture, star-topology, gateway, network-server]
---

# How LoRaWAN Network Works: A Beginner's Guide

**ประเภท**: article
**วันที่**: 2025-08-22
**ผู้เขียน**: UniConverge Technologies

## ประเด็นหลัก

1. **LoRa vs LoRaWAN**: LoRa = radio technology (physical layer), LoRaWAN = network protocol (rules + routing + security บน LoRa)
2. **Star topology**: LoRaWAN ใช้ star topology — end-device ส่งหา gateway ตรง ไม่ mesh
3. **3-layer architecture**: End-devices → Gateways → Network Server (LNS) → Application Server
4. **One gateway, thousands of devices**: gateway เดียวรองรับอุปกรณ์ได้มากเพราะ LoRa bandwidth ต่ำมาก
5. **LoRa Alliance**: organization ที่ดูแล LoRaWAN spec — open, secure, scalable

## LoRaWAN Architecture

```
[End-device]  ~~LoRa~~  [Gateway]
                              ↓ IP
                    [Network Server (LNS)]
                              ↓
                    [Application Server]
                              ↓
                    [User Application / Dashboard]
```

## ข้อมูลที่น่าสนใจ

- End-device ใน LoRaWAN มี 3 classes: A (most power-efficient), B (beacon), C (always-on)
- Security: OTAA (Over-the-Air Activation) หรือ ABP (Activation by Personalization)
- LoRaWAN ใช้ AES-128 encryption
- Network Server ตัวอย่าง: The Things Network (TTN), ChirpStack (self-hosted)

## เปรียบเทียบกับโปรเจ็คปัจจุบัน

| | โปรเจ็คนี้ (LoRa P2P) | LoRaWAN |
|--|----------------------|---------|
| Gateway | ESP32-S3 (custom) | LoRaWAN-compliant gateway |
| Network Server | ไม่มี (direct to MQTT) | TTN / ChirpStack |
| Scale | 1 node | หลายพัน nodes |
| Security | ไม่มี encryption | AES-128 |

## หน้า Wiki ที่ได้รับการอัปเดต

- [[concepts/iot/lorawan]] — สร้างใหม่ (ข้อมูลหลัก)
- [[entities/iot/the-things-network]] — อ้างอิง
