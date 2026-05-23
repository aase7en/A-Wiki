---
type: entity
category: platform
tags: [esp-idf, espressif, cmake, freertos, c-programming, advanced, native]
sources: [esp-idf-docs]
created: 2026-04-18
updated: 2026-04-18
---

# ESP-IDF (Espressif IoT Development Framework)

**ผู้พัฒนา**: Espressif Systems
**License**: Apache 2.0
**เวอร์ชันปัจจุบัน**: v6.0 (stable) — v4.4 เป็น EOL แล้ว
**บทบาทในโปรเจ็ค**: Advanced option (ไม่จำเป็นสำหรับโปรเจ็คปัจจุบัน)

## ภาพรวม

ESP-IDF คือ official framework ของ Espressif สำหรับพัฒนา firmware บน ESP32 ทุกรุ่น ใช้ CMake build system และเปิดเผย FreeRTOS API โดยตรง ให้ control ระดับต่ำกว่า Arduino framework มาก

## เมื่อไหร่ควรเปลี่ยนจาก Arduino → ESP-IDF

Arduino framework เพียงพอสำหรับโปรเจ็คส่วนใหญ่ แต่ ESP-IDF จำเป็นเมื่อ:
- ต้องการ FreeRTOS tasks หลายตัว (เช่น LoRa receive task + MQTT publish task ต่างหาก)
- Deep sleep ละเอียด (ULP coprocessor, custom wake stub)
- OTA firmware update ผ่าน partition table ที่กำหนดเอง
- Production code ที่ต้องการ stability สูงสุด
- Ethernet, USB HID/CDC custom profiles

## ESP-IDF vs Arduino

| หัวข้อ | Arduino | ESP-IDF |
|--------|---------|---------|
| Language | C++ (simplified) | C/C++ |
| Build | Arduino IDE / PlatformIO | CMake + idf.py |
| FreeRTOS | ซ่อน | เปิดเผย API |
| Abstraction | สูง (ง่าย) | ต่ำ (control) |
| เหมาะกับ | Maker, prototype | Production, advanced |

## SoC Compatibility

รองรับ: ESP32, ESP32-S2, ESP32-S3, ESP32-C3, ESP32-C6, ESP32-H2
ไม่รองรับ: ESP8266 (ใช้ ESP8266 RTOS SDK แยก)

## ความสัมพันธ์

- ทางเลือก (ง่ายกว่า): [[entities/iot/arduino-ide]], [[entities/iot/platformio]]
- ใช้กับ: [[entities/iot/esp32]], [[entities/iot/esp32-s3]]

## แหล่งข้อมูล

- [[sources/esp-idf-docs]] — official docs + GitHub repo
