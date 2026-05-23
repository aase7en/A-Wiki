---
type: source
title: "Raspberry Pi and IoT: the guide to understanding their role in the Internet of Things"
slug: raspberry-pi-iot-guide
date_ingested: 2026-04-18
original_file: raw/Raspberry Pi and IoT the guide to understanding their role in the Internet of Things.md
tags: [raspberry-pi, iot, gateway, edge-computing, home-assistant, mosquitto, python]
---

# Raspberry Pi and IoT: The Complete Guide

**ประเภท**: article / guide
**วันที่**: unknown
**ผู้เผยแพร่**: monraspberry.com

## ประเด็นหลัก

1. **RPi เป็น "intelligent gateway"** — เก็บข้อมูลจาก sensor, ประมวลผล, ส่งต่อ cloud หรือ local server
2. **3 บทบาทหลัก**: IoT Gateway, Edge Computing node, Home Automation Server
3. **Protocol รองรับ**: WiFi, Bluetooth, Ethernet, GPIO, Zigbee, Z-Wave, LoRa, LTE dongle
4. **ราคา**: Pi Zero ~€5 ถึง Pi 5 ~€100 — ยังถูกสำหรับ production deployment
5. **Software stack**: Home Assistant, Node-RED, Mosquitto รันบน RPi ได้ดี

## บทบาทใน IoT

| บทบาท | รายละเอียด | เหมาะกับโปรเจ็คนี้ |
|-------|-----------|-------------------|
| **IoT Gateway** | รับ sensor data → ส่งต่อ cloud/local | ✅ รัน Mosquitto broker |
| **Edge Computing** | วิเคราะห์ data ก่อนส่ง cloud | ⬜ อนาคต |
| **Home Automation** | รัน Home Assistant, Node-RED | ⬜ optional |

## เหมาะกับโปรเจ็คนี้อย่างไร

RPi เป็นตัวเลือกที่ดีสำหรับ **production deployment ของ Mosquitto broker**:
- ใช้ไฟน้อย (เปิดตลอด 24 ชั่วโมงได้)
- รัน Mosquitto + Telegraf + InfluxDB + Grafana ได้พร้อมกัน
- ราคาถูก (Pi 4 ~$35–75)
- Linux OS ทำให้ต่อยอดได้ไม่จำกัด

ปัจจุบันโปรเจ็คใช้ Mac local สำหรับ dev — RPi เป็น upgrade path สำหรับ production

## ข้อมูลที่น่าสนใจ

- RPi 5 มี PCIe connector — รองรับ NVMe SSD ได้
- RPi Zero W (~€15) เพียงพอสำหรับ Mosquitto broker ขนาดเล็ก

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/raspberry-pi]] — สร้างใหม่
