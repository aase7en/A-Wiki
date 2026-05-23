---
type: entity
category: device
tags: [lora, 900mhz, uart, wireless, long-range, dx-smart, asr6601]
sources: [hardware-inventory-2026-04-18, dx-lr02-datasheet, dx-lr02-official-arduino-library, dx-lr02-module-spec-official, dx-lr02-serial-guide-v2]
created: 2026-04-18
updated: 2026-04-19
---

# DX-LR02-900T22D LoRa Module

**ผู้ผลิต**: DX-SMART (Shenzhen Daxia Longque Technology Co., Ltd.)
**รุ่น**: DX-LR02-900T22D (900MHz, 22dBm)
**Chip ภายใน**: **ASR6601** SOC (Arm China STAR-MC1) — ยืนยันจาก official spec
**สถานะใน Lab**: ✅ มีอยู่ × **2** พร้อมเสาอากาศ SMA

> ⚠️ **แก้ไขข้อมูลเดิม**: source บทความ third-party ระบุ LLCC68 แต่ official PDF ยืนยันชัดว่าเป็น **ASR6601** — ดู [[sources/dx-lr02-module-spec-official]]

> ⚠️ **Safety**: ต้องต่อเสาอากาศก่อนจ่ายไฟเสมอ — ถ้าไม่มีเสา RF power ไม่ระบาย → วงจรภายในพัง

## ภาพรวม

DX-LR02 เป็น UART LoRa transceiver module ใช้ ASR6601 SOC (Sub-1GHz LoRa + Arm China STAR-MC1 processor) สื่อสารกับ MCU ผ่าน LPUART/UART TTL มาพร้อม antenna SMA connector ทำงานที่ 900MHz band ระยะไกลสูงสุด 8km (LOS)

## Specs หลัก (Official)

| Parameter | Value |
|-----------|-------|
| Chip | **ASR6601** (Arm China STAR-MC1, 48MHz) |
| Module size | 19.0 × 16.5 × 2.4 mm |
| Frequency | **850–930 MHz** (รุ่นในแล็บ) |
| TX power | 0–**+22 dBm** |
| Sensitivity | **-138 dBm** |
| Operating voltage | **3.3V–5.5V** |
| Range (LOS) | **~8 km** |
| Range (Urban) | **~3.8 km** |
| Op. temperature | -40 to +85 °C |
| Interfaces | LPUART, UART, I2C, SSP, ADC |

## Power Consumption

| Mode | State | Current |
|------|-------|---------|
| Sleep | Standby | **59.15 µA** |
| Air Wake-Up | Standby | 4.63 mA |
| Air Wake-Up | Receive | 6.7 mA |
| High Efficiency | Standby | 9.71 mA |
| High Efficiency | **Transmit** | **53.5 mA** |
| High Efficiency | Receive | 9.53 mA |

## ⚠️ ซื้อให้ถูกรุ่น

DX-LR02 มี **2 frequency versions** — ต้องซื้อคู่ที่ตรงกัน:
- **850-930 MHz** (รุ่นที่มีในแล็บ ✅)
- **430-475 MHz**

## Pin Definition

| Pin | Name | Function |
|-----|------|---------|
| 1 | M0 | Mode select / Customizable IO |
| 2 | M1 | Mode select / Customizable IO |
| 3 | UART_RX | Serial data input |
| 4 | UART_TX | Serial data output |
| 5 | AUX | RF status indicator |
| 6 | VCC | Power (3.3–5.5V) |
| 7 | GND | Ground |

## AUX Pin

- **HIGH** = กำลัง TX/RX หรือ switching mode → รอ
- **LOW** = พร้อมรับส่ง (idle/done)
- AUX จะ HIGH **ล่วงหน้า 2-3ms** ก่อนส่งข้อมูลให้ MCU — ใช้ interrupt ได้

```cpp
// ตัวอย่าง: รอ AUX = LOW ก่อนส่ง
while (digitalRead(AUX_PIN) == HIGH) delay(1);
Serial2.write(data, len);
```

## Default Settings

| Parameter | Default |
|-----------|---------|
| Baud rate | **9600 bps** |
| Air rate | **LEVEL2** = 2148 bps |
| Frequency | **Channel 41** = 915.15 MHz |
| TX power | 22 dBm |
| Mode | Transparent (MODE0) |
| Address | ff,ff |
| Encryption key | **12345** (ON by default) |

## AT Commands (สำคัญ)

```
+++              เข้า AT mode (ออกด้วย +++ อีกครั้ง)
AT               Test
AT+RESET         Restart (จำเป็นหลังเปลี่ยน config)
AT+DEFAULT       Factory reset
AT+HELP          Query all settings

AT+BAUD3         Set 9600 bps (default)
AT+LEVEL2        Set air rate LEVEL2 (default, 2148 bps)
AT+MODE0         Transparent mode
AT+CHANNEL41     Channel 41 = 915.15 MHz (default)
AT+SLEEP2        High Efficiency mode (default)
AT+POWE22        Max TX power 22 dBm
```

## LEVEL (Air Rate) เลือกตามระยะ

| LEVEL | Air Rate | Range LOS |
|-------|----------|-----------|
| 0 | 336 bps | **8.0 km** (max range) |
| **2** | **2148 bps** | — (default) |
| 5 | 18229 bps | 2.4 km |
| 7 | 62500 bps | — (max speed) |

## การต่อสาย (ESP32)

```
ESP32          DX-LR02
──────────────────────────
GPIO (any) --> M0
GPIO (any) --> M1
TX2 (GPIO17) --> RXD
RX2 (GPIO16) --> TXD
GPIO (any) <-- AUX
3.3V/5V     --> VCC
GND         --> GND
```

## Official Arduino Library

```cpp
LoRaModule lora(rxPin, txPin); // baud=9600 default
lora.setExpect(pong, sizeof(pong));
lora.onTxDone(cb);
lora.onRxDone(cb);
lora.onRxTimeout(cb);
lora.send(buf, len);
lora.poll(); // ต้องเรียกใน loop()
```

> บน ESP32 ให้แทน `SoftwareSerial` ด้วย `HardwareSerial Serial2`

## ความสัมพันธ์

- ใช้งาน concept: [[concepts/iot/lora]], [[concepts/iot/lora-p2p]]
- ต่อกับ: [[entities/iot/esp32]], [[entities/iot/esp32-s3]]
- เปรียบเทียบ chip: [[entities/iot/rfm95-sx1276]] (SX1276 = Semtech, ใช้ SPI)

## แหล่งข้อมูล

- [[sources/dx-lr02-module-spec-official]] — Official spec v1.1 (2024-06-19), ยืนยัน ASR6601, range, power
- [[sources/dx-lr02-serial-guide-v2]] — Official AT guide v2.0 (2025-11-17), command ครบชุด, LEVEL table
- [[sources/dx-lr02-official-arduino-library]] — Official Arduino library + PingPong example
- [[sources/dx-lr02-datasheet]] — ⚠️ third-party article, ระบุ LLCC68 ซึ่งไม่ถูกต้อง
- [[sources/hardware-inventory-2026-04-18]] — รูป 2 ตัวต่อกับ ESP32 กำลัง test
