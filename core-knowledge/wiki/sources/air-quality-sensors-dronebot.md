---
type: source
title: "Measure Air Quality with Microcontrollers — DroneBot Workshop"
slug: air-quality-sensors-dronebot
date_ingested: 2026-04-18
original_file: https://dronebotworkshop.com/air-quality/
tags: [air-quality, pms5003, sgp30, bme280, mq-series, aqi, esp32, sensor-comparison]
---

# Measure Air Quality with Microcontrollers

**ประเภท**: tutorial + sensor comparison  
**แหล่ง**: DroneBot Workshop

## ประเด็นหลัก

1. **ไม่มี sensor ตัวเดียวที่วัดได้ทุกอย่าง** — ต้องใช้หลายตัวร่วมกันเพื่อ AQI ครบ
2. **PMS5003**: laser PM sensor, UART 9600, วัด PM1/2.5/10, 5V, ~100mA
3. **SGP30/SGP40**: I2C, วัด CO2 equivalent + tVOC — ต้องการ 24h warmup ครั้งแรก
4. **BME280/680**: I2C, Temp + Humidity + Pressure (+Gas สำหรับ 680)
5. **MQ series**: Analog 5V, วัด gas เฉพาะตัว (MQ-7=CO, MQ-135=NH3/benzene)

## เปรียบเทียบ Sensor ตามงบประมาณ

| งบ | Sensor stack | วัดได้ |
|----|-------------|--------|
| ต่ำ (~$5) | MQ-135 | CO2 approx, VOC (ไม่แม่นมาก) |
| กลาง (~$35) | PMS5003 + BME280 | PM2.5, Temp, Humidity, Pressure |
| สูง (~$80) | PMS5003 + BME688 + SCD41 | PM2.5/10, Temp, VOC, CO2 จริง |

## ข้อควรระวัง

- **PMS5003**: Adafruit library มี bug หลังหลายชั่วโมง → discrete UART parsing
- **SGP30**: baseline เก็บใน EEPROM เพื่อลด warmup ครั้งถัดไป
- **ESP32 I2C pins**: ใช้ GPIO 21 (SDA) และ GPIO 22 (SCL) ตาม library default

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/pms5003]] — เพิ่ม known library issue
- [[concepts/iot/air-quality-index]] — เพิ่ม sensor comparison table
