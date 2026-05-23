---
type: source
title: "เครื่องวัดน้ำ LoRa-NB-IoT: การวิเคราะห์เปรียบเทียบ LoRa และ NB-IoT"
slug: lora-vs-nbiot
date_ingested: 2026-04-18
original_file: raw/เครื่องวัดน้ำ LoRa-nb iot เครื่องวัดน้ำ-เครื่องวัดน้ำอัจฉริยะ.md
tags: [lora, nb-iot, lpwan, comparison, smart-meter]
---

# เครื่องวัดน้ำ LoRa-NB-IoT: เปรียบเทียบ LoRa และ NB-IoT

**ประเภท**: article (ภาษาไทย)
**วันที่**: 2022-04-06
**ผู้เขียน**: เหอเป่ย ซ่างหง เมตร เทคโนโลยี บจก.

## ประเด็นหลัก

1. **LPWAN 2 ค่าย**: LoRa (unlicensed, private network) vs NB-IoT (licensed cellular, operator network)
2. **LoRa ข้อดี**: ไม่มีค่าบริการรายเดือน, ตั้ง private network เองได้, ราคา node ถูก
3. **NB-IoT ข้อดี**: coverage ทั่วประเทศ (ใช้ cell tower), ไม่ต้องติดตั้ง gateway, QoS ดีกว่า
4. **LoRa ใช้ frequency ไม่มีใบอนุญาต** < 1GHz — ไม่มีค่าใช้จ่าย spectrum
5. **NB-IoT ใช้ licensed band** — ต้องจ่าย operator (AIS/DTAC/True ไทย)

## ตารางเปรียบเทียบ

| หัวข้อ | LoRa | NB-IoT |
|--------|------|--------|
| Frequency | unlicensed (433/868/915 MHz) | licensed cellular |
| Infrastructure | ต้องติดตั้ง gateway เอง | ใช้ tower cellular |
| ค่าใช้จ่าย | ถูก (hardware only) | มีค่าบริการ monthly |
| Coverage | เฉพาะ gateway range | nationwide |
| Power | ต่ำมาก | ต่ำ |
| QoS | ไม่มี guarantee | มี |
| เหมาะกับ | private IoT, lab, farm, factory | nationwide deployment |

## ข้อโต้แย้งหรือความขัดแย้ง

ไม่มี — ยืนยัน lora.md ที่มี NB-IoT ในตาราง

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/nb-iot]] — สร้างใหม่
- [[concepts/iot/lora]] — เพิ่ม LPWAN comparison context
