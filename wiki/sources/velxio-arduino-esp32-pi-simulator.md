---
type: source
title: "Velxio — Open-Source Arduino/ESP32/Raspberry Pi Simulator"
slug: velxio-arduino-esp32-pi-simulator
date_ingested: 2026-05-30
original_file: raw/velxio-arduino-esp32-pi-simulator.md
url: https://globalbyteshop.com/blogs/projects/velxio-arduino-esp32-raspberry-pi-simulator
tags: [iot, simulator, arduino, esp32, raspberry-pi, open-source, wokwi-alternative]
---

# Velxio — Arduino/ESP32/Raspberry Pi Simulator

**ประเภท**: article (project blog post)
**วันที่**: unknown (verified 2026-05-30 via WebFetch)
**ผู้เขียน**: globalbyteshop.com (project: davidmonterocrespo24)
**License/Status**: Open-source, **Beta**

## ประเด็นหลัก

1. **Web-based hardware simulator** — เขียน/ทดสอบ firmware โดยไม่ต้องมีบอร์ดจริง คล้าย Wokwi (ใช้ Wokwi เป็น reference UI)
2. **Heterogeneous board simulation** — จุดเด่นเหนือคู่แข่ง: ต่อ Arduino + ESP32 + RPi ใน workspace เดียว สื่อสารกันผ่าน SPI/Serial
3. **Self-hosted ได้ด้วย Docker** — รันใน LAN ตัวเอง ไม่ผูก cloud
4. **รองรับ 19 บอร์ดข้าม 5 architecture** — AVR8, Arm Cortex-M0+, RISC-V, Xtensa LX6/LX7, Arm Cortex-A53
5. **48+ components** — LED, LCD, ปุ่ม, sensor หลากหลาย

## ข้อมูลที่น่าสนใจ / สถิติ

- **Supported boards**:
  - **AVR8**: Arduino UNO (ATmega/ATtiny)
  - **Arm Cortex-M0+**: Raspberry Pi RP2040
  - **RISC-V (RV32IMC/EC)**: ESP32-C3, CH32V003
  - **Xtensa LX6/LX7**: ESP32, ESP32-S3 (via QEMU)
  - **Arm Cortex-A53**: Raspberry Pi 3 Linux (via QEMU)
- **Deploy command**: `sudo docker run -d -p 3080:80 ghcr.io/davidmonterocrespo24/velxio:master`
- **เว็บ demo online มีให้ทดลอง** — self-host ต้อง Linux
- **Limitation**: Pi 3 serial console รองรับไม่ครบ, ESP-IDF compile บางส่วน

## ข้อโต้แย้งหรือความขัดแย้ง

- เทียบกับ **Wokwi** (ที่ wiki ยังไม่มี entity): Wokwi ผูกกับ cloud + freemium; Velxio open-source + self-host ได้ — แต่ Wokwi เสถียรกว่า, รองรับ peripherals มากกว่า
- เทียบกับ **[[entities/iot/arduino-ide]] + [[entities/iot/platformio]]**: ตัวจริงต้องมีบอร์ด, Velxio = simulate ก่อน → ดี flow learning/prototyping แต่ยัง Beta ไม่ควรใช้ verify production firmware

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/velxio]] — สร้างใหม่
