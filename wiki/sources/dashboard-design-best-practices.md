---
type: source
title: "Dashboard Design: Best Practices and Examples"
slug: dashboard-design-best-practices
date_ingested: 2026-04-18
original_file: raw/Dashboard Design best practices and examples.md
tags: [dashboard, ux, design, cards, layout, information-hierarchy]
---

# Dashboard Design: Best Practices and Examples

**ประเภท**: article
**วันที่**: 2024-06-14
**ผู้เขียน**: Sarah Shaar (justinmind.com)

## ประเด็นหลัก

1. **Dashboard = critical info at a glance** — เหมือน dashboard รถยนต์ แสดงเฉพาะข้อมูล relevant to task
2. **Cards คือหน่วยพื้นฐาน** — ทุก dashboard ประกอบด้วย cards (profile, notifications, data, graphs, controls)
3. **Show only relevant info** — ต้องถามว่า "ข้อมูลนี้ช่วย user ตัดสินใจได้ไหม?" ถ้าไม่ → ไม่แสดง
4. **Save user time** — ถ้า dashboard ไม่ทำให้งานเร็วขึ้น มันล้มเหลว
5. **Dashboard as homepage** — power user มักใช้ dashboard เป็นจุดเริ่มต้นเสมอ

## Principles สำคัญ

- **Information hierarchy**: สำคัญสุด = ใหญ่สุด/ตำแหน่งบน
- **Consistency**: layout, สี, font เดียวกัน ทั้ง dashboard
- **Actionable data**: data ทุก piece ต้องนำไปสู่ action บางอย่างได้
- **Progressive disclosure**: overview ก่อน → drill-down ถ้าต้องการรายละเอียด

## Apply กับโปรเจ็คปัจจุบัน (Grafana)

Panel ที่ควรมีใน Grafana dashboard:
1. **Current temp** (Gauge) — อุณหภูมิตอนนี้ ตำแหน่งบนซ้าย ใหญ่สุด
2. **Current humidity** (Gauge) — ความชื้นตอนนี้ ข้างๆ temp
3. **24h temperature trend** (Line Chart) — เต็ม width ด้านล่าง
4. **Alert status** (Stat) — สีเขียว/แดง ตาม threshold
5. **Last updated** (Text) — timestamp ล่าสุดที่รับ data

## หน้า Wiki ที่ได้รับการอัปเดต

- [[concepts/iot/dashboard-design]] — สร้างใหม่
