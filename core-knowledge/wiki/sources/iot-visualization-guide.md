---
type: source
title: "IoT Visualization Guide: Designing Effective Dashboards & Monitoring UIs"
slug: iot-visualization-guide
date_ingested: 2026-04-18
original_file: raw/IoT Visualization Guide Designing Effective Dashboards & Monitoring UIs.md
tags: [dashboard, visualization, iot, ux, real-time, gauge, chart, alert]
---

# IoT Visualization Guide: Dashboards & Monitoring UIs

**ประเภท**: video (YouTube — CodeLucky)
**วันที่**: 2025-12-31
**ผู้เขียน**: CodeLucky

## ประเด็นหลัก

1. **Sensor to Screen pipeline**: Raw sensor data → Transmit → Cloud/broker → Dashboard UI
2. **Widget selection**: Gauge เหมาะค่า current (ปัจจุบัน), Graph เหมาะ trend ย้อนหลัง
3. **Real-time data handling**: ต้องรองรับ high-frequency update โดยไม่ freeze UI
4. **Alert system**: threshold-based alert ต้องชัดเจน สีแดง/เขียว/เหลือง
5. **Layout hierarchy**: ข้อมูลสำคัญ = ใหญ่/บนซ้าย; รายละเอียด = เล็กกว่า/ด้านล่าง

## Dashboard Components ที่ดี

| Widget | ใช้กับ | อย่าใช้กับ |
|--------|--------|-----------|
| Gauge / Donut | ค่าปัจจุบัน, threshold | trend ย้อนหลัง |
| Line Chart | trend, เปรียบเทียบเวลา | ค่าเดียว |
| Bar Chart | เปรียบเทียบ category | time series ต่อเนื่อง |
| Number / Text | ค่าล่าสุด, count | ซับซ้อน |
| Alert indicator | status, threshold breach | ข้อมูลปกติ |

## Best Practices

- **Avoid clutter**: แสดงเฉพาะข้อมูลที่ operator ต้องการตัดสินใจ
- **Consistent color**: สี = ความหมาย (เขียว=ปกติ, เหลือง=เตือน, แดง=วิกฤต) ทั้ง dashboard
- **Timestamp visible**: ทุก panel ต้องเห็น "last updated" เสมอ
- **Mobile-ready**: dashboard ต้องอ่านได้บนมือถือ

## Apply กับโปรเจ็คปัจจุบัน

| Data | Widget แนะนำ | Platform |
|------|------------|---------|
| อุณหภูมิปัจจุบัน | Gauge (0-50°C) | Grafana |
| ความชื้นปัจจุบัน | Gauge (0-100%) | Grafana |
| อุณหภูมิ 24h | Line Chart | Grafana |
| Alert status | Alert indicator | Telegram Bot |

## หน้า Wiki ที่ได้รับการอัปเดต

- [[concepts/iot/dashboard-design]] — สร้างใหม่
