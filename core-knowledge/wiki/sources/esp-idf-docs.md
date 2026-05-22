---
type: source
title: "ESP-IDF: Espressif IoT Development Framework (Official)"
slug: esp-idf-docs
date_ingested: 2026-04-18
original_file: raw/espressifesp-idf Espressif IoT Development Framework. Official development framework for Espressif SoCs..md
tags: [esp-idf, espressif, framework, cmake, c-programming, advanced]
---

# ESP-IDF: Espressif IoT Development Framework

**ประเภท**: GitHub repo + official documentation
**ผู้พัฒนา**: Espressif Systems

## ประเด็นหลัก

1. **ESP-IDF คือ native framework** ของ Espressif — ต่างจาก Arduino framework ตรงที่ใช้ C/C++ ล้วน + CMake
2. **Version ปัจจุบัน**: v6.0 (stable) — v4.4 ที่บันทึกไว้เป็น EOL แล้ว
3. **รองรับทุก Espressif SoC**: ESP32, ESP32-S2, ESP32-S3, ESP32-C3, ESP32-H2 ฯลฯ
4. **อดีต ESP8266**: ใช้ ESP8266 RTOS SDK แยก (ไม่ใช่ ESP-IDF)

## ESP-IDF vs Arduino Framework

| หัวข้อ | Arduino Framework | ESP-IDF |
|--------|------------------|---------|
| Language | C++ (simplified) | C/C++ |
| Build system | Arduino IDE / PlatformIO | CMake + idf.py |
| Abstraction | สูง (ง่าย) | ต่ำ (control เต็มที่) |
| RTOS | ซ่อน FreeRTOS | เปิดเผย FreeRTOS API |
| Community | ใหญ่กว่า | เล็กกว่า (แต่ professional) |
| เหมาะกับ | Maker, prototype | Production, advanced |

## เหมาะสำหรับโปรเจ็คนี้ไหม

**Arduino framework เพียงพอ** สำหรับโปรเจ็คปัจจุบัน (DHT11 + LoRa + MQTT)
ESP-IDF จำเป็นถ้าต้องการ:
- FreeRTOS task แยก (concurrent LoRa receive + MQTT publish)
- Deep sleep control ละเอียด (wake stub, ULP coprocessor)
- Custom partition table สำหรับ OTA update

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/esp-idf]] — สร้างใหม่
