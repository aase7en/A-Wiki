---
type: entity
category: platform
tags: [arduino-ide, development-tool, esp32, programming, beginner]
sources: [arduino-ide-esp32-setup, esp32-complete-guide-thai, platformio-esp32-guide]
created: 2026-04-18
updated: 2026-04-18
---

# Arduino IDE

**ผู้พัฒนา**: Arduino LLC / Arduino AG
**License**: Open source
**เวอร์ชันแนะนำ**: 2.x (ใหม่กว่า, เร็วกว่า, autocomplete ดีกว่า)
**บทบาทในโปรเจ็ค**: IDE หลักสำหรับ flash firmware บน ESP32/ESP32-S3

## ภาพรวม

Arduino IDE เป็น IDE ที่ง่ายที่สุดสำหรับเขียนโปรแกรม MCU — รองรับ Arduino, ESP32, ESP8266 และอื่นๆ อีกมาก ผ่าน Board Manager ไม่ต้องตั้งค่าซับซ้อน ดาวน์โหลดแล้วใช้ได้เลย

## คุณสมบัติหลัก

- **Code Editor**: syntax highlighting, autocomplete (IDE 2.x)
- **Verify / Upload**: compile และ flash ผ่านปุ่มเดียว
- **Serial Monitor**: debug ผ่าน Serial.print() real-time
- **Serial Plotter**: graph sensor data ได้ทันที — ดี debug DHT11
- **Board Manager**: เพิ่ม ESP32, ESP8266 support
- **Library Manager**: ติดตั้ง library ง่าย (PubSubClient, DHT, LoRa ฯลฯ)

## เพิ่ม ESP32 Board Support

```
File → Preferences → Additional Boards Manager URLs:
https://espressif.github.io/arduino-esp32/package_esp32_index.json

Tools → Board → Boards Manager → ค้นหา "esp32" → Install "esp32 by Espressif Systems"
Tools → Board → ESP32 Arduino → ESP32 Dev Module  (สำหรับ ESP32 DevKit V1)
Tools → Board → ESP32 Arduino → ESP32S3 Dev Module (สำหรับ ESP32-S3)
```

## Arduino IDE vs PlatformIO

| หัวข้อ | Arduino IDE 2 | [[entities/iot/platformio]] |
|--------|--------------|---------|
| ง่ายสำหรับ beginner | ✅ มาก | ⬜ ต้องตั้งค่า |
| IntelliSense | ⬜ จำกัด | ✅ เต็มที่ |
| Dependency management | ⬜ manual | ✅ platformio.ini |
| เหมาะกับ | เรียนรู้, prototype | production, team |

## ความสัมพันธ์

- ใช้กับ: [[entities/iot/esp32]], [[entities/iot/esp32-s3]], [[entities/iot/arduino-uno-r3]]
- ทางเลือก: [[entities/iot/platformio]], [[entities/iot/esp-idf]]

## แหล่งข้อมูล

- [[sources/arduino-ide-esp32-setup]] — ขั้นตอนติดตั้ง + ESP32 Board Manager
- [[sources/esp32-complete-guide-thai]] — Arduino IDE URL
