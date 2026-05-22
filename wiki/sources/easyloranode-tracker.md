---
type: source
title: "EasyLoRaNode_Tracker: Wearable LoRa Node with Battery"
slug: easyloranode-tracker
date_ingested: 2026-04-18
original_file: raw/IoTThinksEasyLoRaNode_Tracker A wearable LoRa node with battery for long range wearable projects.md
tags: [lora, esp32, wearable, deep-sleep, battery, github, tracker]
---

# EasyLoRaNode_Tracker: Wearable LoRa Node with Battery

**ประเภท**: GitHub project
**วันที่**: unknown
**ผู้เขียน**: IoTThinks (GitHub)

## ประเด็นหลัก

1. **Deep sleep < 15µA**: design เน้น ultra-low power — วัด battery voltage ด้วย BAT_METER pin
2. **ESP32-Pico-D4**: SoC รุ่นเล็ก (embedded flash) เหมาะ wearable ขนาดเล็ก
3. **LoRa SPI pins**: LORA_SS/SCK/MOSI/MISO/DIO0/DIO1/DIO2/RESET — ใช้ sandeepmistry/arduino-LoRa
4. **LORA_POWER pin**: สามารถปิด power LoRa module ได้เพื่อประหยัดพลังงาน

## Pin Mapping ที่น่าสนใจ

```cpp
#define LORA_POWER 21  // LOW=off, HIGH=on
#define LORA_SS    25
#define LORA_SCK   18
#define LORA_MOSI  23
#define LORA_MISO  19
#define LORA_DIO0  26
#define BAT_METER  36  // อ่าน battery voltage
```

## ข้อมูลที่น่าสนใจ

- Pattern `LORA_POWER` pin ให้ปิดโมดูล LoRa ทั้งหมดได้เมื่อไม่ใช้ — ประหยัดพลังงานมาก
- GPIO 16 ใช้โดย internal flash ของ Pico — ห้ามใช้

## เกี่ยวข้องกับโปรเจ็คนี้แค่ไหน

**Deep sleep + battery optimization** เป็นแนวคิดที่ apply ได้กับ ESP32 Sensor Node ในโปรเจ็คปัจจุบัน (Phase 5 ของ implementation plan)

## หน้า Wiki ที่ได้รับการอัปเดต

- [[concepts/iot/lora-p2p]] — เพิ่ม power optimization tip
