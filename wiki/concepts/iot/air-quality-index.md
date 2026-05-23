---
type: concept
tags: [aqi, air-quality, pm2.5, pm10, iot, environment]
sources: [air-quality-sensors-dronebot, air-quality-iot-lora-network]
created: 2026-04-18
updated: 2026-04-18
---

# Air Quality Index (AQI)

## นิยาม

AQI (Air Quality Index) คือตัวเลขมาตรฐานที่แปลงค่าความเข้มข้นของมลพิษในอากาศ (PM2.5, PM10, CO, O₃ ฯลฯ) ให้เป็นสเกลเดียวที่เข้าใจง่าย แต่ละประเทศมี standard ต่างกันเล็กน้อย

## Sensor ที่ใช้วัด

| Sensor | วัดอะไร | Interface | ราคา |
|--------|--------|---------|------|
| [[entities/iot/pms5003]] | PM1.0, PM2.5, PM10 | UART 9600 | ~$20 |
| SGP30/SGP40 | CO2, VOC (tVOC) | I2C | ~$15 |
| BME688 | Temp, Humidity, Pressure, Gas | I2C | ~$20 |
| SCD41 | CO2, Temp, Humidity | I2C | ~$45 |
| MQ-series | CO, LPG, NH3 ฯลฯ (specific gas) | Analog | ~$2-5 |

## มาตรฐาน PM2.5 ประเทศไทย (กรมควบคุมมลพิษ)

| PM2.5 (µg/m³) | AQI | สี | ความหมาย |
|----------------|-----|-----|---------|
| 0–25 | 0–50 | 🟢 | ดี (Good) |
| 26–37 | 51–100 | 🟡 | ปานกลาง |
| 38–50 | 101–150 | 🟠 | มีผลต่อสุขภาพ |
| 51–90 | 151–200 | 🔴 | มีผลต่อสุขภาพมาก |
| >91 | >200 | 🟣 | อันตราย |

## Architecture IoT สำหรับ AQI Network

```
[ESP32 Node + PMS5003 + BME688]
         ↓ LoRa 915MHz (2km range)
[ESP32 Gateway + Raspberry Pi]
         ↓
[InfluxDB → Grafana Dashboard]
         ↓
[Alert เมื่อ PM2.5 > 50 µg/m³]
```

## ข้อควรระวังในการ Implement

- **PMS5003 UART library**: Adafruit library มี bug ค้างหลังหลายชั่วโมง → ใช้ discrete UART parsing แทน
- **SGP30**: ต้องการ 24-hour warmup ครั้งแรก ใช้ EEPROM เก็บ baseline
- **MQ series**: ใช้ 5V, heating element กินไฟ ~100mA → ไม่เหมาะ battery node
- **Temperature compensation**: ค่า gas sensor บางตัวขึ้นกับอุณหภูมิ ต้องชดเชย

## ความสัมพันธ์

- Sensor หลัก: [[entities/iot/pms5003]]
- LoRa network: [[concepts/iot/lora-p2p]], [[concepts/iot/lorawan]]
- Storage + Visualization: [[entities/iot/influxdb]], [[entities/iot/grafana]]

## แหล่งข้อมูล

- [[sources/air-quality-sensors-dronebot]] — เปรียบเทียบ sensor ทุกประเภทละเอียด
- [[sources/air-quality-iot-lora-network]] — distributed LoRa AQI network
