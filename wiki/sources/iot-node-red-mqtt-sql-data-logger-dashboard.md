---
tags: [iot, node, red, mqtt, sql]
type: source
title: "“IoT Node-RED + MQTT + SQL – ทำ Data Logger & Dashboard แบบอุตสาหกรรม”"
slug: iot-node-red-mqtt-sql-data-logger-dashboard
date_ingested: 2026-05-24
original_file: raw/“IoT Node-RED + MQTT + SQL – ทำ Data Logger & Dashboard แบบอุตสาหกรรม”.md
---

```yaml
---
title: "“IoT Node-RED + MQTT + SQL – ทำ Data Logger & Dashboard แบบอุตสาหกรรม”"
source: "https://plcsnook.com/plc-scada-courses/iot-node-red-mqtt-sql/"
author: ""
published: ""
created: "2026-04-18"
description: "คอร์ส IoT Node-RED + MQTT + SQL ครบวงจรสำหรับงานอุตสาหกรรม    เนื้อหามากกว่า 120 วิดีโอ รวมเวลาสอนกว่า 18 ชั่วโมง+    สอนเชื่อมต่อ PLC Siemens, PLC Mitsubishi, RS485/Modbus, Temp Control, VFD    ฝึกทำ Data Logger ด้วย MySQL พร้อม Dashboard (Node-RED + Grafana)    มี Flow ตัวอย่าง, โปรแกรม, และไฟล์ฐานข้อมูลให้ดาวน์โหลดครบ"
tags: ""
---
```

## คอร์ส IoT Node-RED + MQTT + SQL สำหรับงานโรงงานอุตสาหกรรม

คอร์สนี้ออกแบบเพื่อให้ผู้เรียนสามารถสร้างระบบ IoT แบบใช้งานได้จริงในโรงงาน  
ตั้งแต่การรับข้อมูลจาก **PLC Siemens, PLC Mitsubishi, Sensor, Modbus**  
ไปจนถึงส่งข้อมูลเข้าสู่ **MQTT → Node-RED → MySQL → Grafana Dashboard**  
ครบทุกขั้นตอนแบบ **Industrial Grade** ไม่ใช่แค่ IoT ทั่วไป

---

## คุณจะได้เรียนรู้อะไรในคอร์สนี้

- ติดตั้งและใช้งาน Node-RED แบบมืออาชีพ
- สื่อสารกับ PLC Siemens S7-1200, PLC Mitsubishi QCPU/FX5U
- สร้าง Dashboard แบบ Real-Time บน Web UI
- ใช้งาน MQTT สำหรับงานอุตสาหกรรม (Pub/Sub)
- ทำ Data Logger ลง MySQL + Query ข้อมูลกลับมาแสดงผล
- เชื่อมต่ออุปกรณ์จริงผ่าน RS485 Modbus RTU / TCP
- ทำระบบ IoT บนมือถือผ่าน Remote-RED และ Web UI
- ทำ Dashboard ขั้นสูงผ่าน Grafana เหมือนโรงงานสมัยใหม่

---

## PART 1 — NODE-RED BASIC (พื้นฐาน Node-RED)

- ติดตั้ง Node-RED (Windows / Raspberry Pi)
- เริ่มต้นเขียน Flow และใช้งาน Inject / Function / Change
- การใช้ Node-RED Function (Get/Set/Compare)
- พื้นฐาน JSON, Object, Array สำหรับ IoT

### Node-RED Dashboard (UI)

- ตั้งค่า Dashboard / Group / Tab
- การออกแบบ Layout ให้ใช้งานง่าย
- ปรับแต่งสี ฟอนต์ Theme
- ใช้งาน Button, Switch, Dropdown, Input, Date
- Gauge, Donut, Compass, Level, Chart ทุกประเภท
- ใส่ภาพเครื่องจักร, Status LED, Alarm Indicator

---

## PART 2 — MQTT SYSTEM (เชื่อมต่อ IoT แบบ Real-Time)

- ติดตั้ง MQTT Broker (Mosquitto)
- ทดสอบด้วย MQTT Explorer
- สร้าง Topic และระบบ Pub/Sub
- เชื่อม MQTT ↔ Node-RED
- Workshop: ส่งข้อมูลจาก Sensor/PLC เข้า MQTT

---

## PART 3 — DATABASE SYSTEM (MySQL + Node-RED)

**เน้นใช้งานจริง ไม่ใช่แค่สาธิต**

- ติดตั้ง MySQL Server
- พื้นฐาน Query: SELECT / INSERT / UPDATE / DELETE
- ออกแบบฐานข้อมูลสำหรับ IoT
- Node-RED → MySQL (บันทึกข้อมูลจริง)
- Dashboard อ่านค่าจาก MySQL
- Workshop: สร้าง Data Logger สำหรับ Temp/Speed

---

## PART 4 — CONNECT TO PLC (เชื่อม PLC ทั้ง Siemens และ Mitsubishi)

### PLC SIEMENS S7-1200

- ตั้งค่า Node-RED ↔ S7-1200
- อ่านค่า / ส่งค่าเข้า PLC
- Analog In/Out + Dashboard
- บันทึกลง MySQL แบบ Real-Time

### PLC MITSUBISHI QCPU / FX5U

- การสื่อสาร Modbus TCP
- รับค่า–ส่งค่า (Register/Coil)
- ประยุกต์แสดงผลบน Dashboard

---

## PART 5 — MODBUS TCP/RTU (เชื่อมอุปกรณ์จริงในโรงงาน)

- พื้นฐาน Modbus RTU/TCP
- Node-RED Modbus Node
- เชื่อมต่อ Temp Controller Omron E5CC (RS485)
- เชื่อม Power Meter, VFD, Sensor

---

## PART 6 — DASHBOARD ADVANCED (Grafana)

- ติดตั้ง Grafana Enterprise
- เชื่อมต่อ MySQL เข้ากับ Grafana
- สร้าง Table, Gauge, Number Value, Trend
- ทำสีตาราง (Color Mapping)
- ตั้งค่า Auto Refresh
- สร้าง Dashboard สำหรับแสดงผลเครื่องจักร

---

## PART 7 — MOBILE ACCESS (ใช้งานบนมือถือ)

- Dashboard ผ่าน Wi-Fi เดียวกัน
- ใช้งานผ่าน Remote-RED App

---

## ผลลัพธ์หลังเรียนจบ

- สร้างระบบ IoT แบบครบวงจรด้วยตัวเองได้ทันที
- เชื่อม PLC Siemens/Mitsubishi กับ MQTT และ Database ได้จริง
- มี Dashboard พร้อมใช้งานแบบ Real-Time
- สร้าง Data Logger ที่ใช้ได้จริงในโรงงาน
- พร้อมไฟล์ Flow, ฐานข้อมูล, และโปรเจกต์ให้ดาวน์โหลด

---

**คอร์สนี้เหมาะสำหรับ**  
ผู้ที่ต้องการยกระดับทักษะ IoT สำหรับงานอุตสาหกรรม, ช่างเทคนิค, วิศวกร, หรือผู้ที่อยากทำ Dashboard/Automation แบบ Professional
