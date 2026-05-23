---
type: entity
category: platform
tags: [node-red, low-code, flow-programming, mqtt, dashboard, node-js, iot-platform]
sources: [iot-nodered-mqtt-sql-course, nodered-dashboard-ui]
created: 2026-04-18
updated: 2026-04-18
---

# Node-RED

**ผู้พัฒนา**: IBM (open source), ดูแลโดย OpenJS Foundation
**License**: Apache 2.0
**Runtime**: Node.js
**บทบาทในโปรเจ็ค**: ตัวเลือก middleware แทน/เสริม Telegraf — รับ MQTT → บันทึก DB → แสดง Dashboard

## ภาพรวม

Node-RED เป็น flow-based programming tool แบบ low-code สำหรับ IoT และ Automation เขียน Logic ด้วยการ "ลาก-วาง Node" และเชื่อมต่อกัน ทำงานบน Node.js รองรับตั้งแต่ Raspberry Pi จนถึง industrial server

## คุณสมบัติหลัก

- **Flow-based**: ลาก Node มาเชื่อมกัน แทนการเขียนโค้ด
- **MQTT native**: มี MQTT in/out node ในตัว ไม่ต้องติดตั้งเพิ่ม
- **Dashboard UI**: ติดตั้ง `node-red-dashboard` ได้ Gauge, Chart, Button, Switch ทันที
- **Database**: มี node สำหรับ MySQL, MongoDB, InfluxDB, SQLite
- **Protocol**: รองรับ Modbus RTU/TCP, OPC UA, HTTP, WebSocket, TCP/UDP
- **Function node**: เขียน JavaScript ใน node ได้ถ้าต้องการ logic ซับซ้อน

## Architecture ในโปรเจ็คปัจจุบัน (ทางเลือก)

Stack ปัจจุบัน (Telegraf):
```
MQTT → Telegraf → InfluxDB → Grafana
```

Stack ทางเลือก (Node-RED):
```
MQTT → Node-RED → MySQL → Grafana
              ↓
         Node-RED Dashboard (web UI + control)
```

Stack รวม (ใช้ทั้งคู่):
```
MQTT → Node-RED → MySQL (Data Logger + Dashboard)
              ↓
           InfluxDB → Grafana (time-series analytics)
```

## การติดตั้ง

```bash
# ติดตั้ง global
npm install -g --unsafe-perm node-red

# รัน
node-red

# เข้า web editor
# http://localhost:1880

# ติดตั้ง Dashboard package
# Manage Palette → Install → node-red-dashboard
```

## Dashboard UI Nodes

| Node | ประเภท | ใช้กับ |
|------|--------|--------|
| ui_gauge | Display | อุณหภูมิ/ความชื้น real-time |
| ui_chart | Display | trend กราฟย้อนหลัง |
| ui_text | Display | ค่า sensor ปัจจุบัน |
| ui_button | Input | trigger / test command |
| ui_switch | Input | เปิด/ปิดอุปกรณ์ |
| ui_slider | Input | ปรับ threshold/setpoint |

Dashboard เข้าถึงที่: `http://localhost:1880/ui`

## ข้อดี / ข้อเสีย

| ข้อดี | ข้อเสีย |
|-------|---------|
| ไม่ต้องเขียนโค้ด (low-code) | Flow ซับซ้อนขึ้นเมื่อ logic เยอะ |
| Dashboard + Broker bridge ในเครื่องเดียว | ไม่ใช่ time-series DB โดยตรง |
| รองรับ Modbus, PLC, OPC UA | Node.js single-threaded — throughput จำกัด |
| Community node มาก (3000+ nodes) | Dashboard ไม่สวยเท่า Grafana |
| ทำงานบน Raspberry Pi ได้ดี | ต้องการ restart เมื่อแก้ flow บางกรณี |

## ความสัมพันธ์

- ใช้ร่วมกับ: [[entities/iot/mosquitto]] — subscribe/publish MQTT
- ใช้ร่วมกับ: [[entities/iot/mysql]] — Data Logger
- ใช้ร่วมกับ: [[entities/iot/influxdb]] — time-series storage
- แข่งขันกับ: Telegraf (สำหรับ MQTT-to-DB bridge)
- เสริมกับ: [[entities/iot/grafana]] — ใช้คู่กัน (Node-RED ส่งข้อมูล, Grafana แสดงกราฟ)
- โปรโตคอล: [[concepts/iot/modbus]]

## แหล่งข้อมูล

- [[sources/iot-nodered-mqtt-sql-course]] — คอร์สครบวงจร MQTT + SQL + Grafana
- [[sources/nodered-dashboard-ui]] — การสร้าง Dashboard UI แบบ low-code
