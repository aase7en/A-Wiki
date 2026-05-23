---
type: concept
tags: [data-logger, storage, time-series, industrial-iot, database]
sources: [iot-nodered-mqtt-sql-course]
created: 2026-04-18
updated: 2026-04-18
---

# Data Logger

## นิยาม

Data Logger คือระบบที่บันทึกข้อมูลจาก sensor หรืออุปกรณ์ลงใน database อย่างต่อเนื่องตามเวลา เพื่อให้สามารถ query ย้อนหลัง วิเคราะห์ trend และสร้างรายงานได้

## ทำไมถึงสำคัญใน IoT

- **Historical analysis**: ดูแนวโน้มอุณหภูมิ, การใช้พลังงาน, ความผิดปกติ
- **Compliance**: โรงงานอุตสาหกรรมต้องบันทึก log การผลิตตามมาตรฐาน
- **Debugging**: วิเคราะห์ event ย้อนหลังเมื่อระบบมีปัญหา
- **Alerting**: ตรวจจับค่าผิดปกติจาก historical baseline

## วิธีการทำงาน (ในโปรเจ็คนี้)

```
[Sensor] → [MQTT publish] → [Broker]
                                ↓
                          [Node-RED subscribe]
                                ↓
                          [MySQL INSERT]        ← บันทึกทุก reading
                                ↓
                          [Grafana query]       ← แสดง timeline
```

## ตัวอย่างการใช้งาน

**Smart Home Temperature Logger**:
- ESP32 + DHT11 publish temp/humidity ทุก 30 วินาที
- Node-RED subscribe → INSERT ลง MySQL
- Grafana แสดง chart 24 ชั่วโมง + Gauge ปัจจุบัน

**Industrial Power Meter Logger**:
- PZEM-004T วัด current/voltage/power
- ESP32 publish ทุก 1 นาที
- Data Logger บันทึก → คำนวณ energy usage รายวัน/รายเดือน

## ข้อดี / ข้อเสีย

| ข้อดี | ข้อเสีย |
|-------|---------|
| มี historical data สำหรับ analysis | ต้องการ storage เพิ่มขึ้นตามเวลา |
| debugging ง่ายขึ้นมาก | ต้องตั้ง retention policy ไม่งั้น DB โตไม่หยุด |
| สร้าง report และ graph ได้ | latency เพิ่มขึ้น (write → read) |

## เลือก Database ไหน

- **MySQL**: query ยืดหยุ่น, มี JOIN, คุ้นเคย, เหมาะ lab
- **InfluxDB**: compressed time-series, built-in retention, เหมาะ production sensor farm
- **SQLite**: ไม่ต้องการ server, เหมาะ edge device logging

## ความสัมพันธ์

- [[entities/iot/node-red]] — middleware บันทึก data ลง DB
- [[entities/iot/mysql]] — relational data store
- [[entities/iot/influxdb]] — time-series data store
- [[entities/iot/grafana]] — visualization layer

## แหล่งข้อมูล

- [[sources/iot-nodered-mqtt-sql-course]] — Data Logger workshop
