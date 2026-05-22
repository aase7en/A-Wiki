---
type: source
title: "DX-LR02/LR03 Module Demo & AT Commands (Video Transcript)"
slug: dx-lr02-at-commands-demo
date_ingested: 2026-04-18
original_file: raw/Note Taking & Research Assistant Powered by AI.md
tags: [dx-lr02, lora, at-commands, uart, transparent-mode, ch340, 900mhz, 433mhz]
---

# DX-LR02/LR03 Module Demo & AT Commands

**ประเภท**: video transcript (YouTube — DX-SMART official demo)
**วันที่**: unknown
**ผู้เผยแพร่**: DX-SMART

> ⚠️ ไฟล์นี้ถูกบันทึกในชื่อ "Note Taking & Research Assistant" แต่เนื้อหาจริงคือ transcript วิดีโอ demo DX-LR02

## ประเด็นหลัก

1. **2 Frequency bands**: DX-LR02 มี **2 รุ่น** คือ 430-475 MHz และ 850-930 MHz — ต้องซื้อให้ตรงกัน
2. **Baud rate default: 9600** — ตั้งค่า serial port 9600 เสมอ
3. **Driver: CH340** — ไม่ใช่ CH341SER แต่เป็น CH340 driver
4. **ข้อสำคัญด้านความปลอดภัย**: ต้องต่อเสาอากาศก่อนเปิดไฟ **เสมอ** — ถ้าไม่มีเสา RF power จะไม่ระบาย → วงจรภายในพัง
5. **Status indicators**: Power LED = steady, Module LED = blink → ปกติ, พร้อมรับส่ง
6. **LR03**: รุ่นขยาย range สูงสุด **10 กิโลเมตร** (พร้อม package ครบ)

## Transparent Transmission Mode

DX-LR02 ทำงานใน "Transparent Transmission" mode:
- ข้อมูลที่ส่งเข้า UART ฝั่ง Transmitter → ออกมาที่ UART ฝั่ง Receiver โดยตรง
- MCU (ESP32) ไม่ต้องรู้จัก LoRa protocol เลย — แค่เขียน Serial.write() ก็ส่งได้

## Quick Start Checklist (จาก video)

```
1. ต่อเสาอากาศก่อนจ่ายไฟ ← สำคัญมาก
2. ติดตั้ง CH340 driver
3. เปิด UART Assist serial tool
4. เลือก COM port ที่ถูก
5. ตั้ง Baud Rate = 9600
6. เปิด "auto append bytes" option
7. ส่ง AT command เพื่อ verify การเชื่อมต่อ
8. ยืนยัน TX/RX คู่กัน → เข้า transparent mode
```

## Developer Package Contents

- DX-LR02 × 2 modules
- Rubber duck antennas × 2
- Data cables × 2
- Product manual × 1
- USB-to-TTL adapters × 2
- Spacers + screws × 2 sets

## ข้อโต้แย้งหรือความขัดแย้ง

**Driver ต่างกัน**: datasheet file ระบุ CH341SER แต่ video ระบุ CH340 — น่าจะเป็น CH340 chip (ซึ่ง driver ก็ชื่อ CH340) การเรียก CH341SER อาจหมายถึงชื่อไฟล์ installer ไม่ใช่ชื่อ chip

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/dx-lr02-lora]] — **เพิ่มข้อมูลสำคัญ**: 2 frequency bands, baud rate 9600, CH340, safety warning, transparent mode
