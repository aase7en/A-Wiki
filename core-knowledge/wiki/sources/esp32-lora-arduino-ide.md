---
type: source
title: "ESP32 with LoRa using Arduino IDE"
slug: esp32-lora-arduino-ide
date_ingested: 2026-04-18
original_file: raw/ESP32 with LoRa using Arduino IDE.md
tags: [esp32, lora, arduino, rfm95, sx1276, p2p, code]
---

# ESP32 with LoRa using Arduino IDE

**ประเภท**: tutorial
**วันที่**: 2018-06-23
**ผู้เขียน**: Sara Santos (randomnerdtutorials.com)

## ประเด็นหลัก

1. **Library มาตรฐาน**: `sandeepmistry/arduino-LoRa` — ใช้กับ RFM95/SX1276/SX1278 ผ่าน SPI
2. **P2P vs LoRaWAN**: LoRa รองรับทั้ง Point-to-Point และ LoRaWAN — บทความนี้สอน P2P
3. **Frequencies**: 868MHz (EU), 915MHz (US), 433MHz (Asia) — ไทยใช้ 433 หรือ 920-925MHz
4. **ไม่เหมาะกับ**: high data rate, frequent transmission, crowded networks
5. **Code pattern**: LoRa.begin() → LoRa.beginPacket() → LoRa.print() → LoRa.endPacket() (sender); LoRa.parsePacket() → LoRa.readString() (receiver)

## Code ตัวอย่าง (P2P)

**Sender:**
```cpp
#include <SPI.h>
#include <LoRa.h>

void setup() {
  LoRa.begin(915E6);  // 915MHz
}

void loop() {
  LoRa.beginPacket();
  LoRa.print("Hello LoRa");
  LoRa.endPacket();
  delay(1000);
}
```

**Receiver:**
```cpp
void loop() {
  int packetSize = LoRa.parsePacket();
  if (packetSize) {
    String msg = "";
    while (LoRa.available()) msg += (char)LoRa.read();
    Serial.println(msg);
  }
}
```

## ข้อมูลที่น่าสนใจ

- RFM95W = SX1276 chip ที่บรรจุในโมดูล HopeRF
- สามารถส่ง RSSI (signal strength) กลับมาด้วย: `LoRa.packetRssi()`
- LoRa module ต่อผ่าน **SPI** (ต่างจาก DX-LR02 ที่ใช้ **UART**)

## ข้อโต้แย้งหรือความขัดแย้ง

**DX-LR02 ใช้ UART ไม่ใช่ SPI** — library `arduino-LoRa` ใช้กับ chip SX1276 โดยตรง (SPI) เช่น RFM95, TTGO LoRa32 ไม่ตรงกับ DX-LR02 ที่เป็น UART serial module ต้องใช้ AT commands แทน

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/rfm95-sx1276]] — สร้างใหม่
- [[concepts/iot/lora-p2p]] — สร้างใหม่
- [[concepts/iot/lora]] — เพิ่ม library และ interface comparison
