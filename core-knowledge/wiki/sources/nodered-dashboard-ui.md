---
type: source
title: "ตอน 3: สร้าง Dashboard Node-RED มอนิเตอร์และควบคุมทุกอย่าง"
slug: nodered-dashboard-ui
date_ingested: 2026-04-18
original_file: raw/ตอน 3  สร้าง Dashboard Node-RED มอนิเตอร์และควบคุมทุกอย่าง 📊.md
tags: [node-red, dashboard, ui, hmi, low-code, visualization]
---

# ตอน 3: สร้าง Dashboard Node-RED มอนิเตอร์และควบคุมทุกอย่าง

**ประเภท**: article (บทความ series ตอนที่ 3/6)
**วันที่**: 2025-09-27
**ผู้เขียน**: Y.Chanadej (techsourcegroups.com)

## ประเด็นหลัก

1. **node-red-dashboard package** — ติดตั้งผ่าน Manage Palette, ให้ UI nodes ทันที ไม่ต้องเขียน HTML/CSS/JS
2. **UI Nodes แบ่ง 2 กลุ่ม**: Display (Gauge, Chart, Text, Table) และ Input (Button, Switch, Slider)
3. **Bidirectional** — Dashboard ไม่ใช่แค่แสดงผล แต่ควบคุมอุปกรณ์ได้ด้วย (ส่ง MQTT command กลับ)
4. **จัดโครงสร้างด้วย Tab > Group** — ทำให้ Dashboard เป็นระเบียบ สามารถ multi-room หรือ multi-machine ได้
5. **Real-time by default** — ข้อมูลอัปเดต event-driven ไม่ต้อง polling

## UI Nodes สำคัญ

| Node | ประเภท | ใช้กับ |
|------|--------|--------|
| UI Gauge | Display | อุณหภูมิ, ความชื้น, pressure |
| UI Chart | Display | กราฟ trend ย้อนหลัง |
| UI Text | Display | ค่าตัวเลข/ข้อความ real-time |
| UI Table | Display | log ล่าสุด, multi-sensor |
| UI Button | Input | trigger action, test |
| UI Switch | Input | เปิด/ปิดอุปกรณ์ |
| UI Slider | Input | ปรับ setpoint (เช่น threshold อุณหภูมิ) |

## ข้อมูลที่น่าสนใจ

- Node-RED Dashboard เปรียบได้กับ HMI/SCADA ขนาดเล็ก — concept เดียวกับระบบอุตสาหกรรม
- เข้าถึงจากมือถือได้ทันทีผ่าน browser ใน network เดียวกัน
- ต้องการ access จากภายนอก → ต้องตั้ง Port Forwarding หรือ VPN

## ข้อโต้แย้งหรือความขัดแย้ง

ไม่มีข้อขัดแย้งกับ wiki ปัจจุบัน — Node-RED Dashboard เป็นทางเลือกที่ complement กับ Grafana ได้:
- Node-RED Dashboard: เหมาะกับ control panel + monitoring แบบ lightweight
- Grafana: เหมาะกับ data analysis + historical charts ที่ซับซ้อน

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/node-red]] — เพิ่ม Dashboard section
