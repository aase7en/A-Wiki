---
type: entity
category: protocol
tags: [nb-iot, lpwan, cellular, 3gpp, narrowband, licensed]
sources: [lora-vs-nbiot]
created: 2026-04-18
updated: 2026-04-18
---

# NB-IoT (Narrowband IoT)

**ผู้พัฒนา**: 3GPP (cellular standard)
**ความถี่**: Licensed cellular band (ต้องผ่าน operator)
**ประเภท**: LPWAN cellular technology

## ภาพรวม

NB-IoT (Narrowband Internet of Things) เป็น LPWAN technology บนโครงสร้างพื้นฐาน cellular — ใช้ tower ของ AIS/DTAC/True โดยตรง ไม่ต้องติดตั้ง gateway เอง แต่มีค่าบริการรายเดือน

## เปรียบเทียบกับ LoRa

| หัวข้อ | LoRa (โปรเจ็คนี้) | NB-IoT |
|--------|------|--------|
| Frequency | unlicensed (433/900 MHz) | licensed cellular |
| Infrastructure | gateway ของตัวเอง | tower operator |
| ค่าใช้จ่าย | hardware only | monthly fee (operator) |
| Coverage | เฉพาะ gateway range | ทั่วประเทศ |
| Power | ต่ำมาก (µA) | ต่ำ (mA) |
| Data rate | 300 bps–50 kbps | 20–250 kbps |
| QoS | ไม่มี guarantee | มี |
| Latency | วินาที | วินาที |
| เหมาะกับ | private network, lab | nationwide IoT, utility meter |

## Use Cases ใน IoT ไทย

- **เครื่องวัดน้ำอัจฉริยะ** (smart water meter): ติดตั้งทั่วเมือง → ใช้ NB-IoT รายงาน consumption
- **smart parking**: sensor ใต้ถนน → NB-IoT → central management
- **precision farming**: sensor กระจายทั่วไร่ → ต้องการ coverage กว้าง

## ทำไมโปรเจ็คนี้เลือก LoRa ไม่ใช่ NB-IoT

- ต้นทุนต่ำกว่า (ไม่มีค่า operator)
- ไม่ต้องการ nationwide coverage
- Hardware มีอยู่แล้ว (DX-LR02)
- เหมาะ lab และ prototype

## ความสัมพันธ์

- แข่งขันกับ: [[concepts/iot/lora]]
- อยู่ใน category เดียวกัน: LPWAN (Low Power Wide Area Network)
- เปรียบเทียบ: [[concepts/iot/lorawan]] — LoRaWAN คล้าย NB-IoT แต่ใช้ unlicensed spectrum

## แหล่งข้อมูล

- [[sources/lora-vs-nbiot]] — บทความเปรียบเทียบ (smart meter context)
