---
type: entity
category: platform
tags: [home-automation, open-source, mqtt, integration]
sources: [mqtt-introduction]
created: 2026-04-18
updated: 2026-04-18
---

# Home Assistant

**ประเภท**: Home Automation Platform (Open Source)  
**ผู้พัฒนา**: Nabu Casa / Community  
**License**: Apache 2.0  
**ภาษา**: Python

## ภาพรวม

Home Assistant เป็น open-source home automation platform ที่ได้รับความนิยมสูงสุดในโลก รองรับการ integrate กับอุปกรณ์กว่า 3,000 ประเภท ใช้ MQTT เป็นโปรโตคอลหลักสำหรับการสื่อสารกับอุปกรณ์ custom

## การใช้งาน MQTT

Home Assistant มี MQTT integration built-in รองรับ:
- Auto-discovery ผ่าน MQTT topics พิเศษ
- การ subscribe/publish ผ่าน UI หรือ automation
- รองรับ Mosquitto เป็น broker หลัก (มี add-on อย่างเป็นทางการ)

## ความสัมพันธ์

- ใช้งานโปรโตคอล: [[entities/iot/mqtt-protocol]]
- ใช้ร่วมกับ: [[entities/iot/mosquitto]]
- รันบน: Raspberry Pi (ยังไม่มีหน้า), Home Assistant OS

## หมายเหตุ

*(หน้านี้ยังมีข้อมูลน้อย จะอัปเดตเมื่อ ingest source ที่เกี่ยวกับ Home Assistant โดยตรง)*

## แหล่งข้อมูล

- [[sources/mqtt-introduction]] — กล่าวถึง Home Assistant เป็น use case หลักของ MQTT
