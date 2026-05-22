---
type: source
title: "DX-LR02-900T22D MODULE SPECIFICATION v1.1"
slug: dx-lr02-module-spec-official
date_ingested: 2026-04-19
original_file: raw/assets/DX-SMART_LORA MODULE/LR01&02-900Mhz Development & User Information/03-Technical Documentation/DX-LR02 Technical Documentation/DX-LR02-900T22D MODULE SPECIFICATION.pdf
tags: [dx-lr02, lora, datasheet, asr6601, hardware-spec, official]
---

# DX-LR02-900T22D MODULE SPECIFICATION (Official)

**ประเภท**: official datasheet (PDF)
**เวอร์ชัน**: V1.1 — วันที่ 2024-06-19
**ผู้เผยแพร่**: Shenzhen Daxia Longque Technology Co., Ltd. (DX-SMART)

## ประเด็นหลัก

1. **Chip: ASR6601** — SOC จีน (ไม่ใช่ LLCC68!) บรรจุ Arm China STAR-MC1 + RF transceiver + Flash + SRAM
2. **Sensitivity: -138 dBm** — ดีกว่าที่เคยบันทึก
3. **Range: 8 km LOS, 3.8 km urban** — ไกลกว่าที่เคยบันทึก (1-3 km)
4. **Power: 3.3V–5.5V** — รองรับได้ถึง 5.5V
5. **3 Transmission modes**: Transparent, Fixed-point, Broadcast

## Specs หลัก (official)

| Parameter | Value |
|-----------|-------|
| Chip | **ASR6601** (Arm China STAR-MC1, 48MHz) |
| Module size | 19.0 × 16.5 × 2.4 mm |
| Operating voltage | 3.3V – 5.5V (typical 5V) |
| Sensitivity | **-138 dBm** |
| TX power | 0 – +22 dBm |
| Frequency | 850 – 930 MHz |
| RF impedance | 50Ω |
| Interface | LPUART (primary), UART, I2C, SSP, ADC |
| Range (LOS) | **~8 km** |
| Range (Urban) | **~3.8 km** |
| Op. temperature | -40 to +85 °C |
| Storage temperature | -40 to +125 °C |

## Power Consumption

| Mode | State | Current |
|------|-------|---------|
| Sleep | Standby | **59.15 µA** |
| Air Wake-Up | Standby | 4.63 mA |
| Air Wake-Up | Receive | 6.7 mA |
| High Efficiency | Standby | 9.71 mA |
| High Efficiency | Transmit | **53.5 mA** |
| High Efficiency | Receive | 9.53 mA |

## AUX Pin Behavior (official)

- **HIGH** = กำลัง transmit / receive / switching mode → ยังไม่พร้อม
- **LOW** = พร้อมรับส่งข้อมูล (idle/done)
- พิเศษ: เมื่อตรวจจับข้อมูลขาเข้า AUX จะ HIGH ล่วงหน้า **2-3ms** ก่อนส่งให้ MCU

## 3 Transmission Modes

- **MODE0 - Transparent**: ส่งตรง ต้องใช้ channel เดียวกัน
- **MODE1 - Fixed-point**: `[addr_hi][addr_lo][channel][data]` — ระบุปลายทางได้
- **MODE2 - Broadcast**: `[channel][data]` — broadcast ในช่องเดียวกัน

## ข้อโต้แย้งหรือความขัดแย้ง

> ⚠️ **CRITICAL**: source เดิม [[sources/dx-lr02-datasheet]] ระบุ chip = **LLCC68** (Semtech) แต่ official PDF ระบุชัดว่า **ASR6601** (Arm China) — ASR6601 เป็น SOC จีน ไม่ใช่ chip ตระกูล Semtech เลย
>
> **สรุป**: ASR6601 คือข้อมูลที่ถูกต้อง (official spec) — ข้อมูล LLCC68 ใน source เดิมน่าจะเป็นการเข้าใจผิดจากบทความ third-party

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/dx-lr02-lora]] — แก้ chip ASR6601, อัปเดต specs ทั้งหมด
