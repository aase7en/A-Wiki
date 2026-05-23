---
type: entity
category: platform
tags: [mysql, database, sql, relational, data-logger, open-source]
sources: [iot-nodered-mqtt-sql-course]
created: 2026-04-18
updated: 2026-04-18
---

# MySQL

**ผู้พัฒนา**: Oracle (open source community edition)
**License**: GPL v2
**ประเภท**: Relational Database (SQL)
**บทบาทในโปรเจ็ค**: Data Logger สำหรับ sensor data (ทางเลือกแทน InfluxDB)

## ภาพรวม

MySQL เป็น relational database ที่ได้รับความนิยมสูงสุดในโลก ใช้ SQL standard ข้อดีคือ query ยืดหยุ่น มีเอกสารมาก และ Grafana รองรับเป็น data source โดยตรง ต่างจาก InfluxDB ตรงที่ไม่ได้ออกแบบมาสำหรับ time-series โดยเฉพาะ

## การใช้งานใน IoT (Data Logger Pattern)

```sql
-- ตาราง sensor log
CREATE TABLE sensor_data (
  id        INT AUTO_INCREMENT PRIMARY KEY,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  device_id VARCHAR(50),
  topic     VARCHAR(100),
  value     FLOAT,
  unit      VARCHAR(20)
);

-- INSERT จาก Node-RED
INSERT INTO sensor_data (device_id, topic, value, unit)
VALUES ('esp32-s3-gw', 'home/room/temperature', 28.5, 'C');

-- Query ใน Grafana (macro $__timeFilter)
SELECT timestamp, value
FROM sensor_data
WHERE topic = 'home/room/temperature'
  AND $__timeFilter(timestamp)
ORDER BY timestamp ASC;
```

## MySQL vs InfluxDB สำหรับ IoT

| หัวข้อ | MySQL | InfluxDB |
|--------|-------|----------|
| ประเภท DB | Relational (SQL) | Time-series |
| Query | SQL มาตรฐาน | Flux / InfluxQL |
| Compression | ปกติ | สูง (time-series optimize) |
| Retention policy | ต้องจัดการเอง | built-in |
| Grafana datasource | ✅ | ✅ |
| เหมาะกับ | Data Logger ทั่วไป, รายงาน | sensor monitoring, alert |
| Node-RED node | ✅ node-red-node-mysql | ✅ node-red-contrib-influxdb |

## ความสัมพันธ์

- ใช้ร่วมกับ: [[entities/iot/node-red]] — Data Logger via MQTT
- ใช้ร่วมกับ: [[entities/iot/grafana]] — MySQL datasource สำหรับ dashboard
- แข่งขันกับ: [[entities/iot/influxdb]] — สำหรับ IoT data storage

## แหล่งข้อมูล

- [[sources/iot-nodered-mqtt-sql-course]] — Data Logger workshop ด้วย MySQL
