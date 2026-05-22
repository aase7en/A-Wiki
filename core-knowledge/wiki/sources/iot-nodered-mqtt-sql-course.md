---
type: source
title: "IoT Node-RED + MQTT + SQL – ทำ Data Logger & Dashboard แบบอุตสาหกรรม"
slug: iot-nodered-mqtt-sql-course
date_ingested: 2026-04-18
original_file: raw/"IoT Node-RED + MQTT + SQL – ทำ Data Logger & Dashboard แบบอุตสาหกรรม".md
tags: [node-red, mqtt, mysql, grafana, modbus, industrial-iot, dashboard, data-logger]
---

# IoT Node-RED + MQTT + SQL – ทำ Data Logger & Dashboard แบบอุตสาหกรรม

**ประเภท**: course (รายละเอียดหลักสูตร)
**วันที่**: unknown
**ผู้เผยแพร่**: plcsnook.com

## ประเด็นหลัก

1. **Node-RED เป็น middleware หลัก** — รับข้อมูลจาก MQTT → ประมวลผล → บันทึก MySQL → แสดงผล Grafana ได้ในระบบเดียว
2. **Stack อุตสาหกรรม**: MQTT (Mosquitto) + Node-RED + MySQL + Grafana ใช้งานได้จริงใน industrial setting
3. **รองรับ PLC** — เชื่อม PLC Siemens S7-1200 และ Mitsubishi QCPU/FX5U ผ่าน Node-RED โดยตรง
4. **Modbus RTU/TCP** — Node-RED มี Modbus node รองรับอุปกรณ์ RS485 (Temp Controller, Power Meter, VFD)
5. **MySQL เป็น data store** — ต่างจาก InfluxDB ตรงที่ใช้ SQL relational DB เหมาะสำหรับ Data Logger ที่ต้องการ query ยืดหยุ่น

## Stack ที่สอนในหลักสูตร

```
Sensor / PLC
     ↓
   MQTT (Mosquitto)
     ↓
  Node-RED          ← รับข้อมูล, ประมวลผล Flow
     ↓
  MySQL             ← Data Logger (บันทึก historical)
     ↓
  Grafana           ← Dashboard (connect MySQL datasource)
```

## 7 Parts ของหลักสูตร

| Part | หัวข้อ | เกี่ยวข้องกับโปรเจ็ค |
|------|--------|---------------------|
| 1 | Node-RED Basic + Dashboard UI | ✅ สูง |
| 2 | MQTT System (Mosquitto) | ✅ สูง |
| 3 | MySQL + Data Logger | ✅ สูง |
| 4 | PLC Siemens S7-1200 | ⬜ ไม่เกี่ยว |
| 5 | Modbus TCP/RTU | ⬜ อนาคต |
| 6 | Grafana Advanced | ✅ สูง |
| 7 | Mobile Access (Remote-RED) | ⬜ optional |

## ข้อมูลที่น่าสนใจ

- Node-RED สามารถเชื่อม MySQL โดยตรงโดยไม่ต้องใช้ Telegraf
- Grafana รองรับ MySQL เป็น data source ได้ (ไม่ต้องใช้ InfluxDB เสมอไป)
- Remote-RED App ให้ access Dashboard จากมือถือนอก network

## ข้อโต้แย้งหรือความขัดแย้ง

**Architecture ทางเลือก**: Source นี้เสนอ stack **MQTT → Node-RED → MySQL → Grafana** ซึ่งแตกต่างจาก architecture ปัจจุบันในโปรเจ็คที่ใช้ **Telegraf → InfluxDB → Grafana**
- MySQL: SQL query ยืดหยุ่น, เข้าใจง่าย แต่ไม่ใช่ time-series DB โดยตรง
- InfluxDB: optimized สำหรับ time-series, query ทรงพลังกว่าสำหรับ sensor data

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/node-red]] — สร้างใหม่
- [[entities/iot/mysql]] — สร้างใหม่
- [[concepts/iot/data-logger]] — สร้างใหม่
- [[concepts/iot/modbus]] — สร้างใหม่
- [[entities/iot/grafana]] — เพิ่ม MySQL datasource alternative
