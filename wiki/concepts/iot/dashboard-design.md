---
type: concept
tags: [dashboard, ux, visualization, iot, design, grafana, node-red]
sources: [iot-visualization-guide, dashboard-design-best-practices]
created: 2026-04-18
updated: 2026-04-18
---

# Dashboard Design (IoT)

## นิยาม

Dashboard คือหน้าจอที่แสดงข้อมูลสำคัญ "at a glance" สำหรับ IoT — แปลง raw sensor data ให้เป็น visual insight ที่ operator ใช้ตัดสินใจได้ทันที

## ทำไมถึงสำคัญใน IoT

IoT สร้าง data stream ต่อเนื่อง ถ้าไม่มี dashboard ที่ดี ข้อมูลที่เก็บมาก็ไม่มีประโยชน์ Dashboard ที่ดีทำให้ detect anomaly ได้เร็ว, ช่วย troubleshoot, และแสดง trend ที่มองไม่เห็นจาก raw numbers

## Widget Selection Guide

| Widget | ใช้กับ | อย่าใช้กับ |
|--------|--------|-----------|
| **Gauge** | ค่าปัจจุบัน (temp, %, rpm) | trend ย้อนหลัง |
| **Line Chart** | time-series trend | ค่าเดียว snapshot |
| **Stat / Number** | ค่า key metric ปัจจุบัน | หลายค่าพร้อมกัน |
| **Alert Indicator** | threshold status | ข้อมูลต่อเนื่อง |
| **Bar Chart** | เปรียบเทียบ period | real-time stream |
| **Table** | log ล่าสุด, multi-sensor | ค่าเดียว |

## Design Principles

1. **แสดงเฉพาะ relevant data** — ถ้าข้อมูลไม่ช่วยตัดสินใจ → ไม่แสดง
2. **Information hierarchy** — สำคัญ = ใหญ่/บน, รายละเอียด = เล็ก/ล่าง
3. **Consistent color coding** — เขียว=ปกติ, เหลือง=เตือน, แดง=วิกฤต ทั้ง dashboard
4. **Timestamp visible** — ทุก panel ต้องเห็น "last updated"
5. **Mobile-readable** — ขนาดตัวอักษรและ widget ต้องอ่านได้บนมือถือ
6. **Progressive disclosure** — overview ก่อน drill-down ทีหลัง

## Dashboard สำหรับโปรเจ็คนี้ (Grafana)

```
┌──────────────┬──────────────┬──────────────┐
│  Temp Gauge  │   Hum Gauge  │ Alert Status │
│   28.5°C     │    65%       │   ✅ Normal  │
├──────────────┴──────────────┴──────────────┤
│         Temperature / Humidity (24h)        │
│  ~~~~~~~~~~~~~~~~~~~~/~~~~~~~~~~~~~~~~~~~~  │
├─────────────────────────────────────────────┤
│   Last reading: 2026-04-18 14:32:05 UTC     │
└─────────────────────────────────────────────┘
```

## Platform สำหรับ IoT Dashboard

| Platform | เหมาะกับ | ข้อดี |
|---------|---------|-------|
| [[entities/iot/grafana]] | time-series analytics | สวย, query ทรงพลัง |
| [[entities/iot/node-red]] Dashboard | control panel + monitor | low-code, bidirectional |
| Custom HTML/JS | lightweight, embedded | ยืดหยุ่นสุด |

## ความสัมพันธ์

- สร้างด้วย: [[entities/iot/grafana]], [[entities/iot/node-red]]
- Data source: [[entities/iot/influxdb]], [[entities/iot/mysql]]
- Concept: [[concepts/iot/data-logger]] — เก็บข้อมูลก่อน แสดงทีหลัง

## แหล่งข้อมูล

- [[sources/iot-visualization-guide]] — widget selection, IoT-specific patterns
- [[sources/dashboard-design-best-practices]] — general UX principles
