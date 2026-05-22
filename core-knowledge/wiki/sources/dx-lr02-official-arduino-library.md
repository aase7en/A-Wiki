---
type: source
title: "DX-LR02 Official Arduino Library & PingPong Example"
slug: dx-lr02-official-arduino-library
date_ingested: 2026-04-19
original_file: raw/assets/DX-SMART_LORA MODULE/LR01&02-900Mhz Development & User Information/06-LORA & Arduino source/PingPong_LoRa_EN/
tags: [dx-lr02, lora, arduino, library, uart, softwareserial, state-machine]
---

# DX-LR02 Official Arduino Library & PingPong Example

**ประเภท**: official source code (DX-SMART package)  
**วันที่**: unknown  
**ผู้เผยแพร่**: DX-SMART

> ⚠️ PDF ใน package (MODULE SPECIFICATION + Serial port guide) อ่านไม่ได้ — ต้องติดตั้ง `poppler` (`brew install poppler`) ก่อน

## ประเด็นหลัก

1. **Official library ใช้ `SoftwareSerial`** — class `LoRaModule` ห่อหุ้ม UART ด้วย `SoftwareSerial`
2. **Default baud rate: 9600** — ยืนยันตรงกับ source อื่น
3. **Pattern: callback + state machine** — ไม่ใช่ blocking `delay()` แต่ใช้ `poll()` ใน `loop()`
4. **State machine**: `ST_IDLE` → `ST_RX` → `ST_RX_TIMEOUT` → `ST_IDLE`
5. **Ring buffer 64 bytes** สำหรับรับข้อมูล, expected frame buffer 32 bytes
6. **PingPong example**: Master ส่ง "Ping" → Slave ตอบ "Pong" → timeout แล้ว retry อัตโนมัติ

## API หลักของ LoRaModule

```cpp
LoRaModule lora(rxPin, txPin, baud = 9600);  // Constructor

lora.send(buf, len);           // ส่งข้อมูล raw bytes
lora.startReceive(timeout_ms); // เริ่มฟัง (timeout=0 = ฟังตลอด)
lora.setExpect(data, len);     // กำหนด frame ที่รอรับ (len=0 = รับทุก frame)
lora.poll();                   // ต้องเรียกใน loop() ทุก tick

lora.onTxDone(callback);       // เมื่อส่งเสร็จ
lora.onRxDone(callback);       // เมื่อรับ frame ที่ตรงกับ setExpect()
lora.onRxTimeout(callback);    // เมื่อ timeout
```

## PingPong Pattern

**Master:**
```
setup → send("Ping") → onTxDone → startReceive(1000ms)
       → onRxDone("Pong") → send("Ping") อีกรอบ
       → onTimeout → send("Ping") retry
```

**Slave:**
```
setup → startReceive(1000ms) → onRxDone("Ping") → send("Pong")
       → onTxDone → startReceive(1000ms)
       → onTimeout → startReceive(1000ms) retry
```

## ข้อสังเกต

- Library ใช้ `SoftwareSerial` ซึ่งเหมาะกับ Arduino (AVR) — บน ESP32 ควรใช้ HardwareSerial (`Serial2`) แทนเพื่อประสิทธิภาพที่ดีกว่า
- Pattern นี้ port มาใช้กับ ESP32 ได้โดยแทน `SoftwareSerial` ด้วย `HardwareSerial`
- PDF spec และ Serial port guide ยังไม่ได้อ่าน — มีข้อมูล electrical spec, pin config, AT command ฉบับ official อยู่ใน `03-Technical Documentation/DX-LR02 Technical Documentation/`

## ข้อโต้แย้งหรือความขัดแย้ง

ไม่มี — ยืนยันตรงกับ [[sources/dx-lr02-at-commands-demo]] ในเรื่อง baud rate 9600

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/dx-lr02-lora]] — เพิ่ม official library API, PingPong pattern, note เรื่อง SoftwareSerial vs HardwareSerial
