---
type: source
title: "DX-LR02-900T22D Serial Port Application Guide v2.0"
slug: dx-lr02-serial-guide-v2
date_ingested: 2026-04-19
original_file: raw/assets/DX-SMART_LORA MODULE/LR01&02-900Mhz Development & User Information/03-Technical Documentation/DX-LR02 Technical Documentation/DX-LR02-900T22DSerial port application guide NEW.pdf
tags: [dx-lr02, lora, at-commands, uart, official, v2]
---

# DX-LR02 Serial Port Application Guide v2.0 (Official)

**ประเภท**: official application guide (PDF)
**เวอร์ชัน**: V2.0 — วันที่ 2025-11-17 (ล่าสุด)
**ผู้เผยแพร่**: Shenzhen DX-SMART Technology Co., Ltd.

## Default Settings (สำคัญมาก)

| Parameter | Default |
|-----------|---------|
| Baud rate | **9600 bps** (code: 3) |
| Air rate level | **LEVEL2** = 2148 bps |
| Frequency | **915.15 MHz** (channel 41) |
| TX power | **22 dBm** |
| Mode | Transparent (MODE0) |
| Address | **ff,ff** (broadcast) |
| Subpacket length | **230 bytes** (code: 3) |
| Key | **12345** (encryption ON) |
| Work mode | High Efficiency (SLEEP2) |

## AT Command Reference (ครบชุด)

### Basic
| Command | Function | Default |
|---------|----------|---------|
| `+++` | เข้า/ออก AT mode | — |
| `AT` | Test | — |
| `AT+RESET` | Restart | — |
| `AT+DEFAULT` | Factory reset | — |
| `AT+HELP` | Query all config | — |

### Serial Port
| Command | Function | Values |
|---------|----------|--------|
| `AT+BAUD<n>` | Baud rate | 1=2400, 2=4800, **3=9600**, 4=19200, 5=38400, 6=57600, 7=115200 |
| `AT+PARI<n>` | Parity | 0=none, 1=odd, 2=even |

### LoRa Parameters
| Command | Function | Values / Default |
|---------|----------|---------|
| `AT+LEVEL<n>` | Air rate + range | 0-7 (ดูตาราง), **default 2** |
| `AT+MODE<n>` | Transmission mode | **0**=transparent, 1=fixed-point, 2=broadcast |
| `AT+SLEEP<n>` | Power mode | 0=sleep, 1=air-wake, **2**=high-efficiency |
| `AT+CHANNEL<nn>` | Channel (hex) | 00-63, **default 41** (=915.15 MHz) |
| `AT+MAC<h>,<h>` | Device address | **default ff,ff** |
| `AT+POWE<n>` | TX power (dBm) | 0-22, **default 22** |
| `AT+PACKET<n>` | Subpacket length | 0=32, 1=64, 2=128, **3=230 bytes** |
| `AT+DRSSI<n>` | RSSI in packet | 0=off, 1=on |
| `AT+OPENKEY<n>` | Encryption switch | 0=off, **1=on** |
| `AT+KEY<n>` | Encryption key | **default 12345** |
| `AT+SWITCH<n>` | M0/M1 pin control | 0=off, 1=on |
| `AT+LBT<n>` | Listen-Before-Talk | 0=off, 1=on |
| `AT+LRSSI<n>` | LBT threshold | default -87 dBm |
| `AT+ERSSI` | Current noise level | query only |

## LEVEL (Air Rate) Table

| LEVEL | SF | BW (kHz) | CR | Air Rate (bps) | Range LOS |
|-------|----|----------|----|---------------|-----------|
| 0 | 11 | 125 | 4/8 | **336** | **8.0 km** |
| 1 | 11 | 250 | 4/5 | 1075 | — |
| **2** | **11** | **500** | **4/5** | **2148** | — (default) |
| 3 | 8 | 250 | 4/5 | 6250 | — |
| 4 | 8 | 500 | 4/6 | 10417 | — |
| 5 | 7 | 500 | 4/6 | 18229 | **2.4 km** |
| 6 | 6 | 500 | 4/5 | 37500 | — |
| 7 | 5 | 500 | 4/5 | 62500 | — |

> **กฎ**: Rate สูง = ส่งข้อมูลเร็ว แต่ range สั้น / Rate ต่ำ = range ไกล แต่ส่งช้า

## Channel Frequency

เริ่มที่ 850.15 MHz, ห่างกัน 1 MHz:
- Channel 00 = 850.15 MHz
- **Channel 41 = 915.15 MHz (default)**
- Channel 63 = 913.15 MHz

## M0/M1 Pin Modes (เมื่อ AT+SWITCH=1)

| M0 | M1 | Mode |
|----|-----|------|
| 0 | 0 | High Efficiency (ปกติ) |
| 1 | 0 | Air Wake-Up |
| 0 | 1 | AT Command Mode |
| 1 | 1 | Sleep |

## RSSI Calculation

```
รับ packet มีค่า RSSI byte ต่อท้าย (เมื่อเปิด AT+DRSSI1)
Actual RSSI (dBm) = -(0xFF - received_byte)
ตัวอย่าง: received AB → RSSI = -(255-171) = -84 dBm
```

## Error Codes

| Code | Description |
|------|-------------|
| 104 | Invalid instruction |
| 105 | Invalid parameters |
| 106 | Other errors |

## ข้อควรระวัง

- LoRa เป็น **half-duplex** — ส่งได้ครั้งละ 1 node เท่านั้น
- Transparent mode: ต้องตั้ง LEVEL และ CHANNEL เหมือนกันทั้งสอง module
- Key ทั้ง sender และ receiver ต้องตรงกัน
- ทุก command ต้อง restart ถึงจะมีผล ยกเว้น SLEEP mode

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/dx-lr02-lora]] — เพิ่ม AT command reference ครบชุด, default settings, LEVEL table
