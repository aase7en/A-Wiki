---
type: entity
category: project
tags: [simulator, arduino, esp32, raspberry-pi, open-source, docker, web-based, wokwi-alternative]
sources: [velxio-arduino-esp32-pi-simulator]
created: 2026-05-30
updated: 2026-05-30
last_verified: 2026-05-30
verify_tool: WebFetch
---

# Velxio

**ประเภท**: Web-based open-source hardware simulator
**Repo/Image**: `ghcr.io/davidmonterocrespo24/velxio:master`
**License**: Open-source (Beta)
**สถานะใน Lab**: ⏳ ยังไม่ได้ทดลอง (candidate สำหรับ prototyping โดยไม่ต้องใช้บอร์ดจริง)

## ภาพรวม

Velxio เป็น simulator ในเบราว์เซอร์สำหรับ Arduino / ESP32 / Raspberry Pi ที่สร้างขึ้นโดยอ้างอิงสถาปัตยกรรมจาก **Wokwi** แต่เป็น open-source และ self-host ได้ด้วย Docker container เดียว จุดเด่นเหนือคู่แข่งคือ "heterogeneous board simulation" — ต่อ Arduino + ESP32 + RPi ในโปรเจ็คเดียวและให้สื่อสารกันผ่าน SPI/Serial ได้พร้อมกัน

ปัจจุบันยังเป็น **Beta** — Pi 3 console และ ESP-IDF compile ยังไม่สมบูรณ์ [verified 2026-05-30]

## คุณสมบัติหลัก

| คุณสมบัติ | รายละเอียด |
|----------|-----------|
| บอร์ดที่รองรับ | 19 รุ่นข้าม 5 architecture |
| AVR8 | Arduino UNO (ATmega/ATtiny) |
| Arm Cortex-M0+ | Raspberry Pi RP2040 (Pico) |
| RISC-V | ESP32-C3, CH32V003 |
| Xtensa LX6/LX7 | ESP32, ESP32-S3 (QEMU) |
| Arm Cortex-A53 | Raspberry Pi 3 Linux (QEMU) |
| Components | 48+ devices (LED, LCD, ปุ่ม, sensors) |
| IDE | Web-based, drag-and-drop circuit + code editor |
| Multi-board | ✅ ต่อหลายบอร์ดต่าง architecture ใน workspace เดียว |
| Deploy | `sudo docker run -d -p 3080:80 ghcr.io/davidmonterocrespo24/velxio:master` |
| Self-host | ✅ (ต้องการ Linux) |

## การใช้งานใน IoT

เหมาะกับ:

- **เรียน/สอน** — ทดสอบ code [[entities/iot/arduino-uno-r3]] หรือ [[entities/iot/esp32]] โดยไม่ต้องมีบอร์ดจริง
- **Rapid prototyping** — ลองวงจร LED/sensor ก่อนซื้อชิ้นส่วน
- **Multi-MCU bus design** — ทดสอบ ESP32 ↔ Arduino UART/SPI bridge ใน workspace เดียว ก่อนลงเข็มบอร์ด
- **CI verification** — รัน firmware ใน Docker เพื่อ smoke-test ก่อน flash

**ไม่เหมาะสำหรับ**:

- Verify firmware production-ready (ยัง Beta, peripheral simulation ไม่ครบ)
- ทดสอบ timing-critical (เช่น LoRa SF12, PWM แม่นยำสูง) — simulator เพี้ยนจากของจริงได้
- Sensor ที่ wiki มีในแล็บ ([[entities/iot/pms5003]], [[entities/iot/pzem-004t]], [[entities/iot/dx-lr02-lora]]) — ไม่อยู่ใน 48 components built-in

## ข้อจำกัด (Beta)

- Raspberry Pi 3 serial console รองรับไม่ครบ
- ESP-IDF compile flow ยังบางส่วน — ผู้ใช้ ESP-IDF เต็มรูป ([[entities/iot/esp-idf]]) ควรใช้ของจริงคู่กัน
- Self-host requires Linux host

## ความสัมพันธ์

- **แข่งขันกับ**: Wokwi (cloud, freemium, peripheral มากกว่า), Tinkercad Circuits (Arduino only), Proteus (paid, professional)
- **ใช้ร่วมกับ**: [[entities/iot/arduino-ide]], [[entities/iot/platformio]] — flow: prototype ใน Velxio → build จริงด้วย Arduino IDE/PlatformIO
- **บอร์ดที่ simulate ได้และมีในแล็บ**: [[entities/iot/arduino-uno-r3]], [[entities/iot/esp32]], [[entities/iot/esp32-s3]]
- **บอร์ดที่ simulate ได้ แต่ยังไม่มีในแล็บ**: ESP32-C3, RP2040 (Raspberry Pi Pico), CH32V003

## แหล่งข้อมูล

- [[sources/velxio-arduino-esp32-pi-simulator]] — Global Byte Shop project blog (ingested 2026-05-30 via WebFetch)
- Source URL: https://globalbyteshop.com/blogs/projects/velxio-arduino-esp32-raspberry-pi-simulator
- Docker image: `ghcr.io/davidmonterocrespo24/velxio:master`
