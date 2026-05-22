---
type: source
title: "ข้อมูล Datasheet ของ DX-LR02 (DX-SMART)"
slug: dx-lr02-datasheet
date_ingested: 2026-04-18
original_file: raw/ข้อมูล datasheet ของ DX-LR02 .md
tags: [dx-lr02, lora, llcc68, semtech, uart, datasheet, firmware]
---

# ข้อมูล Datasheet ของ DX-LR02

**ประเภท**: datasheet / manufacturer documentation
**วันที่**: unknown
**ผู้เผยแพร่**: DX-SMART (szdx-smart.com)

## ประเด็นหลัก

1. **Chip**: LLCC68 โดย Semtech — ไม่ใช่ SX1276! LLCC68 เป็นชิปรุ่นใหม่ในตระกูล sub-GHz LoRa (150-960 MHz)
2. **Development environment**: Keil uVision5 (สำหรับ firmware ของ module เอง — ไม่ใช่ Arduino)
3. **Driver**: CH341SER — USB-to-UART driver สำหรับ config module ผ่าน PC
4. **2 hardware versions**: LR20/30 series มีทั้ง "old model" และ "new model" — ต้องตรวจสอบ order ก่อน burn firmware
5. **Chip link**: https://www.semtech.cn/products/wireless-rf/lora-connect/llcc68

## DFU Mode (Firmware Burning)

```
Flow: Install CH341SER driver → UartAssist.exe → mcuisp.exe → burn firmware
```

ถ้าเข้า DFU mode ไม่ได้:
1. ตรวจสอบ USB connection
2. ติดตั้ง CH341SER driver ก่อน
3. ดู tutorial video ตาม hardware version ที่มี

## ⚠️ Contradiction พบ

**LLCC68 ≠ SX1276** — source บาง files (เช่น Heltec boards) ใช้ SX1262/SX1276 ซึ่งต่างจาก DX-LR02 ที่ใช้ LLCC68
- LLCC68: LoRa + (G)FSK, sub-GHz 150-960 MHz, ออกแบบ industrial/IoT
- SX1276: LoRa + FSK, 137-1020 MHz (ครอบคลุมกว้างกว่า)
- ทั้งคู่เป็น Semtech, ใช้ LoRa CSS modulation เหมือนกัน

**ผลต่อโปรเจ็ค**: DX-LR02 ใช้ UART transparent mode — ไม่ต้องรู้ว่า chip คืออะไร code ส่วน MCU (ESP32) ไม่เปลี่ยน

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/dx-lr02-lora]] — เพิ่ม LLCC68 chip info, driver info
