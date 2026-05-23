---
type: source
title: "Heltec ESP32 LoRa Libraries (Official + Unofficial)"
slug: heltec-libraries
date_ingested: 2026-04-18
original_file: raw/HelTecAutomationHeltec_ESP32 Arduino library for Heltec ESP32 (or ESP32+LoRa) based boards.md + raw/ropgheltec_esp32_lora_v3...md
tags: [heltec, esp32, lora, sx1262, radiolib, oled, arduino-library]
---

# Heltec ESP32 LoRa Libraries

**ประเภท**: GitHub repos (2 repos รวม)
**ผู้เขียน**: HelTecAutomation (official) + ropg (unofficial)

## ประเด็นหลัก

1. **Heltec WiFi LoRa 32 v3**: ESP32-S3 + SX1262 + 128×64 OLED — บอร์ดแบบ all-in-one
2. **Official library** (HelTecAutomation): LoRa + OLED + LoRaWAN examples, ใช้ Heltec radio stack เอง
3. **Unofficial library** (ropg): ใช้ **RadioLib** แทน — เสถียรกว่า, code คุณภาพดีกว่า, tested examples
4. **SX1262 chip**: 863-928 MHz — ใช้ใน Heltec v3 board (ต่างจาก DX-LR02 ที่ใช้ LLCC68)
5. **Include file เปลี่ยน**: `heltec.h` → `heltec_unofficial.h` ใน unofficial version

## เกี่ยวข้องกับโปรเจ็คนี้แค่ไหน

**ไม่เกี่ยวโดยตรง** — โปรเจ็คใช้ DX-LR02 (UART/LLCC68) ไม่ใช่ Heltec board (SPI/SX1262)

แต่มีประโยชน์เป็น **reference สำหรับ RadioLib** ซึ่งเป็น library LoRa ที่ดีที่สุดในตลาดตอนนี้

## RadioLib (ควรรู้จัก)

RadioLib เป็น universal radio library รองรับ SX1262, SX1276, LLCC68, CC1101 และอื่นๆ มากมาย — ถ้าโปรเจ็คอนาคตเปลี่ยนไปใช้ SPI LoRa module แนะนำ RadioLib แทน arduino-LoRa

## หน้า Wiki ที่ได้รับการอัปเดต

ไม่มีหน้าใหม่ที่จำเป็น — บันทึก RadioLib เป็น stub
