---
type: entity
category: device
tags: [esp32, microcontroller, wifi, bluetooth, espressif, iot-core]
sources: [hardware-inventory-2026-04-18, mqtt-introduction, esp32-complete-guide-thai, arduino-ide-esp32-setup]
created: 2026-04-18
updated: 2026-04-18
---

# ESP32 DevKit V1

**ผู้ผลิต**: Espressif Systems  
**รุ่นที่มีในแล็บ**: ESP32 DevKit V1 + Terminal Breakout Board  
**สถานะใน Lab**: ✅ มีอยู่ × 1

## ภาพรวม

ESP32 เป็น dual-core 32-bit MCU ที่ได้รับความนิยมสูงสุดใน IoT โลก มี WiFi 802.11 b/g/n และ Bluetooth 4.2/BLE built-in ในราคาถูก Espressif ออกแบบมาเพื่อ replace ESP8266 โดยเพิ่ม CPU cores, GPIO, และ peripheral

## Specs หลัก

| คุณสมบัติ | รายละเอียด |
|----------|-----------|
| CPU | Xtensa LX6 dual-core 240MHz |
| RAM | 520KB SRAM |
| Flash | 4MB (DevKit V1 ทั่วไป) |
| WiFi | 802.11 b/g/n 2.4GHz |
| Bluetooth | Classic BT 4.2 + BLE |
| GPIO | 34 pins |
| ADC | 18ch 12-bit |
| DAC | 2ch 8-bit |
| UART/SPI/I2C | 3/4/2 ตามลำดับ |
| Power | 3.3V (VIN 5V ผ่าน AMS1117) |
| Deep sleep current | ~10µA |

## Terminal Breakout Board

ESP32 ในแล็บนี้มาพร้อม breakout board ที่มี screw terminal ทุก pin — ทำให้ต่อสายได้โดยไม่ต้องบัดกรี เหมาะมากสำหรับ prototyping ระยะยาว

## การใช้งานใน IoT

- **WiFi node**: ส่งข้อมูล sensor ผ่าน MQTT หรือ HTTP REST
- **BLE beacon**: advertising ข้อมูลแบบ passive
- **LoRa gateway**: จับคู่กับ [[entities/iot/dx-lr02-lora]] ผ่าน UART
- **MQTT client**: ใช้ library `PubSubClient` หรือ `AsyncMqttClient`

## ข้อจำกัด

- ADC บน ESP32 classic มี non-linearity ที่ voltage สูง (>3V) — ใช้ ADC1 ดีกว่า ADC2 เมื่อใช้ WiFi
- GPIO 34-39 เป็น input-only
- ใช้ 3.3V logic ทุก pin (ห้ามต่อ 5V signal โดยตรง)

## โปรเจ็คที่วางแผน

- Temperature monitor ด้วย [[entities/iot/dht11]] → MQTT → Dashboard
- LoRa node ด้วย [[entities/iot/dx-lr02-lora]]

## Development Environment

| IDE/Framework | เหมาะกับ | Board Manager URL |
|--------------|---------|-----------------|
| [[entities/iot/arduino-ide]] | เริ่มต้น, prototype | `https://espressif.github.io/arduino-esp32/package_esp32_index.json` |
| [[entities/iot/platformio]] | professional, team | auto-detect จาก platformio.ini |
| [[entities/iot/esp-idf]] | production, advanced | idf.py install |

**แนะนำ: Arduino IDE 2.x** สำหรับโปรเจ็คนี้ (Phase 1-4 ทั้งหมด)

## ความสัมพันธ์

- รุ่นพี่/น้อง: [[entities/iot/esp32-s3]] (แรงกว่า, ML), [[entities/iot/esp32-c6]] (WiFi 6 + Thread/Zigbee), ESP8266 (รุ่นเก่า)
- ใช้งานโปรโตคอล: [[entities/iot/mqtt-protocol]]
- Sensor ที่ใช้ร่วม: [[entities/iot/dht11]], [[entities/iot/hc-sr501]]
- ใช้ร่วมกับ: [[entities/iot/dx-lr02-lora]], [[entities/iot/mosquitto]]

## แหล่งข้อมูล

- [[sources/hardware-inventory-2026-04-18]] — มีใน lab × 1 พร้อม terminal breakout
- [[sources/mqtt-introduction]] — กล่าวถึง ESP32 เป็น MQTT client platform
- [[sources/esp32-complete-guide-thai]] — specs ครบ, features overview
- [[sources/arduino-ide-esp32-setup]] — Board Manager URL, setup guide
